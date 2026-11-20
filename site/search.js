/* NGQA search – Hebrew-aware search over slide text (and CT-GenAI exercises).
   NGQASearch.open({courses:[{id,name}], course, chapter, scope, onPick}) shows the search panel. */
(function () {
  const FIN = { 'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ' };
  const BASE = { 'כ': '[כך]', 'מ': '[מם]', 'נ': '[נן]', 'פ': '[פף]', 'צ': '[צץ]' };
  const strip = s => String(s || '').replace(/[֑-ׇ]/g, '');           // niqqud / cantillation
  function tokens(q) { return strip(q).trim().split(/\s+/).filter(Boolean).slice(0, 6); }
  function tokRe(t) {
    let src = /^[A-Za-z]/.test(t) ? '(?<![A-Za-z0-9])' : '';   // English: match from the start of a word (RAG ≠ coverage)
    for (const ch of t) { const b = FIN[ch] || ch; src += BASE[b] || ch.replace(/[.*+?^${}()|[\]\\/-]/g, '\\$&'); }
    return src;
  }
  const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const cache = {};
  async function load(course) {
    if (!cache[course]) cache[course] = Promise.all([
      fetch(`/courses/${course}/search.json`, { credentials: 'same-origin' }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch(`/courses/${course}/decks.json`, { credentials: 'same-origin' }).then(r => r.ok ? r.json() : []).catch(() => [])
    ]).then(([idx, decks]) => ({ idx, decks })).catch(e => { delete cache[course]; throw e; });
    return cache[course];
  }
  function run(data, course, q, chapter) {
    const ts = tokens(q); if (!ts.length) return [];
    const res = ts.map(t => new RegExp(tokRe(t), 'gi'));
    const score = (t, x) => {
      let s = 0;
      for (const r of res) { r.lastIndex = 0; const inT = r.test(t); r.lastIndex = 0; const n = (x.match(r) || []).length; if (!inT && !n) return -1; s += (inT ? 20 : 0) + Math.min(n, 5); }
      return s;
    };
    const out = [];
    for (const s of data.idx.slides) {
      if (chapter && s.c !== chapter) continue;
      const sc = score(s.t, s.x); if (sc < 0) continue;
      out.push({ kind: 'slide', course, c: s.c, s: s.s, t: s.t, x: s.x, score: sc });
    }
    for (const e of data.idx.ex || []) {
      if (chapter && e.c !== chapter) continue;
      const sc = score(e.label + ' ' + e.t, e.x); if (sc < 0) continue;
      out.push({ kind: 'ex', course, c: e.c, id: e.id, label: e.label, t: e.t, x: e.x, score: sc + 1 });
    }
    out.sort((a, b) => b.score - a.score || a.c - b.c || (a.s || 0) - (b.s || 0));
    return out;
  }
  function snippet(x, q) {
    const ts = tokens(q); const all = new RegExp(ts.map(tokRe).join('|'), 'gi');
    const m = all.exec(x); all.lastIndex = 0;
    let a = 0, b = Math.min(x.length, 150);
    if (m) { a = Math.max(0, m.index - 60); b = Math.min(x.length, m.index + 100); }
    let s = x.slice(a, b);
    return (a ? '…' : '') + esc(s).replace(new RegExp(ts.map(t => tokRe(esc(t))).join('|'), 'gi'), '<mark>$&</mark>') + (b < x.length ? '…' : '');
  }
  const hl = (t, q) => { const ts = tokens(q); return ts.length ? esc(t).replace(new RegExp(ts.map(x => tokRe(esc(x))).join('|'), 'gi'), '<mark>$&</mark>') : esc(t); };

  let css = false, root, opts, timer = 0, lastFocus;
  function ensure() {
    if (root) return;
    if (!css) {
      css = true; const st = document.createElement('style');
      st.textContent = `
.ns-bg{position:fixed;inset:0;background:rgba(11,10,36,.6);z-index:300;display:none}
.ns{position:fixed;z-index:310;top:max(4vh,12px);left:50%;transform:translateX(-50%);width:min(760px,96vw);max-height:min(86vh,900px);display:none;flex-direction:column;background:var(--card,#fff);color:var(--ink,#121133);border-radius:18px;box-shadow:0 30px 80px rgba(0,0,0,.45);overflow:hidden;font-family:Heebo,Arial,sans-serif}
.ns.on,.ns-bg.on{display:flex}.ns-bg.on{display:block}
.ns-h{background:#121133;padding:12px;display:flex;gap:8px;align-items:center}
.ns-h input{flex:1;font:inherit;font-size:17px;padding:11px 14px;border-radius:12px;border:0;background:#fff;color:#121133;outline:none}
.ns-h input:focus{box-shadow:0 0 0 3px #14DACD}
.ns-x{width:44px;height:44px;border-radius:12px;border:1.5px solid #3b3a78;background:transparent;color:#fff;font-size:18px;cursor:pointer}
.ns-sc{display:flex;gap:6px;flex-wrap:wrap;padding:10px 14px;border-bottom:1px solid var(--line,#e1e3ef);align-items:center;font-size:14px}
.ns-sc button{font:inherit;font-size:13.5px;border-radius:999px;padding:5px 12px;border:1.5px solid var(--line,#e1e3ef);background:transparent;color:inherit;cursor:pointer}
.ns-sc button[aria-pressed=true]{background:#121133;border-color:#121133;color:#fff}
.ns-n{margin-inline-start:auto;color:var(--mute,#5d5c7c);font-size:13px}
.ns-l{overflow-y:auto;padding:8px;overscroll-behavior:contain}
.ns-r{display:flex;gap:12px;align-items:flex-start;width:100%;text-align:start;padding:10px;border:0;border-radius:12px;background:transparent;color:inherit;cursor:pointer;font:inherit;text-decoration:none}
.ns-r:hover,.ns-r:focus-visible{background:light-dark(#eef7f6,#1d1c4a);outline:none}
.ns-r .th{flex:none;width:132px;aspect-ratio:16/9;border-radius:8px;background-color:#e8eaf3;background-repeat:no-repeat;background-size:100% 600%;box-shadow:0 2px 8px rgba(18,17,51,.15)}
.ns-r .th.ex{display:grid;place-items:center;background:#F38911;color:#fff;font-weight:800;font-size:13px;text-align:center;padding:4px}
.ns-r b{display:block;font-size:15.5px;line-height:1.3}.ns-r small{display:block;color:#0E9F97;font-weight:700;font-size:12.5px;margin-bottom:2px}
.ns-r p{margin:4px 0 0;font-size:13.5px;color:var(--mute,#5d5c7c);line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.ns mark{background:#ffe08a;color:#121133;border-radius:3px;padding:0 1px}
.ns-e{padding:30px 16px;text-align:center;color:var(--mute,#5d5c7c)}
@media(max-width:600px){.ns{top:0;width:100vw;max-height:100svh;height:100svh;border-radius:0}.ns-r .th{width:96px}}`;
      document.head.appendChild(st);
    }
    root = document.createElement('div');
    root.innerHTML = `<div class="ns-bg" id="nsBg"></div>
<div class="ns" id="ns" role="dialog" aria-modal="true" aria-label="חיפוש">
  <div class="ns-h"><input id="nsQ" type="search" placeholder="חיפוש מושג או מילה…" aria-label="חיפוש" autocomplete="off" enterkeyhint="search"><button class="ns-x" id="nsX" type="button" aria-label="סגירת החיפוש">✕</button></div>
  <div class="ns-sc" id="nsSc"></div>
  <div class="ns-l" id="nsL" aria-live="polite"></div>
</div>`;
    document.body.appendChild(root);
    const $ = id => document.getElementById(id);
    $('nsX').onclick = close; $('nsBg').onclick = close;
    $('nsQ').oninput = () => { clearTimeout(timer); timer = setTimeout(render, 120); };
    $('ns').addEventListener('keydown', e => {
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key === 'Enter' && e.target.id === 'nsQ') { const f = $('nsL').querySelector('.ns-r'); if (f) f.click(); }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        const it = [...$('nsL').querySelectorAll('.ns-r')]; if (!it.length) return; e.preventDefault();
        let i = it.indexOf(document.activeElement); i = e.key === 'ArrowDown' ? Math.min(it.length - 1, i + 1) : i - 1;
        (i < 0 ? $('nsQ') : it[i]).focus();
      }
    });
    $('nsSc').onclick = e => { const b = e.target.closest('[data-sc]'); if (!b) return; opts.scope = b.dataset.sc; scopes(); render(); $('nsQ').focus(); };
    $('nsL').onclick = e => {
      const b = e.target.closest('.ns-r'); if (!b) return; e.preventDefault();
      const r = JSON.parse(b.dataset.r); try { localStorage.setItem('ngqa.lastq', $('nsQ').value); } catch (x) {}
      close(); opts.onPick(r);
    };
  }
  function scopes() {
    const $ = id => document.getElementById(id);
    const list = [];
    if (opts.chapter) list.push(['chapter', 'פרק ' + opts.chapter]);
    if (opts.course) list.push(['course', 'כל הקורס']);
    if (opts.courses.length > 1 || !opts.course) list.push(['all', 'כל הקורסים']);
    if (!list.some(x => x[0] === opts.scope)) opts.scope = list[0][0];
    $('nsSc').innerHTML = (list.length > 1 ? '<span>חיפוש ב:</span>' + list.map(([k, l]) => `<button type="button" data-sc="${k}" aria-pressed="${k === opts.scope}">${l}</button>`).join('') : '') + '<span class="ns-n" id="nsN"></span>';
  }
  async function render() {
    const $ = id => document.getElementById(id), q = $('nsQ').value.trim(), L = $('nsL');
    if (!q) { L.innerHTML = '<p class="ns-e">הקלידו מילה או מושג – למשל "בדיקות רגרסיה" או "Prompt".<br>החיפוש מוצא גם צורות עם ה/ו/ב/ל/מ/ש בתחילת המילה.</p>'; $('nsN').textContent = ''; return; }
    const cs = opts.scope === 'all' ? opts.courses : opts.courses.filter(c => c.id === opts.course);
    let res = [];
    try {
      for (const c of cs) {
        const d = await load(c.id);
        run(d, c.id, q, opts.scope === 'chapter' ? opts.chapter : 0).forEach(r => { r.cname = c.name; r.deck = d.decks.find(x => x.num === r.c); res.push(r); });
      }
    } catch (e) { L.innerHTML = '<p class="ns-e">לא הצלחתי לטעון את החיפוש. בדקו שאתם מחוברים ונסו שוב.</p>'; return; }
    if ($('nsQ').value.trim() !== q) return;
    res.sort((a, b) => b.score - a.score);
    $('nsN').textContent = res.length ? `${res.length} תוצאות` : '';
    if (!res.length) { L.innerHTML = `<p class="ns-e">לא נמצאו תוצאות ל-"${esc(q)}".</p>`; return; }
    L.innerHTML = res.slice(0, 80).map(r => {
      const where = (opts.scope === 'all' && opts.courses.length > 1 ? r.cname + ' · ' : '') + 'פרק ' + r.c + (r.kind === 'slide' ? ' · שקף ' + r.s : ' · תרגיל מעשי');
      let th = '<span class="th"></span>';
      if (r.kind === 'ex') th = `<span class="th ex">✎ ${esc(r.label)}</span>`;
      else if (r.deck && r.deck.slides[r.s - 1]) { const sl = r.deck.slides[r.s - 1]; th = `<span class="th" style="background-image:url('/courses/${r.course}/${sl.img}');background-position:0 ${sl.k * 100 / (r.deck.per - 1)}%"></span>`; }
      const data = esc(JSON.stringify({ kind: r.kind, course: r.course, c: r.c, s: r.s, id: r.id }));
      return `<a class="ns-r" href="#" data-r="${data}">${th}<span><small>${esc(where)}</small><b>${hl(r.kind === 'ex' ? r.label + ' · ' + r.t : r.t, q)}</b><p>${snippet(r.x, q)}</p></span></a>`;
    }).join('');
  }
  function open(o) {
    opts = Object.assign({ courses: [], scope: null, onPick: () => {} }, o); ensure();
    const $ = id => document.getElementById(id);
    lastFocus = document.activeElement;
    if (!opts.scope) opts.scope = opts.chapter ? 'chapter' : (opts.course ? 'course' : 'all');
    scopes(); $('ns').classList.add('on'); $('nsBg').classList.add('on'); document.body.style.overflow = 'hidden';
    const q = $('nsQ'); if (o.q != null) q.value = o.q; q.focus(); q.select(); render();
  }
  function close() {
    const n = document.getElementById('ns'); if (!n) return;
    n.classList.remove('on'); document.getElementById('nsBg').classList.remove('on'); document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  window.NGQASearch = { open, close, run, tokens, load, isOpen: () => !!document.querySelector('.ns.on') };
})();
