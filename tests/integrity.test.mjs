// Static checks on the published site (site/) – content, links, security config, consistency.
// node --test tests/integrity.test.mjs
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseRedirects } from "./support/server.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE = path.join(ROOT, "site");
const read = (p) => fs.readFileSync(path.join(SITE, p), "utf8");
const exists = (p) => fs.existsSync(path.join(SITE, p));
const json = (p) => JSON.parse(read(p));

const authJs = read("auth.js");
const AUTH_IDS = [...authJs.matchAll(/\{ id: '([a-z0-9-]+)', name: '[^']+', path: '\/courses\/\1\/' \}/g)].map((m) => m[1]);
const COMMON_IDS = JSON.parse(read("netlify/functions/_common.js").match(/COURSE_ROLES = (\[[^\]]*\])/)[1].replace(/'/g, '"'));
const COURSES_JSON = json("courses.json");
const COURSE_DIRS = fs.readdirSync(path.join(SITE, "courses")).filter((d) => fs.statSync(path.join(SITE, "courses", d)).isDirectory());
const HOME = read("index.html");
const IDS = [...COURSE_DIRS].sort();

function htmlFiles(dir = SITE, out = []) {
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    if (f === "netlify" || f === "node_modules") continue;
    if (fs.statSync(p).isDirectory()) htmlFiles(p, out); else if (f.endsWith(".html")) out.push(p);
  }
  return out;
}

describe("רשימת הקורסים עקבית בכל המקומות", () => {
  test("auth.js, הרשאות השרת, courses.json ותיקיות הקורסים תואמים", () => {
    assert.deepEqual([...AUTH_IDS].sort(), IDS, "auth.js COURSES");
    assert.deepEqual([...COMMON_IDS].sort(), IDS, "_common.js COURSE_ROLES");
    assert.deepEqual(Object.keys(COURSES_JSON).sort(), IDS, "courses.json");
  });
  test("לכל קורס יש כרטיס בעמוד הראשי ומקום בחיפוש הכללי ובדף הניהול", () => {
    const admin = read("admin/index.html");
    for (const id of IDS) {
      assert.match(HOME, new RegExp(`href="/courses/${id}/" data-c="${id}"`), `home card ${id}`);
      assert.match(HOME, new RegExp(`\\{id:'${id}',name:`), `hub search ${id}`);
      assert.match(admin, new RegExp(`${id}:'`), `admin NAMES ${id}`);
    }
  });
});

describe("אבטחה: נעילת הקורסים בשרת", () => {
  const rules = parseRedirects(read("_redirects"));
  for (const id of IDS) {
    test(`הקורס ${id} נעול: מותר רק להרשאה ${id} או מנהל, ומי שאין לו הרשאה מופנה להתחברות`, () => {
      const allow = rules.findIndex((r) => r.from === `/courses/${id}/*` && r.roles && r.status === 200 && r.force);
      const deny = rules.findIndex((r) => r.from === `/courses/${id}/*` && !r.roles && r.status === 302 && r.force);
      assert.ok(allow >= 0, "missing role rule");
      assert.deepEqual([...rules[allow].roles].sort(), ["admin", id].sort());
      assert.ok(deny > allow, "fallback redirect must come after the role rule");
      assert.equal(rules[deny].to, `/?login=1&next=/courses/${id}/`);
    });
    test(`עמוד הקורס ${id} בודק הרשאה לפני שהוא מוצג`, () => {
      const h = read(`courses/${id}/index.html`);
      const guardAt = h.indexOf(`NGQAAuth.guard('${id}')`);
      assert.ok(guardAt > 0, "guard call");
      assert.ok(h.indexOf('src="/auth.js"') < guardAt, "auth.js loads before guard");
      assert.match(h.slice(0, guardAt), /style\.visibility='hidden'/);
    });
  }
  test("קובצי השרת (netlify/) לא נגישים מהאתר", () => {
    assert.ok(rules.some((r) => r.from === "/netlify/*" && r.status === 404 && r.force));
  });
  test("כותרות אבטחה מוגדרות לכל האתר", () => {
    const h = read("_headers");
    for (const k of ["X-Content-Type-Options: nosniff", "X-Frame-Options", "Referrer-Policy"]) assert.ok(h.includes(k), k);
  });
  test("אין סודות או מפתחות בקוד", () => {
    const bad = /(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{30,}|nfp_[A-Za-z0-9]{20,})/;
    const files = [];
    (function walk(d) { for (const f of fs.readdirSync(d)) { const p = path.join(d, f); if (/\.git$|node_modules|\.(jpg|png|pdf|pptx|zip|ico)$/i.test(p)) continue; fs.statSync(p).isDirectory() ? walk(p) : files.push(p); } })(ROOT);
    for (const f of files) { const t = fs.readFileSync(f, "utf8"); assert.ok(!bad.test(t), `secret-like string in ${path.relative(ROOT, f)}`); }
  });
});

describe("תוכן הקורסים", () => {
  for (const id of IDS) {
    test(`${id}: מספר הפרקים, השקפים והתרגילים בעמוד הראשי תואם למצגות`, () => {
      const decks = json(`courses/${id}/decks.json`);
      const c = COURSES_JSON[id];
      assert.equal(decks.length, c.chapters, "chapters");
      assert.equal(decks.reduce((a, d) => a + d.slides.length, 0), c.slides, "slides");
      const pages = decks.reduce((a, d) => a + (d.ex ? d.ex.length : 0), 0);
      const questions = decks.reduce((a, d) => a + (d.ex || []).reduce((b, e) => b + (e.items ? e.items.length : 0), 0), 0);
      if (c.exlabel) {
        // counted in questions (e.g. SQL "שאלות תרגול"); summary exercises add more questions outside decks.json
        assert.ok(c.exercises >= questions, `exercises ${c.exercises} < questions in decks ${questions}`);
      } else if (pages || c.exercises) assert.equal(pages, c.exercises, "exercises");
    });
    test(`${id}: כל קובצי השקפים, השערים והתמונות קיימים`, () => {
      const decks = json(`courses/${id}/decks.json`);
      const missing = new Set();
      for (const d of decks) {
        for (const f of [d.cover, ...d.slides.map((s) => s.img)]) {
          if (!f) continue;
          const rel = `courses/${id}/${f.split("?")[0]}`;
          if (!exists(rel)) missing.add(rel);
        }
      }
      assert.deepEqual([...missing], []);
    });
    test(`${id}: קישורים פנימיים בשקפים ובתוכן העניינים מפנים לשקף קיים`, () => {
      const decks = json(`courses/${id}/decks.json`);
      const bad = [];
      for (const d of decks) {
        const n = d.slides.length;
        for (const t of d.toc || []) if (t.slide < 1 || t.slide > n) bad.push(`${d.id} toc ${t.num} -> ${t.slide}`);
        d.slides.forEach((s, i) => (s.links || []).forEach((l) => { if (l.slide && (l.slide < 1 || l.slide > n)) bad.push(`${d.id} slide ${i + 1} -> ${l.slide}`); }));
      }
      assert.deepEqual(bad, []);
    });
    test(`${id}: אינדקס החיפוש תקין ומפנה רק לשקפים קיימים`, () => {
      const decks = json(`courses/${id}/decks.json`);
      const s = json(`courses/${id}/search.json`);
      assert.ok(Array.isArray(s.slides) && s.slides.length > 0);
      const bad = s.slides.filter((x) => !decks[x.c - 1] || x.s < 1 || x.s > decks[x.c - 1].slides.length);
      assert.equal(bad.length, 0, JSON.stringify(bad.slice(0, 3)));
      assert.equal(s.slides.length, decks.reduce((a, d) => a + d.slides.length, 0), "every slide is searchable");
    });
  }
});

describe("עמודים, קישורים ונגישות בסיסית", () => {
  const pages = htmlFiles();
  test("כל הקישורים והקבצים המקומיים בעמודים קיימים", () => {
    const broken = [];
    for (const f of pages) {
      const h = fs.readFileSync(f, "utf8");
      for (const m of h.matchAll(/(?:href|src)="([^"]+)"/g)) {
        const u = m[1];
        if (/^(https?:|mailto:|tel:|#|data:|javascript:|\/\/)/.test(u) || u.includes("${")) continue;
        const clean = u.split("#")[0].split("?")[0];
        if (!clean) continue;
        const target = clean.startsWith("/") ? path.join(SITE, clean) : path.join(path.dirname(f), clean);
        const ok = fs.existsSync(target) && (fs.statSync(target).isFile() || fs.existsSync(path.join(target, "index.html")));
        if (!ok) broken.push(`${path.relative(SITE, f)} -> ${u}`);
      }
    }
    assert.deepEqual(broken, []);
  });
  test("כל העמודים בעברית, מימין לשמאל, ומותאמים לטלפון", () => {
    for (const f of pages) {
      const h = fs.readFileSync(f, "utf8");
      assert.match(h, /<html lang="he" dir="rtl">/, path.relative(SITE, f));
      assert.match(h, /name="viewport"/, path.relative(SITE, f));
    }
  });
  test("כפתור הוואטסאפ לניצן נטען בכל עמודי התלמידים", () => {
    const missing = pages.filter((f) => !/\/admin\//.test(f) && !fs.readFileSync(f, "utf8").includes('src="/wa.js"')).map((f) => path.relative(SITE, f));
    assert.deepEqual(missing, []);
    assert.match(read("wa.js"), /PHONE = '972526718757'/);
  });
  test("קבצי ה-JSON והמניפסט תקינים, והאייקונים קיימים", () => {
    const man = json("manifest.webmanifest");
    for (const i of man.icons) assert.ok(exists(i.src.replace(/^\//, "")), i.src);
    for (const id of IDS) for (const f of ["decks.json", "search.json"]) json(`courses/${id}/${f}`);
  });
});

describe("גרסאות ותיעוד", () => {
  const readme = fs.readFileSync(path.join(ROOT, "README.md"), "utf8");
  const latest = (readme.match(/^\| (v\d+\.\d+(?:\.\d+)?) \| \d/m) || [])[1];
  test("הגרסה בתחתית העמוד הראשי היא הגרסה האחרונה ב-README", () => {
    const shown = (HOME.match(/<bdi dir="ltr">(v[\d.]+) ·/) || [])[1];
    assert.ok(latest, "README versions table");
    assert.equal(shown, latest, `home page footer shows ${shown}, README latest is ${latest}`);
  });
  test("כל גרסה ב-README מתועדת גם ב-CHANGELOG", () => {
    const cl = fs.readFileSync(path.join(ROOT, "CHANGELOG.md"), "utf8");
    const vers = [...readme.matchAll(/^\| (v\d+\.\d+(?:\.\d+)?) \| \d/gm)].map((m) => m[1]);
    const missing = vers.filter((v) => !new RegExp(`${v.replace(/\./g, "\\.")}(?![\\d.])`).test(cl));
    assert.deepEqual(missing, []);
  });
  test("תיאור העמוד הראשי (למנועי חיפוש ושיתוף) מזכיר את כל הקורסים", () => {
    const d = (HOME.match(/<meta name="description" content="([^"]+)"/) || [])[1] || "";
    const names = { ctfl: /CTFL/, genai: /GenAI/, sql: /SQL/ };
    const missing = IDS.filter((id) => names[id] && !names[id].test(d));
    assert.deepEqual(missing, [], `description: ${d}`);
  });
});
