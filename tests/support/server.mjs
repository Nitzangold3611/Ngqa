// Local stand-in for Netlify serving site/: static files, _redirects role locks, Identity, functions.
// Usage: node tests/support/server.mjs [port]
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { createIdentity, SERVICE_TOKEN } from "./gotrue-mock.mjs";
import { verify } from "./jwt.mjs";

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const SITE = path.join(ROOT, "site");
process.env.ADMIN_EMAILS = process.env.ADMIN_EMAILS || "owner@test.local";
const identity = createIdentity(SITE);
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".pdf": "application/pdf", ".webmanifest": "application/manifest+json", ".sql": "text/plain", ".txt": "text/plain" };

// ---- parse site/_redirects (role rules + plain rules) ----
export function parseRedirects(text) {
  return text.split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#")).map((l) => {
    const parts = l.split(/\s+/);
    const [from, to, statusRaw, ...rest] = parts;
    const cond = rest.find((x) => x.startsWith("Role="));
    return { from, to, status: parseInt(statusRaw, 10), force: /!$/.test(statusRaw || ""), roles: cond ? cond.slice(5).split(",") : null };
  });
}
const RULES = parseRedirects(fs.readFileSync(path.join(SITE, "_redirects"), "utf8")).filter((r) => r.from.startsWith("/"));
function match(rule, p) {
  if (rule.from.endsWith("/*")) { const base = rule.from.slice(0, -1); return p.startsWith(base) ? p.slice(base.length) : null; }
  return rule.from === p ? "" : null;
}
const cookie = (req, name) => (req.headers.cookie || "").split(/;\s*/).map((c) => c.split("=")).find(([k]) => k === name)?.[1];

function serveFile(res, rel) {
  let file = path.join(SITE, decodeURIComponent(rel));
  if (!file.startsWith(SITE)) return false;
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, "index.html");
  if (!fs.existsSync(file)) return false;
  res.writeHead(200, { "content-type": (types[path.extname(file)] || "application/octet-stream") + (/(html|javascript|css|json|plain)/.test(types[path.extname(file)] || "") ? ";charset=utf-8" : "") });
  fs.createReadStream(file).pipe(res);
  return true;
}

const port = Number(process.argv[2] || 8898);
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://localhost");
    let p = url.pathname;
    let body = ""; for await (const c of req) body += c;

    if (p.startsWith("/.netlify/identity")) {
      const r = await identity.handle(req.method, p.slice("/.netlify/identity".length) + url.search, req.headers, body);
      res.writeHead(r.status, { "content-type": "application/json" }); res.end(r.body === null ? "" : JSON.stringify(r.body)); return;
    }
    if (p.startsWith("/.netlify/functions/")) {
      const name = p.split("/")[3];
      const file = path.join(SITE, "netlify/functions", name + ".js");
      if (!/^[a-z-]+$/.test(name) || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
      const tok = /^Bearer (.+)$/.exec(req.headers.authorization || "")?.[1];
      const user = verify(tok);
      const origin = `http://127.0.0.1:${req.socket.localPort}`;
      const r = await require(file).handler(
        { httpMethod: req.method, body, headers: req.headers, path: p, queryStringParameters: Object.fromEntries(url.searchParams) },
        { clientContext: { identity: { url: origin + "/.netlify/identity", token: SERVICE_TOKEN }, user: user || undefined } });
      res.writeHead(r.statusCode, r.headers || {}); res.end(r.body || ""); return;
    }

    // _redirects: first matching rule wins (role rules only match when the JWT cookie has the role)
    for (const rule of RULES) {
      const splat = match(rule, p); if (splat === null) continue;
      if (rule.roles) {
        const c = verify(cookie(req, "nf_jwt"));
        const roles = (c && c.app_metadata && c.app_metadata.roles) || [];
        if (!roles.some((r) => rule.roles.includes(r))) continue;
      }
      const target = rule.to.replace(":splat", splat);
      if (rule.status === 404) { res.writeHead(404, { "content-type": "text/html" }); fs.createReadStream(path.join(SITE, "404.html")).pipe(res); return; }
      if (rule.status === 301 || rule.status === 302) { res.writeHead(rule.status, { location: target }); res.end(); return; }
      if (rule.status === 200) { p = target; break; }
    }
    if (!serveFile(res, p)) { res.writeHead(404, { "content-type": "text/html" }); fs.createReadStream(path.join(SITE, "404.html")).pipe(res); }
  } catch (e) { res.writeHead(500); res.end(String(e && e.stack || e)); }
});
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) server.listen(port, "127.0.0.1", () => console.log(`course test server on http://127.0.0.1:${port}`));
export { server, identity };
