// In-memory stand-in for Netlify Identity (GoTrue) – only the endpoints the site uses.
// Runs the site's real identity-login / identity-signup functions as hooks, like Netlify does.
import { randomUUID } from "node:crypto";
import { createRequire } from "node:module";
import path from "node:path";
import { sign, verify } from "./jwt.mjs";

const require = createRequire(import.meta.url);
export const SERVICE_TOKEN = "service-token-for-functions";

export function createIdentity(siteDir) {
  const hookLogin = require(path.join(siteDir, "netlify/functions/identity-login.js")).handler;
  const hookSignup = require(path.join(siteDir, "netlify/functions/identity-signup.js")).handler;
  const users = new Map();          // id -> user
  const refresh = new Map();        // refresh token -> user id
  const tokens = new Map();         // invite/recovery token -> {id,type}
  const outbox = [];                // "sent" e-mails

  const byEmail = (e) => [...users.values()].find((u) => u.email === String(e || "").toLowerCase());
  const pub = (u) => { const { password, ...rest } = u; return rest; };
  const claims = (u) => ({ sub: u.id, email: u.email, app_metadata: u.app_metadata, user_metadata: u.user_metadata });
  async function runHook(fn, u) {
    const r = await fn({ body: JSON.stringify({ event: "login", user: pub(u) }) });
    if (r && r.statusCode === 200 && r.body) { const d = JSON.parse(r.body); if (d.app_metadata) u.app_metadata = d.app_metadata; if (d.user_metadata) u.user_metadata = d.user_metadata; }
  }
  function issue(u) {
    const rt = randomUUID(); refresh.set(rt, u.id); u.last_sign_in_at = new Date().toISOString();
    return { access_token: sign(claims(u)), token_type: "bearer", expires_in: 3600, refresh_token: rt };
  }
  const json = (status, body) => ({ status, body });
  const err = (status, error, desc) => json(status, { error, error_description: desc || error, msg: desc || error });
  const bearer = (h) => { const m = /^Bearer (.+)$/.exec(h || ""); return m ? m[1] : null; };

  function addUser({ email, password = null, roles = [], name = "", blocked = false, confirmed = true }) {
    const u = { id: randomUUID(), email: email.toLowerCase(), password, confirmed_at: confirmed ? new Date().toISOString() : null,
      invited_at: null, created_at: new Date().toISOString(), last_sign_in_at: null,
      app_metadata: { provider: "email", roles, ...(blocked ? { blocked: true } : {}) }, user_metadata: { full_name: name } };
    users.set(u.id, u); return u;
  }

  async function handle(method, sub, headers, rawBody) {
    let body = {};
    if (rawBody) { try { body = JSON.parse(rawBody); } catch { body = Object.fromEntries(new URLSearchParams(rawBody)); } }
    const url = new URL("http://x" + sub);
    const p = url.pathname;

    // ---- test-only helpers (exist only in this stand-in) ----
    if (p === "/__test/users" && method === "POST") { const out = (body.users || []).map((x) => pub(addUser(x))); return json(200, { users: out }); }
    if (p === "/__test/users" && method === "GET") return json(200, { users: [...users.values()].map(pub) });
    if (p === "/__test/mail") return json(200, { mail: outbox });
    if (p === "/__test/reset" && method === "POST") { users.clear(); refresh.clear(); tokens.clear(); outbox.length = 0; return json(200, {}); }

    if (p === "/settings") return json(200, { external: { google: true, email: true }, disable_signup: true, autoconfirm: false });

    if (p === "/token" && method === "POST") {
      if (body.grant_type === "password") {
        const u = byEmail(body.username);
        if (!u) return err(400, "invalid_grant", "No user found with that email, or password invalid.");
        if (!u.confirmed_at) return err(400, "invalid_grant", "Email not confirmed");
        if (u.password !== body.password) return err(400, "invalid_grant", "No user found with that email, or password invalid.");
        await runHook(hookLogin, u);
        return json(200, issue(u));
      }
      if (body.grant_type === "refresh_token") {
        const id = refresh.get(body.refresh_token); const u = id && users.get(id);
        if (!u) return err(400, "invalid_grant", "Invalid Refresh Token");
        return json(200, issue(u));
      }
      return err(400, "unsupported_grant_type");
    }
    if (p === "/user") {
      const c = verify(bearer(headers.authorization)); const u = c && users.get(c.sub);
      if (!u) return err(401, "unauthorized", "Invalid token");
      if (method === "PUT") {
        if (body.password) { if (String(body.password).length < 8) return err(422, "invalid", "Password should be at least 8 characters"); u.password = body.password; }
        if (body.data) u.user_metadata = { ...u.user_metadata, ...body.data };
      }
      return json(200, pub(u));
    }
    if (p === "/verify" && method === "POST") {
      const t = tokens.get(body.token);
      if (!t || (body.type === "signup" && t.type !== "invite") || (body.type === "recovery" && t.type !== "recovery")) return err(404, "not_found", "Invalid token");
      const u = users.get(t.id); tokens.delete(body.token);
      if (body.type === "signup") { if (body.password) u.password = body.password; u.confirmed_at = new Date().toISOString(); await runHook(hookSignup, u); }
      return json(200, issue(u));
    }
    if (p === "/recover" && method === "POST") {
      const u = byEmail(body.email);
      if (u) { const tk = randomUUID(); tokens.set(tk, { id: u.id, type: "recovery" }); outbox.push({ to: u.email, type: "recovery", token: tk }); }
      return json(200, {});
    }
    if (p === "/logout") return json(204, null);

    // ---- admin API (used by the admin function with the service token) ----
    const isService = bearer(headers.authorization) === SERVICE_TOKEN;
    if (p === "/invite" && method === "POST") {
      if (!isService) return err(401, "unauthorized");
      const email = String(body.email || "").toLowerCase();
      let u = byEmail(email);
      if (u && u.confirmed_at) return err(422, "invalid", "A user with this email address has already been registered");
      if (!u) u = addUser({ email, confirmed: false, name: (body.data || {}).full_name || "" });
      u.invited_at = new Date().toISOString();
      const tk = randomUUID(); tokens.set(tk, { id: u.id, type: "invite" }); outbox.push({ to: email, type: "invite", token: tk });
      return json(200, pub(u));
    }
    if (p === "/admin/users") {
      if (!isService) return err(401, "unauthorized");
      const page = +url.searchParams.get("page") || 1, per = +url.searchParams.get("per_page") || 50;
      const all = [...users.values()].map(pub);
      return json(200, { users: all.slice((page - 1) * per, page * per) });
    }
    const m = /^\/admin\/users\/([^/]+)$/.exec(p);
    if (m) {
      if (!isService) return err(401, "unauthorized");
      const u = users.get(decodeURIComponent(m[1]));
      if (!u) return err(404, "not_found", "User not found");
      if (method === "PUT") { if (body.app_metadata) u.app_metadata = body.app_metadata; if (body.user_metadata) u.user_metadata = body.user_metadata; }
      if (method === "DELETE") { users.delete(u.id); return json(200, {}); }
      return json(200, pub(u));
    }
    return err(404, "not_found", "no route " + p);
  }
  return { handle, addUser, users, outbox, claimsFor: (token) => verify(token) };
}
