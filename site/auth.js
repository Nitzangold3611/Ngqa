/* NGQA auth – thin client for Netlify Identity (GoTrue) in Hebrew.
   Used by the home page, every course page and /admin.
   Fail-open while Identity is not enabled on the site (settings endpoint 404). */
(function () {
  const API = '/.netlify/identity';
  const KEY = 'ngqa.auth';
  const COURSES = [
    { id: 'ctfl', name: 'ISTQB CTFL 4.0', path: '/courses/ctfl/' },
    { id: 'genai', name: 'CT-GenAI', path: '/courses/genai/' },
    { id: 'sql', name: 'SQL', path: '/courses/sql/' },
    { id: 'ste', name: 'CT-STE', path: '/courses/ste/' },
    { id: 'ai', name: 'CT-AI', path: '/courses/ai/' },
    { id: 'mat', name: 'CT-MAT', path: '/courses/mat/' },
    { id: 'jobs', name: 'סדנת מחפשי עבודה', path: '/courses/jobs/' }
  ];
  let enabled = null; // null = unknown, true/false after probe

  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; } };
  const save = s => { try { s ? localStorage.setItem(KEY, JSON.stringify(s)) : localStorage.removeItem(KEY); } catch (e) {} setCookie(s); };
  function setCookie(s) {
    // the server-side lock (v3.2) reads this cookie
    const sec = location.protocol === 'https:' ? '; Secure' : '';
    if (s && s.access_token) document.cookie = `nf_jwt=${s.access_token}; Path=/; Max-Age=${60 * 60 * 24 * 30}; SameSite=Lax${sec}`;
    else document.cookie = `nf_jwt=; Path=/; Max-Age=0; SameSite=Lax${sec}`;
  }
  function decode(t) {
    try { return JSON.parse(decodeURIComponent(escape(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))))); } catch (e) { return null; }
  }
  async function req(path, opt = {}) {
    const r = await fetch(API + path, opt);
    let d = null; try { d = await r.json(); } catch (e) {}
    if (!r.ok) { const err = new Error((d && (d.error_description || d.msg || d.error)) || ('HTTP ' + r.status)); err.status = r.status; err.data = d; throw err; }
    return d;
  }
  const form = o => ({ method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams(o).toString() });
  const json = (m, o, tok) => ({ method: m, headers: Object.assign({ 'Content-Type': 'application/json' }, tok ? { Authorization: 'Bearer ' + tok } : {}), body: JSON.stringify(o) });

  async function isEnabled() {
    if (enabled !== null) return enabled;
    try { const r = await fetch(API + '/settings'); enabled = r.ok; } catch (e) { enabled = false; }
    return enabled;
  }
  async function storeTokens(t) {
    const s = { access_token: t.access_token, refresh_token: t.refresh_token, expires_at: Date.now() + (t.expires_in || 3600) * 1000 };
    try { s.user = await req('/user', { headers: { Authorization: 'Bearer ' + s.access_token } }); } catch (e) {}
    save(s); return s;
  }
  async function session() {
    let s = load(); if (!s) return null;
    if (Date.now() > s.expires_at - 60000) {
      try { s = await storeTokens(await req('/token', form({ grant_type: 'refresh_token', refresh_token: s.refresh_token }))); }
      catch (e) { if (e.status === 400 || e.status === 401) { save(null); return null; } return s; }
    } else setCookie(s);
    return s;
  }
  /* roles live in the token, which is renewed only once an hour. Ask the server for the current
     user on every page load; when the admin changed the roles, get a new token right away. */
  let freshDone = false;
  async function fresh() {
    let s = await session(); if (!s || freshDone) return s;
    freshDone = true;
    try {
      const u = await req('/user', { headers: { Authorization: 'Bearer ' + s.access_token } });
      const tok = decode(s.access_token) || {};
      const same = JSON.stringify((tok.app_metadata || {}).roles || []) === JSON.stringify((u.app_metadata || {}).roles || [])
                && !!(tok.app_metadata || {}).blocked === !!(u.app_metadata || {}).blocked;
      if (!same) s = await storeTokens(await req('/token', form({ grant_type: 'refresh_token', refresh_token: s.refresh_token })));
      else { s.user = u; save(s); }
    } catch (e) { if (e.status === 401) { save(null); return null; } }
    return s;
  }
  function info(s) {
    if (!s) return null;
    const c = decode(s.access_token) || {}; const u = s.user || {};
    const am = u.app_metadata || c.app_metadata || {}; const um = u.user_metadata || c.user_metadata || {};
    const roles = am.roles || [];
    return { email: c.email || u.email, name: um.full_name || um.name || '', roles, admin: roles.includes('admin'), blocked: !!am.blocked };
  }
  const can = (i, course) => !!i && !i.blocked && (i.admin || i.roles.includes(course));

  const Auth = {
    COURSES, isEnabled, session, fresh, info, can,
    async login(email, password) { return storeTokens(await req('/token', form({ grant_type: 'password', username: email, password }))); },
    google() { location.href = API + '/authorize?provider=google'; },
    async recover(email) { await req('/recover', json('POST', { email })); },
    async acceptInvite(token, password, name) {
      const t = await req('/verify', json('POST', { token, password, type: 'signup' }));
      const s = await storeTokens(t);
      if (name) { try { s.user = await req('/user', json('PUT', { data: { full_name: name } }, s.access_token)); save(s); } catch (e) {} }
      return s;
    },
    async verifyRecovery(token) { return storeTokens(await req('/verify', json('POST', { token, type: 'recovery' }))); },
    async setPassword(password) { const s = await session(); s.user = await req('/user', json('PUT', { password }, s.access_token)); save(s); return s; },
    async confirm(token) { return storeTokens(await req('/verify', json('POST', { token, type: 'signup' }))); },
    async refreshUser() { const s = await session(); if (!s) return null; return storeTokens({ access_token: s.access_token, refresh_token: s.refresh_token, expires_in: Math.max(60, (s.expires_at - Date.now()) / 1000) }); },
    logout() { const s = load(); if (s) fetch(API + '/logout', { method: 'POST', headers: { Authorization: 'Bearer ' + s.access_token } }).catch(() => {}); save(null); },
    /* reads #access_token=… (Google), #invite_token=…, #recovery_token=…, #confirmation_token=… */
    async handleHash() {
      const h = new URLSearchParams(location.hash.slice(1));
      const clear = () => history.replaceState(null, '', location.pathname + location.search);
      if (h.get('access_token')) { clear(); await storeTokens({ access_token: h.get('access_token'), refresh_token: h.get('refresh_token'), expires_in: +h.get('expires_in') || 3600 }); return { type: 'external' }; }
      if (h.get('error_description') || h.get('error')) { clear(); return { type: 'error', message: h.get('error_description') || h.get('error') }; }
      for (const t of ['invite', 'recovery', 'confirmation']) { const v = h.get(t + '_token'); if (v) { clear(); return { type: t, token: v }; } }
      return null;
    },
    /* course pages: send people without access back to the home page (does nothing while Identity is off) */
    async guard(course) {
      if (!(await isEnabled())) return true;
      const i = info(await fresh());
      if (can(i, course)) return true;
      location.replace('/?' + (i ? 'denied=' + course : 'login=1&next=' + encodeURIComponent(location.pathname + location.hash)));
      return false;
    },
    inApp: () => /FBAN|FBAV|Instagram|WhatsApp|Line\/|; wv\)|TikTok|Snapchat|LinkedInApp/i.test(navigator.userAgent),
    he(msg) {
      const m = String(msg || '');
      if (/invalid_grant|No user found|Invalid Password|invalid.*credentials/i.test(m)) return 'המייל או הסיסמה שגויים.';
      if (/Email not confirmed/i.test(m)) return 'החשבון עדיין לא אושר. פתחו את הקישור שנשלח במייל.';
      if (/User not found/i.test(m)) return 'לא נמצא משתמש עם המייל הזה.';
      if (/expired|invalid.*token|Invalid token|not found/i.test(m)) return 'הקישור כבר לא בתוקף. בקשו קישור חדש.';
      if (/password.*(short|least|characters)/i.test(m)) return 'הסיסמה קצרה מדי (לפחות 8 תווים).';
      if (/Signups not allowed|registration/i.test(m)) return 'הכניסה בהזמנה בלבד. לקבלת הזמנה פנו לניצן: 052-6718757 או nitzan@ngqa.info';
      if (/rate|too many/i.test(m)) return 'יותר מדי ניסיונות. נסו שוב בעוד כמה דקות.';
      return 'משהו השתבש: ' + m;
    }
  };
  window.NGQAAuth = Auth;
  if (location.pathname.startsWith('/courses/')) { const w = document.createElement('script'); w.src = '/wm.js'; w.defer = true; document.head.appendChild(w); }
})();
