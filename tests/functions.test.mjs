// Server functions (admin API, Identity hooks) and the per-course lock, run against the local Netlify stand-in.
// node --test tests/functions.test.mjs
import { test, describe, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

process.env.ADMIN_EMAILS = "owner@test.local";
const { server, identity } = await import("./support/server.mjs");
const { sign } = await import("./support/jwt.mjs");
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const hook = require(path.join(ROOT, "site/netlify/functions/identity-login.js")).handler;

let base;
before(async () => { await new Promise((r) => server.listen(0, "127.0.0.1", r)); base = `http://127.0.0.1:${server.address().port}`; });
after(() => server.close());
beforeEach(() => { identity.users.clear(); identity.outbox.length = 0; });

const PW = "Password123";
const add = (email, roles = [], extra = {}) => identity.addUser({ email, password: PW, roles, ...extra });
async function login(email, password = PW) {
  const r = await fetch(base + "/.netlify/identity/token", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ grant_type: "password", username: email, password }) });
  return { status: r.status, data: await r.json() };
}
async function adminApi(token, method, body) {
  const r = await fetch(base + "/.netlify/functions/admin", { method, headers: { "content-type": "application/json", ...(token ? { authorization: "Bearer " + token } : {}) }, body: body ? JSON.stringify(body) : undefined });
  return { status: r.status, data: await r.json() };
}
const ownerToken = async () => { add("owner@test.local"); return (await login("owner@test.local")).data.access_token; };
const page = (p, jwt) => fetch(base + p, { redirect: "manual", headers: jwt ? { cookie: `nf_jwt=${jwt}` } : {} });

describe("הוק הכניסה (identity-login)", () => {
  test("בעל האתר מקבל הרשאת מנהל וגישה לכל הקורסים, וחסימה מתבטלת", async () => {
    const r = await hook({ body: JSON.stringify({ user: { email: "OWNER@test.local", app_metadata: { roles: ["ctfl"], blocked: true } } }) });
    const am = JSON.parse(r.body).app_metadata;
    assert.equal(r.statusCode, 200);
    assert.deepEqual([...am.roles].sort(), ["admin", "ctfl", "genai", "sql"]);
    assert.equal(am.blocked, false);
  });
  test("משתמש רגיל לא משתנה, וגוף לא תקין לא מפיל את הכניסה", async () => {
    assert.equal((await hook({ body: JSON.stringify({ user: { email: "s@test.local", app_metadata: {} } }) })).statusCode, 204);
    assert.equal((await hook({ body: "not json" })).statusCode, 204);
  });
});

describe("כניסה", () => {
  test("סיסמה שגויה ומשתמש שלא קיים מקבלים אותה תשובה", async () => {
    add("s@test.local");
    const a = await login("s@test.local", "wrong"), b = await login("nobody@test.local");
    assert.equal(a.status, 400); assert.equal(a.data.error_description, b.data.error_description);
  });
  test("משתמש שהוזמן ועוד לא השלים הרשמה לא יכול להיכנס", async () => {
    identity.addUser({ email: "p@test.local", password: PW, confirmed: false });
    assert.match((await login("p@test.local")).data.error_description, /not confirmed/);
  });
});

describe("נעילת הקורסים בשרת", () => {
  test("בלי התחברות: כל קורס מפנה להתחברות עם חזרה לקורס", async () => {
    for (const id of ["ctfl", "genai", "sql"]) {
      const r = await page(`/courses/${id}/`);
      assert.equal(r.status, 302, id);
      assert.equal(r.headers.get("location"), `/?login=1&next=/courses/${id}/`);
      const f = await page(`/courses/${id}/decks.json`);
      assert.equal(f.status, 302, `${id} files are locked too`);
    }
  });
  test("תלמיד עם הרשאה לקורס אחד נכנס רק אליו", async () => {
    const jwt = sign({ sub: "1", email: "s@test.local", app_metadata: { roles: ["ctfl"] } });
    assert.equal((await page("/courses/ctfl/", jwt)).status, 200);
    assert.equal((await page("/courses/ctfl/decks.json", jwt)).status, 200);
    assert.equal((await page("/courses/genai/", jwt)).status, 302);
    assert.equal((await page("/courses/sql/decks.json", jwt)).status, 302);
  });
  test("מנהל נכנס לכל הקורסים", async () => {
    const jwt = sign({ sub: "1", email: "a@test.local", app_metadata: { roles: ["admin"] } });
    for (const id of ["ctfl", "genai", "sql"]) assert.equal((await page(`/courses/${id}/`, jwt)).status, 200, id);
  });
  test("טוקן מזויף או שפג תוקפו לא פותח קורס", async () => {
    const good = sign({ sub: "1", email: "s@test.local", app_metadata: { roles: ["ctfl"] } });
    const [h, , s] = good.split(".");
    const forgedBody = Buffer.from(JSON.stringify({ sub: "1", app_metadata: { roles: ["admin"] }, exp: 9e9 })).toString("base64url");
    assert.equal((await page("/courses/ctfl/", `${h}.${forgedBody}.${s}`)).status, 302);
    assert.equal((await page("/courses/ctfl/", sign({ sub: "1", app_metadata: { roles: ["ctfl"] } }, -10))).status, 302);
  });
  test("קובצי הקוד של השרת לא נגישים", async () => {
    assert.equal((await page("/netlify/functions/admin.js")).status, 404);
  });
});

describe("פונקציית הניהול (admin)", () => {
  test("בלי התחברות 401, תלמיד 403, בעל האתר מקבל את הרשימה", async () => {
    add("s@test.local", ["ctfl"]);
    const st = (await login("s@test.local")).data.access_token;
    assert.equal((await adminApi(null, "GET")).status, 401);
    assert.equal((await adminApi(st, "GET")).status, 403);
    const r = await adminApi(await ownerToken(), "GET");
    assert.equal(r.status, 200);
    assert.deepEqual(r.data.courses, ["ctfl", "genai", "sql"]);
    assert.ok(r.data.users.some((u) => u.email === "s@test.local"));
    assert.ok(r.data.users.every((u) => !("password" in u)));
  });
  test("הזמנה: מייל לא תקין נדחה; הזמנה תקינה שולחת מייל ופותחת קורסים בלי הרשאת מנהל", async () => {
    const t = await ownerToken();
    assert.equal((await adminApi(t, "POST", { action: "invite", email: "bad" })).status, 400);
    const r = await adminApi(t, "POST", { action: "invite", email: " New@Test.local ", name: "חדש", roles: ["ctfl", "admin", "hack"] });
    assert.equal(r.status, 200);
    assert.equal(r.data.user.email, "new@test.local");
    assert.deepEqual(r.data.user.roles, ["ctfl"]);
    assert.equal(r.data.user.confirmed, false);
    assert.ok(identity.outbox.some((m) => m.to === "new@test.local" && m.type === "invite"));
  });
  test("הזמנה של מייל שכבר רשום מחזירה הודעה בעברית", async () => {
    const t = await ownerToken();
    add("exists@test.local");
    const r = await adminApi(t, "POST", { action: "invite", email: "exists@test.local" });
    assert.equal(r.data.error, "המייל הזה כבר רשום");
  });
  test("שינוי הרשאות; מנהל לא יכול להוריד לעצמו את הרשאת המנהל", async () => {
    const t = await ownerToken();
    const s = add("s@test.local", ["ctfl"]);
    let r = await adminApi(t, "POST", { action: "roles", id: s.id, roles: ["genai", "sql", "bogus"] });
    assert.deepEqual(r.data.user.roles, ["genai", "sql"]);
    const me = [...identity.users.values()].find((u) => u.email === "owner@test.local");
    r = await adminApi(t, "POST", { action: "roles", id: me.id, roles: ["ctfl"] });
    assert.ok(r.data.user.roles.includes("admin"));
  });
  test("חסימה מסירה גישה ושומרת אותה; ביטול חסימה מחזיר בדיוק את מה שהיה", async () => {
    const t = await ownerToken();
    const s = add("s@test.local", ["ctfl", "sql"]);
    let r = await adminApi(t, "POST", { action: "block", id: s.id, blocked: true });
    assert.equal(r.data.user.blocked, true); assert.deepEqual(r.data.user.roles, []);
    r = await adminApi(t, "POST", { action: "block", id: s.id, blocked: false });
    assert.equal(r.data.user.blocked, false); assert.deepEqual(r.data.user.roles, ["ctfl", "sql"]);
  });
  test("אי אפשר לחסום או למחוק את עצמך", async () => {
    const t = await ownerToken();
    const me = [...identity.users.values()].find((u) => u.email === "owner@test.local");
    assert.equal((await adminApi(t, "POST", { action: "block", id: me.id, blocked: true })).status, 400);
    assert.equal((await adminApi(t, "POST", { action: "delete", id: me.id })).status, 400);
  });
  test("שליחה חוזרת רק למי שלא השלים הרשמה; איפוס סיסמה שולח קישור", async () => {
    const t = await ownerToken();
    const done = add("done@test.local");
    const pend = identity.addUser({ email: "pend@test.local", confirmed: false });
    assert.equal((await adminApi(t, "POST", { action: "resend", id: done.id })).status, 400);
    assert.equal((await adminApi(t, "POST", { action: "resend", id: pend.id })).status, 200);
    assert.equal((await adminApi(t, "POST", { action: "recover", id: done.id })).status, 200);
    assert.ok(identity.outbox.some((m) => m.to === "done@test.local" && m.type === "recovery"));
  });
  test("מחיקה מסירה את המשתמש; פעולה לא מוכרת ושיטה לא נתמכת נדחות", async () => {
    const t = await ownerToken();
    const s = add("s@test.local");
    assert.equal((await adminApi(t, "POST", { action: "delete", id: s.id })).status, 200);
    assert.ok(![...identity.users.values()].some((u) => u.email === "s@test.local"));
    assert.equal((await adminApi(t, "POST", { action: "nope" })).status, 400);
    assert.equal((await adminApi(t, "PUT", {})).status, 405);
  });
});
