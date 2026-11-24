const COURSE_ROLES = ['ctfl', 'genai', 'sql', 'ste', 'ai', 'mat', 'jobs'];
// v3.13: which courses have recorded lessons is set in the backoffice (Blobs key "config"); default: genai.
// Every course may carry a "<course>-rec" role (= full access incl. recordings).
const DEFAULT_REC = ['genai'];
const REC_COURSES = DEFAULT_REC; // legacy name
const REC_ROLES = COURSE_ROLES.map(c => c + '-rec');
const ALL_ROLES = [...COURSE_ROLES, ...REC_ROLES, 'admin'];
const adminEmails = () => (process.env.ADMIN_EMAILS || '').toLowerCase().split(/[\s,;]+/).filter(Boolean);
const isAdmin = u => !!u && (((u.app_metadata && u.app_metadata.roles) || []).includes('admin') || adminEmails().includes(String(u.email || '').toLowerCase()));
// site settings kept in Netlify Blobs (key "config"): { courses: { <c>: { rec, pdf, info } }, at, by }
async function getConfig(store) { let c = null; try { c = await store.get('config'); } catch (e) { c = null; }
  c = c && typeof c === 'object' ? c : {}; c.courses = c.courses || {};
  for (const k of COURSE_ROLES) { const x = c.courses[k] = c.courses[k] || {}; if (typeof x.rec !== 'boolean') x.rec = DEFAULT_REC.includes(k); if (typeof x.pdf !== 'boolean') x.pdf = true; }
  return c; }
const recList = cfg => COURSE_ROLES.filter(k => cfg.courses[k].rec);
const json = (statusCode, body, cache) => ({ statusCode, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': cache || 'no-store' }, body: JSON.stringify(body) });
module.exports = { getConfig, recList, json, DEFAULT_REC, COURSE_ROLES, REC_COURSES, REC_ROLES, ALL_ROLES, adminEmails, isAdmin };
