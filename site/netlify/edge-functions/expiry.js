// Access dates, enforced on the server before the role-based redirects in _redirects.
//  v3.9  app_metadata.expires = YYYY-MM-DD → the whole site is locked from that date (Israel time).
//  v3.11 app_metadata.access[<course>] = { m, r } → end date of the course materials (m) and of the
//        recorded lessons (r, path /courses/<course>/lessons/…).
// It can only take access away, never grant it, so reading the cookie without checking its signature
// is safe: the role check in _redirects still applies afterwards. Admins are never locked.
const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jerusalem' }).format(new Date());

export default async (req, context) => {
  const m = (req.headers.get('cookie') || '').match(/(?:^|;\s*)nf_jwt=([^;]+)/);
  if (m) {
    try {
      let b = m[1].split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      b += '='.repeat((4 - b.length % 4) % 4);
      const am = JSON.parse(atob(b)).app_metadata || {};
      if (!(am.roles || []).includes('admin')) {
        const t = today();
        if (am.expires && t >= am.expires)
          return Response.redirect(new URL('/?expired=' + encodeURIComponent(am.expires), req.url), 302);
        const p = new URL(req.url).pathname.match(/^\/courses\/([a-z0-9-]+)\/(lessons\/)?/);
        const a = p && am.access && am.access[p[1]];
        if (a) {
          if (a.m && t >= a.m)
            return Response.redirect(new URL('/?cexp=' + encodeURIComponent(p[1] + ':' + a.m), req.url), 302);
          if (p[2] && a.r && t >= a.r)
            return Response.redirect(new URL('/courses/' + p[1] + '/?norec=' + encodeURIComponent(a.r), req.url), 302);
        }
      }
    } catch (e) { /* unreadable cookie: leave it to the role check */ }
  }
  return context.next();
};

export const config = { path: '/courses/*' };
