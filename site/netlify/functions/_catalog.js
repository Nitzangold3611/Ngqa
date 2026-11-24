// Lessons tree (v3.13): Blobs key "catalog-<course>" = { ch: { <chapterId>: [lesson, …] }, at, by }
// lesson = { id, title, desc, kind: 'none'|'url'|'bunny', src, dur, sf, st, ex, files: [{ n, u }], status: 'draft'|'pub' }
const S = (v, n) => String(v == null ? '' : v).trim().slice(0, n);
const okUrl = u => /^https:\/\/[^\s"'<>]+$/.test(u);
function cleanLesson(x) {
  const kind = ['none', 'url', 'bunny'].includes(x && x.kind) ? x.kind : 'none';
  let src = S(x && x.src, 300);
  if (kind === 'url' && !okUrl(src)) src = '';
  if (kind === 'bunny' && !/^[a-zA-Z0-9-]{6,64}$/.test(src)) src = '';
  const n = v => { const k = parseInt(v, 10); return k > 0 && k < 1000 ? k : 0; };
  const files = (Array.isArray(x && x.files) ? x.files : []).slice(0, 10).map(f => ({ n: S(f && f.n, 80), u: S(f && f.u, 300) })).filter(f => f.n && okUrl(f.u));
  const id = String((x && x.id) || '');
  return { id: /^[a-z0-9]{4,16}$/.test(id) && id !== 'undefined' ? id : 'l' + Math.random().toString(36).slice(2, 9),
    title: S(x && x.title, 120) || 'שיעור ללא שם', desc: S(x && x.desc, 600), kind, src,
    dur: /^\d{1,3}:\d{2}$/.test(S(x && x.dur, 7)) ? S(x.dur, 7) : '', sf: n(x && x.sf), st: n(x && x.st), ex: !!(x && x.ex),
    files, status: x && x.status === 'pub' ? 'pub' : 'draft' };
}
function cleanCatalog(ch) {
  const o = {};
  for (const k of Object.keys(ch || {}).slice(0, 40)) { if (!/^ch\d{1,2}$/.test(k)) continue; const a = Array.isArray(ch[k]) ? ch[k].slice(0, 60).map(cleanLesson) : []; if (a.length) o[k] = a; }
  return o;
}
module.exports = { cleanLesson, cleanCatalog };
