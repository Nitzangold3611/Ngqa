const COURSE_ROLES = ['ctfl', 'genai', 'sql', 'ste'];
const ALL_ROLES = [...COURSE_ROLES, 'admin'];
const adminEmails = () => (process.env.ADMIN_EMAILS || '').toLowerCase().split(/[\s,;]+/).filter(Boolean);
const isAdmin = u => !!u && (((u.app_metadata && u.app_metadata.roles) || []).includes('admin') || adminEmails().includes(String(u.email || '').toLowerCase()));
module.exports = { COURSE_ROLES, ALL_ROLES, adminEmails, isAdmin };
