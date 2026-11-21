// Minimal HS256 JWT for the local Identity stand-in.
import { createHmac } from "node:crypto";
export const SECRET = "ngqa-test-jwt-secret";
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString("base64url");
export function sign(claims, ttl = 3600) {
  const body = b64({ ...claims, exp: Math.floor(Date.now() / 1000) + ttl });
  const head = b64({ alg: "HS256", typ: "JWT" });
  const sig = createHmac("sha256", SECRET).update(`${head}.${body}`).digest("base64url");
  return `${head}.${body}.${sig}`;
}
export function verify(token) {
  const [h, b, s] = String(token || "").split(".");
  if (!h || !b || !s) return null;
  const exp = createHmac("sha256", SECRET).update(`${h}.${b}`).digest("base64url");
  if (exp !== s) return null;
  try { const c = JSON.parse(Buffer.from(b, "base64url").toString()); return c.exp * 1000 > Date.now() ? c : null; } catch { return null; }
}
