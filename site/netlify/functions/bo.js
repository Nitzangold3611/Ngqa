// Backoffice API (v3.13) – admin only. Site settings per course and the recorded-lessons tree, kept in Netlify Blobs.
//  GET  ?what=config                 → { config }
//  GET  ?what=catalog&c=<course>     → { catalog }  (drafts included)
//  GET  ?what=summary                → { lessons: { <c>: { pub, draft } } }
//  POST { action: 'course', c, rec, pdf, info|null }
//  POST { action: 'catalog', c, ch }
const { COURSE_ROLES, isAdmin, getConfig, recList, json } = require('./_common');
const { cleanCatalog } = require('./_catalog');
const blobs = require('./_blobs');
const S = (v, n) => String(v == null ? '' : v).trim().slice(0, n);
const list = (a, n, m) => (Array.isArray(a) ? a : []).map(x => S(x, m)).filter(Boolean).slice(0, n);
function cleanInfo(x) {
  if (!x) return null;
  const i = { about: S(x.about, 1500), audience: list(x.audience, 10, 200), prereq: S(x.prereq, 400), goals: list(x.goals, 12, 200) };
  return i.about || i.audience.length || i.prereq || i.goals.length ? i : null;
}
exports.handler = async (event, context) => {
  const me = (context.clientContext || {}).user;
  if (!me) return json(401, { error: 'יש להתחבר' });
  if (!isAdmin(me)) return json(403, { error: 'אין הרשאת ניהול' });
  try {
    const st = blobs(event);
    const q = event.queryStringParameters || {};
    if (event.httpMethod === 'GET') {
      if (q.what === 'config') return json(200, { config: await getConfig(st), rec: recList(await getConfig(st)) });
      if (q.what === 'catalog') { if (!COURSE_ROLES.includes(q.c)) return json(400, { error: 'קורס לא מוכר' });
        return json(200, { catalog: (await st.get('catalog-' + q.c)) || { ch: {} } }); }
      if (q.what === 'summary') { const lessons = {};
        await Promise.all(COURSE_ROLES.map(async c => { const k = (await st.get('catalog-' + c)) || { ch: {} }; const all = Object.values(k.ch || {}).flat();
          lessons[c] = { pub: all.filter(l => l.status === 'pub').length, draft: all.filter(l => l.status !== 'pub').length }; }));
        return json(200, { lessons }); }
      return json(400, { error: 'בקשה לא מוכרת' });
    }
    if (event.httpMethod !== 'POST') return json(405, { error: 'method' });
    const b = JSON.parse(event.body || '{}');
    if (!COURSE_ROLES.includes(b.c)) return json(400, { error: 'קורס לא מוכר' });
    const stamp = { at: new Date().toISOString(), by: me.email };
    if (b.action === 'course') {
      const cfg = await getConfig(st), x = cfg.courses[b.c];
      if (typeof b.rec === 'boolean') x.rec = b.rec;
      if (typeof b.pdf === 'boolean') x.pdf = b.pdf;
      if ('info' in b) { const i = cleanInfo(b.info); if (i) x.info = i; else delete x.info; }
      Object.assign(x, stamp); Object.assign(cfg, stamp);
      await st.set('config', cfg);
      return json(200, { config: cfg, rec: recList(cfg) });
    }
    if (b.action === 'catalog') {
      const cat = { ch: cleanCatalog(b.ch), ...stamp };
      await st.set('catalog-' + b.c, cat);
      return json(200, { catalog: cat });
    }
    return json(400, { error: 'פעולה לא מוכרת' });
  } catch (e) { return json(500, { error: e.message || 'שגיאה' }); }
};
