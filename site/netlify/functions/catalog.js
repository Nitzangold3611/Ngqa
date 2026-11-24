// Recorded lessons of a course for the signed-in student (v3.13). GET ?c=<course>
// Students with the course get the published tree; the video source only with recordings access ("<c>-rec",
// recordings date not passed, recordings enabled for the course). Admins also get drafts.
const { COURSE_ROLES, isAdmin, getConfig, json } = require('./_common');
const blobs = require('./_blobs');
const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jerusalem' }).format(new Date());
exports.handler = async (event, context) => {
  const me = (context.clientContext || {}).user;
  if (!me) return json(401, { error: 'יש להתחבר' });
  const c = (event.queryStringParameters || {}).c;
  if (!COURSE_ROLES.includes(c)) return json(400, { error: 'קורס לא מוכר' });
  const am = me.app_metadata || {}, roles = am.roles || [], admin = isAdmin(me), t = today();
  const a = (am.access || {})[c] || {};
  if (!admin && (am.blocked || (am.expires && t >= am.expires) || !roles.includes(c) || (a.m && t >= a.m))) return json(403, { error: 'אין גישה לקורס' });
  try {
    const st = blobs(event), cfg = await getConfig(st);
    const recOn = cfg.courses[c].rec;
    const rec = recOn && (admin || (roles.includes(c + '-rec') && !(a.r && t >= a.r)));
    const cat = (await st.get('catalog-' + c)) || { ch: {} }, ch = {};
    for (const [k, ls] of Object.entries(cat.ch || {})) {
      const v = ls.filter(l => admin || l.status === 'pub').map(l => rec ? l : { ...l, src: '', kind: l.kind === 'none' ? 'none' : 'locked', files: [] });
      if (v.length) ch[k] = v;
    }
    return json(200, { rec, recOn, admin, ch: recOn ? ch : {} });
  } catch (e) { return json(500, { error: e.message || 'שגיאה' }); }
};
