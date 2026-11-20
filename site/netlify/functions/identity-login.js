// Runs on every Netlify Identity login. Makes the owner (ADMIN_EMAILS env var) an admin with access to every course.
const { ALL_ROLES, adminEmails } = require('./_common');
exports.handler = async (event) => {
  let user;
  try { ({ user } = JSON.parse(event.body || '{}')); } catch (e) { return { statusCode: 204 }; }
  if (!user || !adminEmails().includes(String(user.email || '').toLowerCase())) return { statusCode: 204 };
  const am = user.app_metadata || {};
  const roles = Array.from(new Set([...(am.roles || []), ...ALL_ROLES]));
  return { statusCode: 200, body: JSON.stringify({ app_metadata: { ...am, roles, blocked: false } }) };
};
