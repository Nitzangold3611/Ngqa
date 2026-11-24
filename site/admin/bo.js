/* NGQA backoffice (v3.13): side menu + dashboard, courses (settings and "מידע על הקורס" texts) and the
   recorded-lessons tree. The users screen lives in index.html. API: /.netlify/functions/bo (admin only). */
(() => {
  const A = window.NGQAAuth, $ = id => document.getElementById(id);
  const NAMES = { ctfl: 'CTFL 4.0', genai: 'CT-GenAI', sql: 'SQL', ste: 'CT-STE', ai: 'CT-AI', mat: 'CT-MAT', jobs: 'מחפשי עבודה' };
  const CS = Object.keys(NAMES);
  const esc = t => String(t ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const toast = (t, bad) => window.boToast ? window.boToast(t, bad) : alert(t);
  const IC = {
    dash: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    courses: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5"/><path d="M8 7h7M8 11h7"/>',
    lessons: '<rect x="3" y="5" width="14" height="14" rx="2"/><path d="M17 10l4-2v8l-4-2z"/>',
    progress: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    log: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'
  };
  const NAV = [['dash', 'לוח בקרה'], ['users', 'משתמשים'], ['courses', 'קורסים'], ['lessons', 'שיעורים מוקלטים'], ['progress', 'התקדמות צפייה', '2ג'], ['log', 'יומן פעולות', '2ד']];

  async function bo(method, q, body) {
    const s = await A.session(); if (!s) throw new Error('יש להתחבר מחדש');
    const r = await fetch('/.netlify/functions/bo' + (q || ''), { method, headers: { Authorization: 'Bearer ' + s.access_token, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
    let d = {}; try { d = await r.json(); } catch (e) {}
    if (!r.ok) throw new Error(d.error || ('שגיאה ' + r.status)); return d;
  }
  let cfg = null, summary = null;
  const decksCache = {}, infoCache = {}, cat = {};
  const getDecks = c => decksCache[c] || (decksCache[c] = fetch(`/courses/${c}/decks.json`).then(r => r.json()).catch(() => []));

  /* ------------------------------------------------------------ routing */
  function route() {
    const [v, arg] = (location.hash.slice(1) || 'dash').split('/');
    const view = NAV.some(n => n[0] === v) ? v : 'dash';
    document.querySelectorAll('.view').forEach(x => { x.hidden = x.dataset.v !== view; });
    document.querySelectorAll('#side a').forEach(a => a.classList.toggle('on', a.dataset.v === view));
    document.title = (NAV.find(n => n[0] === view) || [, ''])[1] + ' · מערכת ניהול NGQA';
    ({ dash, courses, lessons, progress, log }[view] || (() => {}))(arg);
  }

  /* ------------------------------------------------------------ dashboard */
  async function dash() {
    const v = $('v-dash'), us = (window.boUsers ? window.boUsers() : []).filter(u => !u.roles.includes('admin'));
    const t = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jerusalem' }).format(new Date());
    const days = d => Math.round((Date.parse(d) - Date.parse(t)) / 864e5);
    const soon = us.filter(u => !u.blocked && CS.some(c => u.roles.includes(c) && u.access && u.access[c] && u.access[c].m && days(u.access[c].m) >= 0 && days(u.access[c].m) <= 14)).length;
    const tiles = [['תלמידים', us.length, ''], ['פעילים', us.filter(u => u.confirmed && !u.blocked).length, 'ok'], ['ממתינים להרשמה', us.filter(u => !u.confirmed && !u.blocked).length, ''], ['הגישה מסתיימת ב-14 יום', soon, soon ? 'warn' : ''], ['חסומים', us.filter(u => u.blocked).length, '']];
    const row = c => { const n = us.filter(u => u.roles.includes(c)).length, r = us.filter(u => u.roles.includes(c + '-rec')).length, l = summary && summary[c];
      return `<tr><td><b>${NAMES[c]}</b></td><td>${n}</td><td>${cfg && cfg.courses[c].rec ? r : '—'}</td><td>${cfg && cfg.courses[c].rec ? (l ? `${l.pub}${l.draft ? ` <span class="mut">(+${l.draft} טיוטות)</span>` : ''}` : '…') : '<span class="mut">ללא הקלטות</span>'}</td><td class="lnk"><a href="#courses/${c}">הגדרות</a> <a href="#lessons/${c}">שיעורים</a> <a href="/courses/${c}/" target="_blank" rel="noopener">לקורס ↗</a></td></tr>`; };
    v.innerHTML = `<div class="vh"><h2>לוח בקרה</h2></div>
      <section class="tiles">${tiles.map(([a, b, k]) => `<div class="tile ${k}" style="cursor:default"><b>${b}</b><span>${a}</span></div>`).join('')}</section>
      <section class="card"><div class="vh" style="margin-bottom:10px"><h2 style="font-size:19px">קורסים</h2></div>
      <div class="tw"><table class="tb"><thead><tr><th>קורס</th><th>תלמידים</th><th>עם הקלטות</th><th>שיעורים מפורסמים</th><th></th></tr></thead><tbody>${CS.map(row).join('')}</tbody></table></div></section>
      <section class="card qk"><b>פעולות מהירות</b><div><a class="btn pri" href="#users" id="dInv">＋ הזמנת תלמיד</a><a class="btn ghost" href="#lessons">＋ שיעור מוקלט</a><a class="btn ghost" href="#courses">עריכת מידע על קורס</a></div></section>`;
    $('dInv').onclick = () => setTimeout(() => { const b = $('invB'); if (b) b.click(); }, 50);
    if (!summary) { try { summary = (await bo('GET', '?what=summary')).lessons; if (!$('v-dash').hidden) dash(); } catch (e) { summary = {}; } }
  }

  /* ------------------------------------------------------------ courses */
  async function defaultsOf(c) {
    if (infoCache[c]) return infoCache[c];
    const h = await fetch(`/courses/${c}/`).then(r => r.text()).catch(() => '');
    const d = new DOMParser().parseFromString(h, 'text/html'), f = k => d.querySelector(`#cinfo [data-f="${k}"]`);
    const li = k => f(k) ? [...f(k).querySelectorAll('li')].map(x => x.textContent.trim()) : [];
    return (infoCache[c] = { about: f('about') ? f('about').textContent.trim() : '', audience: li('audience'), prereq: f('prereq') ? f('prereq').textContent.trim() : '', goals: li('goals') });
  }
  async function courses(arg) {
    const v = $('v-courses');
    if (!cfg) v.innerHTML = '<p class="msg">טוען…</p>';
    try { if (!cfg) cfg = (await bo('GET', '?what=config')).config; } catch (e) { v.innerHTML = `<div class="card gate"><h2>לא הצלחנו לטעון את הגדרות הקורסים</h2><p>${esc(e.message)}</p></div>`; return; }
    const us = window.boUsers ? window.boUsers() : [];
    v.innerHTML = `<div class="vh"><h2>קורסים</h2></div><p class="mut" style="margin:-8px 0 0">כאן מדליקים שיעורים מוקלטים לקורס, קובעים אם תלמידים יכולים להוריד PDF, ועורכים את הטקסטים בלשונית "מידע על הקורס".</p>
      <div class="cg">${CS.map(c => { const x = cfg.courses[c];
        return `<div class="card cc" data-c="${c}"><div class="cch"><b>${NAMES[c]}</b><span class="mut">${us.filter(u => u.roles.includes(c) && !u.roles.includes('admin')).length} תלמידים</span></div>
        <label class="tg"><span>שיעורים מוקלטים בקורס</span><input type="checkbox" data-k="rec" ${x.rec ? 'checked' : ''}><span class="t"></span></label>
        <label class="tg"><span>תלמידים יכולים להוריד PDF</span><input type="checkbox" data-k="pdf" ${x.pdf ? 'checked' : ''}><span class="t"></span></label>
        <div class="mut sm">${x.info ? 'מידע על הקורס: נערך' + (x.at ? ' · ' + new Date(x.at).toLocaleDateString('he-IL') : '') : 'מידע על הקורס: הטקסט המקורי'}</div>
        <div class="acts2"><button class="btn ghost" type="button" data-ed="${c}">עריכת מידע על הקורס</button>${x.rec ? `<a class="btn ghost" href="#lessons/${c}">שיעורים</a>` : ''}<a class="btn ghost" href="/courses/${c}/#info" target="_blank" rel="noopener">צפייה ↗</a></div></div>`; }).join('')}</div>
      <section class="card" id="ied" hidden></section>`;
    v.querySelectorAll('.cc input[data-k]').forEach(i => i.onchange = async () => {
      const c = i.closest('.cc').dataset.c, k = i.dataset.k;
      if (k === 'rec' && !i.checked && !confirm(`לכבות את השיעורים המוקלטים ב-${NAMES[c]}? התלמידים לא יראו את השיעורים (השיעורים עצמם והרשאות התלמידים נשמרים).`)) { i.checked = true; return; }
      i.disabled = true;
      try { const d = await bo('POST', '', { action: 'course', c, [k]: i.checked }); cfg = d.config; if (k === 'rec' && window.boSetRec) window.boSetRec(d.rec);
        toast(k === 'rec' ? (i.checked ? 'השיעורים המוקלטים הופעלו בקורס' : 'השיעורים המוקלטים כובו בקורס') : (i.checked ? 'הורדת PDF פתוחה לתלמידים' : 'הורדת PDF מוסתרת מתלמידים'));
        courses(); } catch (e) { i.checked = !i.checked; toast(e.message, 1); } finally { i.disabled = false; }
    });
    v.querySelectorAll('[data-ed]').forEach(b => b.onclick = () => { location.hash = 'courses/' + b.dataset.ed; });
    if (CS.includes(arg)) editInfo(arg);
  }
  async function editInfo(c) {
    const box = $('ied'), x = cfg.courses[c], def = await defaultsOf(c), cur = x.info || def;
    box.hidden = false;
    box.innerHTML = `<div class="vh"><h2 style="font-size:19px">מידע על הקורס · ${NAMES[c]}</h2><a class="btn ghost" href="#courses">סגירה</a></div>
      <form id="iedF" class="ef"><label>על הקורס<textarea name="about" rows="4">${esc(cur.about)}</textarea></label>
      <div class="f2"><label>למי הקורס מתאים <span class="hint">שורה לכל פריט</span><textarea name="audience" rows="5">${esc((cur.audience || []).join('\n'))}</textarea></label>
      <label>מה לומדים <span class="hint">שורה לכל פריט</span><textarea name="goals" rows="5">${esc((cur.goals || []).join('\n'))}</textarea></label></div>
      <label>דרישות קדם<input name="prereq" value="${esc(cur.prereq)}"></label>
      <p class="hint">מבנה הקורס, מה כלול באתר ופרטי הבחינה מחושבים אוטומטית ולא נערכים כאן.</p>
      <div class="acts2"><button class="btn pri" type="submit">שמירה</button>${x.info ? '<button class="btn ghost" type="button" id="iedR">חזרה לטקסט המקורי</button>' : ''}</div></form>`;
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const lines = t => t.split('\n').map(s => s.trim()).filter(Boolean);
    const save = async info => { try { cfg = (await bo('POST', '', { action: 'course', c, info })).config; try { sessionStorage.removeItem('ngqa.cfg'); } catch (e) {} toast(info ? 'המידע נשמר. התלמידים יראו אותו תוך דקה.' : 'חזרנו לטקסט המקורי'); location.hash = 'courses'; } catch (e) { toast(e.message, 1); } };
    $('iedF').onsubmit = e => { e.preventDefault(); const f = e.target;
      const info = { about: f.about.value.trim(), audience: lines(f.audience.value), prereq: f.prereq.value.trim(), goals: lines(f.goals.value) };
      const same = JSON.stringify(info) === JSON.stringify(def);
      save(same ? null : info); };
    if ($('iedR')) $('iedR').onclick = () => { if (confirm('למחוק את העריכה ולחזור לטקסט המקורי?')) save(null); };
  }

  /* ------------------------------------------------------------ lessons tree */
  let lc = '';
  async function lessons(arg) {
    const v = $('v-lessons');
    try { if (!cfg) cfg = (await bo('GET', '?what=config')).config; } catch (e) { v.innerHTML = `<div class="card gate"><h2>שגיאה</h2><p>${esc(e.message)}</p></div>`; return; }
    const recCs = CS.filter(c => cfg.courses[c].rec);
    lc = CS.includes(arg) ? arg : (lc || recCs[0] || 'genai');
    v.innerHTML = `<div class="vh"><h2>שיעורים מוקלטים</h2><a class="btn ghost" href="/courses/${lc}/lessons/" target="_blank" rel="noopener">תצוגת תלמיד ↗</a></div>
      <div class="ctab">${CS.map(c => `<a href="#lessons/${c}" class="${c === lc ? 'on' : ''} ${cfg.courses[c].rec ? '' : 'off'}">${NAMES[c]}</a>`).join('')}</div>
      ${cfg.courses[lc].rec ? '' : `<div class="note">השיעורים המוקלטים כבויים בקורס הזה, אז התלמידים לא רואים אותם. אפשר לבנות את העץ מראש ולהדליק במסך <a href="#courses">קורסים</a>.</div>`}
      <div id="tree"><p class="msg">טוען…</p></div>`;
    try {
      const [decks, d] = await Promise.all([getDecks(lc), cat[lc] ? Promise.resolve({ catalog: cat[lc] }) : bo('GET', '?what=catalog&c=' + lc)]);
      cat[lc] = d.catalog || { ch: {} }; tree(decks);
    } catch (e) { $('tree').innerHTML = `<div class="card gate"><h2>לא הצלחנו לטעון את השיעורים</h2><p>${esc(e.message)}</p></div>`; }
  }
  const KIND = { none: 'בלי סרטון עדיין', url: 'קישור לסרטון', bunny: 'Bunny Stream' };
  function tree(decks) {
    const ch = cat[lc].ch = cat[lc].ch || {}, c = lc;
    const ids = decks.map(x => x.id).concat(Object.keys(ch).filter(k => !decks.some(x => x.id === k)));
    const lab = k => { const d = decks.find(x => x.id === k); return d ? `${d.lab || 'פרק ' + d.num} · ${d.title}` : k; };
    $('tree').innerHTML = ids.map(k => { const ls = ch[k] || [];
      return `<section class="card tc" data-ch="${k}"><div class="tch2"><b>${esc(lab(k))}</b><span class="mut">${ls.length ? ls.length + ' שיעורים' : 'אין שיעורים'}</span><button class="btn ghost sm" type="button" data-add="${k}">＋ שיעור</button></div>
        <ol class="ll" data-ch="${k}">${ls.map((l, i) => `<li class="lr" draggable="true" data-ch="${k}" data-i="${i}"><span class="gr" title="גרירה לשינוי הסדר" aria-hidden="true">⋮⋮</span><span class="no">${i + 1}</span>
          <span class="lt"><b>${esc(l.title)}</b><small>${[l.dur, KIND[l.kind] + (l.kind !== 'none' && !l.src ? ' (חסר)' : ''), l.sf ? 'שקפים ' + l.sf + (l.st > l.sf ? '–' + l.st : '') : '', l.ex ? 'תרגיל' : '', (l.files || []).length ? (l.files.length + ' קבצים') : ''].filter(Boolean).map(esc).join(' · ')}</small></span>
          <span class="st ${l.status === 'pub' ? 'pub' : ''}">${l.status === 'pub' ? 'פורסם' : 'טיוטה'}</span>
          <span class="ra"><button type="button" data-up title="למעלה" aria-label="להזיז למעלה">▲</button><button type="button" data-dn title="למטה" aria-label="להזיז למטה">▼</button><button type="button" data-ed>עריכה</button><button type="button" data-del class="del">מחיקה</button></span></li>`).join('')}</ol></section>`; }).join('');
    const T = $('tree');
    T.querySelectorAll('[data-add]').forEach(b => b.onclick = () => openLesson(b.dataset.add, -1, decks));
    T.querySelectorAll('.lr').forEach(li => {
      const k = li.dataset.ch, i = +li.dataset.i;
      li.querySelector('[data-ed]').onclick = () => openLesson(k, i, decks);
      li.querySelector('[data-del]').onclick = () => { if (!confirm(`למחוק את השיעור "${ch[k][i].title}"?`)) return; ch[k].splice(i, 1); persist(decks, 'השיעור נמחק'); };
      li.querySelector('[data-up]').onclick = () => move(k, i, k, i - 1, decks);
      li.querySelector('[data-dn]').onclick = () => move(k, i, k, i + 1, decks);
      li.ondragstart = e => { e.dataTransfer.setData('text/plain', k + ':' + i); li.classList.add('drag'); };
      li.ondragend = () => li.classList.remove('drag');
    });
    T.querySelectorAll('.ll').forEach(ol => {
      ol.ondragover = e => { e.preventDefault(); ol.classList.add('over'); };
      ol.ondragleave = () => ol.classList.remove('over');
      ol.ondrop = e => { e.preventDefault(); ol.classList.remove('over');
        const [fk, fi] = e.dataTransfer.getData('text/plain').split(':'); const tgt = e.target.closest('.lr');
        const tk = ol.dataset.ch; let ti = tgt ? +tgt.dataset.i : (ch[tk] || []).length;
        if (tgt) { const r = tgt.getBoundingClientRect(); if (e.clientY > r.top + r.height / 2) ti++; }
        move(fk, +fi, tk, ti, decks, true); };
    });
  }
  function move(fk, fi, tk, ti, decks, drop) {
    const ch = cat[lc].ch, src = ch[fk]; if (!src || !src[fi]) return;
    if (!drop && (ti < 0 || ti >= src.length)) return;
    const [l] = src.splice(fi, 1); ch[tk] = ch[tk] || [];
    if (drop && fk === tk && ti > fi) ti--;
    ch[tk].splice(Math.max(0, Math.min(ti, ch[tk].length)), 0, l);
    if (!src.length) delete ch[fk];
    persist(decks, 'הסדר עודכן');
  }
  async function persist(decks, msg) {
    tree(decks);
    try { const d = await bo('POST', '', { action: 'catalog', c: lc, ch: cat[lc].ch }); cat[lc] = d.catalog; summary = null; tree(decks); toast(msg || 'נשמר'); }
    catch (e) { toast('השמירה נכשלה: ' + e.message, 1); delete cat[lc]; lessons(lc); }
  }
  function openLesson(k, i, decks) {
    const ch = cat[lc].ch, l = i >= 0 ? ch[k][i] : { title: '', desc: '', kind: 'none', src: '', dur: '', sf: 0, st: 0, ex: false, files: [], status: 'draft' };
    let dl = $('ldlg'); if (!dl) { dl = document.createElement('dialog'); dl.id = 'ldlg'; document.body.appendChild(dl); }
    const opts = decks.map(d => `<option value="${d.id}" ${d.id === k ? 'selected' : ''}>${esc((d.lab || 'פרק ' + d.num) + ' · ' + d.title)}</option>`).join('');
    const hasEx = d => d && (d.ex || []).length;
    dl.innerHTML = `<h3>${i >= 0 ? 'עריכת שיעור' : 'שיעור חדש'}</h3><p>${NAMES[lc]}</p>
      <form method="dialog" id="lF"><label>כותרת<input name="title" required maxlength="120" value="${esc(l.title)}" placeholder="2.1 מבנה של פרומפט"></label>
      <label>פרק<select name="ch">${opts}</select></label>
      <label>תיאור קצר <span class="hint">לא חובה</span><textarea name="desc" rows="3" maxlength="600">${esc(l.desc)}</textarea></label>
      <div class="sect"><b>סרטון</b><div class="f2"><label>מקור<select name="kind">${Object.entries(KIND).map(([a, b]) => `<option value="${a}" ${l.kind === a ? 'selected' : ''}>${b}</option>`).join('')}</select></label>
      <label>משך <span class="hint">דקות:שניות</span><input name="dur" value="${esc(l.dur)}" placeholder="14:20" pattern="\\d{1,3}:\\d{2}" dir="ltr"></label></div>
      <label id="srcL">קישור / מזהה<input name="src" value="${esc(l.src)}" dir="ltr"></label><span class="hint" id="srcH"></span></div>
      <div class="sect"><b>קישורים לחומר</b><div class="f2"><label>משקף<input name="sf" type="number" min="0" max="999" value="${l.sf || ''}"></label><label>עד שקף<input name="st" type="number" min="0" max="999" value="${l.st || ''}"></label></div>
      <label class="opt"><input type="checkbox" name="ex" ${l.ex ? 'checked' : ''}> קישור לתרגילים של הפרק</label>
      <label>קבצים מצורפים <span class="hint">שורה לכל קובץ: שם | קישור https</span><textarea name="files" rows="2" dir="auto">${esc((l.files || []).map(f => f.n + ' | ' + f.u).join('\n'))}</textarea></label></div>
      <div class="sect"><b>סטטוס</b><label class="opt"><input type="radio" name="status" value="draft" ${l.status !== 'pub' ? 'checked' : ''}> טיוטה — רק מנהל רואה</label><label class="opt"><input type="radio" name="status" value="pub" ${l.status === 'pub' ? 'checked' : ''}> פורסם — התלמידים עם גישה להקלטות רואים</label></div>
      <div class="acts"><button class="btn pri" value="ok">שמירה</button><button class="btn ghost" value="cancel" formnovalidate>ביטול</button></div></form>`;
    const f = $('lF');
    const hint = () => { const kd = f.kind.value; $('srcL').hidden = kd === 'none';
      $('srcH').textContent = kd === 'url' ? 'קישור https לסרטון: MP4, ‏YouTube (לא רשום) או Vimeo. מתאים לבדיקה — ההגנה המלאה תגיע עם Bunny.' : kd === 'bunny' ? 'מזהה הסרטון (Video ID) מ-Bunny Stream. הנגן יחובר בשלב 2ג.' : ''; };
    f.kind.onchange = hint; hint();
    f.ex.closest('label').hidden = !decks.some(hasEx);
    dl.onclose = () => {
      if (dl.returnValue !== 'ok') return;
      const files = f.files.value.split('\n').map(s => s.split('|').map(x => x.trim())).filter(a => a[0] && a[1]).map(([n, u]) => ({ n, u }));
      const nl = { ...l, title: f.title.value.trim(), desc: f.desc.value.trim(), kind: f.kind.value, src: f.kind.value === 'none' ? '' : f.src.value.trim(), dur: f.dur.value.trim(),
        sf: +f.sf.value || 0, st: +f.st.value || 0, ex: f.ex.checked, files, status: f.querySelector('[name=status]:checked').value };
      const bad = files.find(x => !/^https:\/\//.test(x.u)); if (bad) toast(`הקובץ "${bad.n}" לא נשמר: הקישור צריך להתחיל ב-https://`, 1);
      const nk = f.ch.value;
      if (i >= 0) { ch[k].splice(i, 1); if (!ch[k].length) delete ch[k]; }
      ch[nk] = ch[nk] || [];
      if (i >= 0 && nk === k) ch[nk].splice(Math.min(i, ch[nk].length), 0, nl); else ch[nk].push(nl);
      persist(decks, i >= 0 ? 'השיעור עודכן' : 'השיעור נוסף');
    };
    f.src.oninput = () => f.src.setCustomValidity('');
    f.querySelector('[value=ok]').onclick = e => { const kd = f.kind.value, v = f.src.value.trim();
      f.src.setCustomValidity(kd === 'url' && v && !/^https:\/\//.test(v) ? 'הקישור צריך להתחיל ב-https://' : kd === 'bunny' && v && !/^[a-zA-Z0-9-]{6,64}$/.test(v) ? 'מזהה Bunny לא תקין' : '');
      if (!f.reportValidity()) e.preventDefault(); };
    dl.showModal();
  }

  /* ------------------------------------------------------------ coming next */
  function progress() {
    $('v-progress').innerHTML = `<div class="vh"><h2>התקדמות צפייה</h2></div><div class="card soonc"><b>יגיע בשלב 2ג, יחד עם Bunny Stream</b>
      <p>כאן תופיע טבלה של תלמידים מול שיעורים, עם אחוז הצפייה בכל שיעור: אפור — לא התחיל, כתום — בצפייה, ירוק ✓ — נצפה (90% ומעלה, נמדד לפי שניות שנצפו בפועל).</p>
      <p>לכל שיעור: כמה תלמידים סיימו ואחוז צפייה ממוצע. בכרטיס התלמיד: ההתקדמות שלו בכל הקורסים. ייצוא ל-CSV, איפוס וסימון ידני על ידי מנהל בלבד.</p></div>`;
  }
  function log() {
    $('v-log').innerHTML = `<div class="vh"><h2>יומן פעולות</h2></div><div class="card soonc"><b>יגיע בשלב 2ד</b>
      <p>מי שינה מה ומתי: הזמנות, שינויי גישה, חסימות, שינויי הגדרות קורס ושינויים בעץ השיעורים. עד אז, ליד כל קורס אצל כל תלמיד נשמר מי שינה את הגישה ומתי, וגם הגדרות הקורס והעץ שומרים את העדכון האחרון.</p></div>`;
  }

  /* ------------------------------------------------------------ start */
  const st = document.createElement('style');
  st.textContent = `a.btn{display:inline-flex;align-items:center;text-decoration:none}.mut{color:var(--mute)}.sm{font-size:13px}.tw{overflow-x:auto}
.tb{width:100%;border-collapse:collapse;font-size:15px}.tb th{text-align:start;font-size:13px;color:var(--mute);font-weight:600;padding:6px 10px;border-bottom:1px solid var(--line)}
.tb td{padding:10px;border-bottom:1px solid var(--line)}.tb .lnk a{color:var(--teal-d);font-weight:600;text-decoration:none;margin-inline-end:10px;font-size:14px;white-space:nowrap}
.qk{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.qk div{display:flex;gap:8px;flex-wrap:wrap}.qk .btn{display:inline-flex;align-items:center;text-decoration:none}
.cg{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}.cc{display:grid;gap:10px;align-content:start}
.cch{display:flex;justify-content:space-between;align-items:baseline}.cch b{font-size:18px}
.cc .tg{font-size:14.5px;font-weight:600;padding:4px 0}.acts2{display:flex;gap:8px;flex-wrap:wrap}.acts2 .btn{display:inline-flex;align-items:center;text-decoration:none;min-height:36px;font-size:14px}
.ef{display:grid;gap:12px;margin-top:12px}.ef label{display:grid;gap:4px;font-weight:600;font-size:14px}
.ef textarea,.ef input,dialog textarea{padding:10px 12px;border-radius:10px;border:1.5px solid var(--line);background:var(--bg);color:var(--ink);font:inherit;width:100%;resize:vertical}
.ctab{display:flex;gap:6px;flex-wrap:wrap}.ctab a{padding:7px 14px;border-radius:999px;border:1.5px solid var(--line);text-decoration:none;color:var(--ink);font-weight:600;font-size:14.5px;background:var(--card)}
.ctab a.off{color:var(--mute);border-style:dashed}.ctab a.on{background:var(--navy);border-color:var(--navy);color:#fff}
.note{background:light-dark(#fff6ea,#3a2a14);border-radius:12px;padding:10px 14px;font-size:14.5px}.note a{color:inherit;font-weight:700}
#tree{display:grid;gap:12px}.tc{padding:14px}.tch2{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.tch2 b{flex:1;font-size:16.5px}.btn.sm{min-height:34px;font-size:14px;padding:0 12px}
.ll{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:6px;min-height:8px;border-radius:10px}.ll.over{outline:2px dashed var(--teal-d);outline-offset:3px}
.lr{display:flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:12px;padding:8px 10px;background:var(--card)}.lr.drag{opacity:.4}
.lr .gr{cursor:grab;color:var(--mute);letter-spacing:-3px;font-size:15px;user-select:none}.lr .no{flex:none;width:26px;height:26px;border-radius:50%;background:var(--soft);display:grid;place-items:center;font-size:12.5px;font-weight:700}
.lr .lt{flex:1;display:grid}.lr .lt b{font-size:15.5px;line-height:1.35}.lr .lt small{color:var(--mute);font-size:13px}
.lr .st{font-size:12px;font-weight:700;border-radius:999px;padding:2px 10px;background:#fde7c7;color:#7a4a05}.lr .st.pub{background:#d9f5e8;color:#11643f}
.lr .ra{display:flex;gap:4px}.lr .ra button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:4px 9px;cursor:pointer}
.lr .ra button:hover{border-color:var(--teal)}.lr .ra .del{color:var(--red)}
#ldlg{width:min(640px,96vw)}#ldlg form{max-height:76vh;overflow:auto;padding:2px}
.soonc{display:grid;gap:8px;max-width:760px}.soonc b{font-size:17px}.soonc p{margin:0;color:var(--mute)}
@media(max-width:700px){.lr{flex-wrap:wrap}.lr .ra{width:100%;justify-content:flex-end}}`;
  document.head.appendChild(st);
  document.addEventListener('bo:ready', () => {
    const side = $('side');
    side.innerHTML = NAV.map(([k, t, s]) => `<a href="#${k}" data-v="${k}"><svg viewBox="0 0 24 24" aria-hidden="true">${IC[k]}</svg>${t}${s ? `<span class="soon">${s}</span>` : ''}</a>`).join('');
    side.hidden = false;
    bo('GET', '?what=config').then(d => { cfg = d.config; }).catch(() => {});
    addEventListener('hashchange', route); route();
  });
})();
