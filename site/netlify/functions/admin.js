// Admin API for /admin – list / invite / set course roles / block / reset password / delete users,
// phone number and access lock date (app_metadata.phone, app_metadata.expires = YYYY-MM-DD, enforced by edge-functions/expiry.js).
// Only callable by an admin (role "admin" or an e-mail listed in ADMIN_EMAILS).
const { COURSE_ROLES, ALL_ROLES, isAdmin } = require('./_common');
// Israeli numbers 05x… → 9725x…; others: digits only, with country code
const normPhone = v => { let d = String(v || '').replace(/[^\d+]/g, '').replace(/^\+/, '').replace(/^00/, ''); if (/^0\d{8,9}$/.test(d)) d = '972' + d.slice(1); return d; };
const okPhone = d => d === '' || /^\d{10,15}$/.test(d);
const okDate = d => d === '' || (/^\d{4}-\d{2}-\d{2}$/.test(d) && !isNaN(Date.parse(d)));
const out = (statusCode, body) => ({ statusCode, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }, body: JSON.stringify(body) });

exports.handler = async (event, context) => {
  const cc = context.clientContext || {};
  const identity = cc.identity, me = cc.user;
  if (!identity || !identity.url) return out(500, { error: 'Netlify Identity לא מופעל באתר' });
  if (!me) return out(401, { error: 'יש להתחבר' });
  if (!isAdmin(me)) return out(403, { error: 'אין הרשאת ניהול' });
  const api = async (path, method = 'GET', body) => {
    const r = await fetch(identity.url + path, { method, headers: { Authorization: 'Bearer ' + identity.token, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
    const t = await r.text(); let d = null; try { d = t ? JSON.parse(t) : null; } catch (e) { d = { raw: t }; }
    if (!r.ok) { const e = new Error((d && (d.msg || d.error_description || d.error)) || ('HTTP ' + r.status)); e.status = r.status; throw e; }
    return d;
  };
  const shape = u => ({
    id: u.id, email: u.email, name: (u.user_metadata && (u.user_metadata.full_name || u.user_metadata.name)) || '',
    roles: ((u.app_metadata && u.app_metadata.roles) || []).filter(r => ALL_ROLES.includes(r)),
    blocked: !!(u.app_metadata && u.app_metadata.blocked),
    provider: (u.app_metadata && u.app_metadata.provider) || 'email',
    phone: (u.app_metadata && u.app_metadata.phone) || '', expires: (u.app_metadata && u.app_metadata.expires) || '',
    confirmed: !!u.confirmed_at, invited_at: u.invited_at || null, created_at: u.created_at, last_login: u.last_sign_in_at || null,
    owner: isAdmin({ email: u.email, app_metadata: {} })
  });
  const getUser = id => api('/admin/users/' + encodeURIComponent(id));
  const setMeta = async (id, patch) => { const u = await getUser(id); const am = { ...(u.app_metadata || {}), ...patch }; return shape(await api('/admin/users/' + encodeURIComponent(id), 'PUT', { app_metadata: am })); };
  const cleanRoles = rs => Array.from(new Set((rs || []).filter(r => ALL_ROLES.includes(r))));

  try {
    if (event.httpMethod === 'GET') {
      let all = [], page = 1;
      while (page < 20) {
        const d = await api(`/admin/users?page=${page}&per_page=100`);
        const us = (d && d.users) || [];
        all = all.concat(us); if (us.length < 100) break; page++;
      }
      return out(200, { users: all.map(shape), courses: COURSE_ROLES, me: me.email });
    }
    if (event.httpMethod !== 'POST') return out(405, { error: 'method' });
    const b = JSON.parse(event.body || '{}');
    switch (b.action) {
      case 'invite': {
        const email = String(b.email || '').trim().toLowerCase();
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return out(400, { error: 'כתובת מייל לא תקינה' });
        const phone = normPhone(b.phone), expires = String(b.expires || '');
        if (!okPhone(phone)) return out(400, { error: 'מספר טלפון לא תקין' });
        if (!okDate(expires)) return out(400, { error: 'תאריך לא תקין' });
        const u = await api('/invite', 'POST', { email, data: { full_name: String(b.name || '').trim() } });
        const roles = cleanRoles(b.roles).filter(r => r !== 'admin');
        const patch = {}; if (roles.length) patch.roles = roles; if (phone) patch.phone = phone; if (expires) patch.expires = expires;
        const done = Object.keys(patch).length ? await setMeta(u.id, patch) : shape(u);
        return out(200, { user: done });
      }
      case 'roles': {
        const u = await getUser(b.id);
        let roles = cleanRoles(b.roles);
        if (u.email === me.email && !roles.includes('admin')) roles.push('admin'); // never lock yourself out
        return out(200, { user: await setMeta(b.id, { roles }) });
      }
      case 'details': {
        const phone = normPhone(b.phone), expires = String(b.expires || '');
        if (!okPhone(phone)) return out(400, { error: 'מספר טלפון לא תקין' });
        if (!okDate(expires)) return out(400, { error: 'תאריך לא תקין' });
        const u = await getUser(b.id);
        if (u.email === me.email && expires) return out(400, { error: 'אי אפשר להגדיר תאריך נעילה לעצמך' });
        const body = { app_metadata: { ...(u.app_metadata || {}), phone, expires } };
        if (typeof b.name === 'string') body.user_metadata = { ...(u.user_metadata || {}), full_name: b.name.trim() };
        return out(200, { user: shape(await api('/admin/users/' + encodeURIComponent(b.id), 'PUT', body)) });
      }
      case 'block': {
        const u = await getUser(b.id);
        if (u.email === me.email) return out(400, { error: 'אי אפשר לחסום את עצמך' });
        const am = u.app_metadata || {};
        const patch = b.blocked ? { blocked: true, roles: [], prev_roles: (am.roles || []).filter(r => r !== 'admin') }
                                : { blocked: false, roles: cleanRoles(am.prev_roles || []), prev_roles: [] };
        return out(200, { user: await setMeta(b.id, patch) });
      }
      case 'resend': {
        const u = await getUser(b.id);
        if (u.confirmed_at) return out(400, { error: 'המשתמש כבר השלים הרשמה – שלחו קישור לאיפוס סיסמה במקום' });
        await api('/invite', 'POST', { email: u.email, data: u.user_metadata || {} });
        return out(200, { ok: true });
      }
      case 'recover': {
        const u = await getUser(b.id);
        const r = await fetch(identity.url + '/recover', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: u.email }) });
        if (!r.ok) return out(r.status, { error: 'שליחת הקישור נכשלה (' + r.status + ')' });
        return out(200, { ok: true });
      }
      case 'delete': {
        const u = await getUser(b.id);
        if (u.email === me.email) return out(400, { error: 'אי אפשר למחוק את עצמך' });
        await api('/admin/users/' + encodeURIComponent(b.id), 'DELETE');
        return out(200, { ok: true });
      }
      default: return out(400, { error: 'פעולה לא מוכרת' });
    }
  } catch (e) {
    let msg = e.message;
    if (/already been registered|already registered|exists/i.test(msg)) msg = 'המייל הזה כבר רשום';
    return out(e.status && e.status < 500 ? e.status : 500, { error: msg });
  }
};
