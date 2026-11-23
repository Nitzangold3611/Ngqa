// Access lock date (v3.9): course files are refused once the date in the user's token
// (app_metadata.expires, YYYY-MM-DD, set in /admin) has arrived — counted in Israel time.
// Runs before the role-based redirects in _redirects. It can only take access away, never grant it,
// so reading the cookie without checking its signature is safe: the role check still applies afterwards.
const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jerusalem' }).format(new Date());

export default async (req, context) => {
  const m = (req.headers.get('cookie') || '').match(/(?:^|;\s*)nf_jwt=([^;]+)/);
  if (m) {
    try {
      let b = m[1].split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      b += '='.repeat((4 - b.length % 4) % 4);
      const am = JSON.parse(atob(b)).app_metadata || {};
      if (am.expires && !(am.roles || []).includes('admin') && today() >= am.expires)
        return Response.redirect(new URL('/?expired=' + encodeURIComponent(am.expires), req.url), 302);
    } catch (e) { /* unreadable cookie: leave it to the role check */ }
  }
  return context.next();
};

export const config = { path: '/courses/*' };
