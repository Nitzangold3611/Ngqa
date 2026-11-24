const COURSE_ROLES = ['ctfl', 'genai', 'sql', 'ste', 'ai', 'mat', 'jobs'];
// courses that have recorded lessons (role "<course>-rec" = full access incl. recordings). Pilot: genai.
const REC_COURSES = ['genai'];
const REC_ROLES = REC_COURSES.map(c => c + '-rec');
const ALL_ROLES = [...COURSE_ROLES, ...REC_ROLES, 'admin'];
const adminEmails = () => (process.env.ADMIN_EMAILS || '').toLowerCase().split(/[\s,;]+/).filter(Boolean);
const isAdmin = u => !!u && (((u.app_metadata && u.app_metadata.roles) || []).includes('admin') || adminEmails().includes(String(u.email || '').toLowerCase()));
module.exports = { COURSE_ROLES, REC_COURSES, REC_ROLES, ALL_ROLES, adminEmails, isAdmin };
