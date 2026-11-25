/* NGQA recorded lessons (v3.13): lessons tree + player, used by /courses/<c>/lessons/ and by the
   "שיעורים מוקלטים" tab of the chapter viewer. Data: /.netlify/functions/catalog?c=<course> (needs a session). */
(() => {
  const esc = t => String(t ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const cache = {};
  async function load(c) {
    if (cache[c]) return cache[c];
    cache[c] = (async () => {
      const A = window.NGQAAuth, s = A && await A.session();
      if (!s) throw new Error('יש להתחבר');
      const r = await fetch('/.netlify/functions/catalog?c=' + encodeURIComponent(c), { headers: { Authorization: 'Bearer ' + s.access_token } });
      let d = {}; try { d = await r.json(); } catch (e) {}
      if (!r.ok) throw new Error(d.error || ('שגיאה ' + r.status));
      return d;
    })();
    cache[c].catch(() => { delete cache[c]; });
    return cache[c];
  }
  const ytId = u => (u.match(/(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:watch\?v=|embed\/|shorts\/))([\w-]{11})/) || [])[1];
  const vimeoId = u => (u.match(/vimeo\.com\/(?:video\/)?(\d+)/) || [])[1];
  function player(l) {
    const box = t => `<div class="lp-msg">${t}</div>`;
    if (l.kind === 'locked') return box('🔒 השיעורים המוקלטים לא כלולים בגישה שלך. לפרטים — <a href="https://wa.me/972526718757" target="_blank" rel="noopener">וואטסאפ לניצן</a>.');
    if (l.kind === 'bunny') return box('הסרטון של השיעור הזה יחובר בקרוב.');
    if (l.kind !== 'url' || !l.src) return box('הסרטון של השיעור הזה יעלה בקרוב.');
    const y = ytId(l.src), v = vimeoId(l.src);
    if (y) return `<iframe src="https://www.youtube-nocookie.com/embed/${y}?rel=0" title="${esc(l.title)}" allow="encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>`;
    if (v) return `<iframe src="https://player.vimeo.com/video/${v}" title="${esc(l.title)}" allow="fullscreen; picture-in-picture" allowfullscreen></iframe>`;
    return `<video controls playsinline preload="metadata" controlslist="nodownload" src="${esc(l.src)}"></video>`;
  }
  const CSS = `.lsn{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:20px;align-items:start}
.lsn .main{min-width:0}.lsn .side{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:10px;position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}
.lp{aspect-ratio:16/9;background:#0b0a24;border-radius:16px;overflow:hidden;display:grid}
.lp iframe,.lp video{width:100%;height:100%;border:0;display:block;background:#000}
.lp-msg{display:grid;place-items:center;text-align:center;color:#d8d9f5;padding:24px;font-size:17px}.lp-msg a{color:#14DACD}
.ld{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 20px;margin-top:14px}
.ld h2{margin:0 0 4px;font-size:22px}.ld .meta{color:var(--mute);font-size:14.5px}.ld p{margin:10px 0 0;white-space:pre-line}
.ld .lk{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.ld .lk a{text-decoration:none;border:1px solid var(--line);border-radius:10px;padding:6px 12px;font-size:15px;font-weight:600;color:var(--ink)}
.ld .lk a:hover{border-color:var(--teal)}.ld .nav{display:flex;justify-content:space-between;gap:8px;margin-top:14px}
.ld .nav button{font:inherit;font-weight:700;border:0;border-radius:10px;padding:8px 14px;background:var(--navy);color:#fff;cursor:pointer}.ld .nav button[disabled]{opacity:.35;cursor:default}
.tch{margin-bottom:4px}.tch>button{font:inherit;width:100%;display:flex;justify-content:space-between;gap:8px;align-items:center;border:0;background:none;color:var(--ink);font-weight:700;padding:9px 10px;border-radius:10px;cursor:pointer;text-align:start}
.tch>button:hover{background:color-mix(in srgb,var(--teal) 12%,transparent)}.tch>button small{color:var(--mute);font-weight:500;white-space:nowrap}
.tch ol{list-style:none;margin:0;padding:0 0 6px}.tch.shut ol{display:none}
.tl{display:flex;gap:10px;align-items:center;padding:7px 10px 7px 8px;border-radius:10px;cursor:pointer;font-size:15px}
.tl:hover{background:color-mix(in srgb,var(--teal) 10%,transparent)}.tl.on{background:var(--navy);color:#fff}.tl.on .d{color:#c9cbf0}
.tl .n{flex:none;width:26px;height:26px;border-radius:50%;border:1.5px solid var(--line);display:grid;place-items:center;font-size:12.5px;font-weight:700}
.tl.on .n{border-color:var(--teal);color:var(--teal)}.tl .t{flex:1;line-height:1.35}.tl .d{flex:none;color:var(--mute);font-size:13px}
.tl .dr{font-size:11.5px;font-weight:700;border-radius:999px;padding:1px 7px;background:#fde7c7;color:#7a4a05}
.lempty{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px;text-align:center}.lempty h2{margin:0 0 6px}.lempty p{color:var(--mute);margin:6px auto;max-width:56ch}
@media(max-width:900px){.lsn{grid-template-columns:1fr}.lsn .side{position:static;max-height:none}}`;
  function style() { if (document.getElementById('lsnCss')) return; const s = document.createElement('style'); s.id = 'lsnCss'; s.textContent = CSS; document.head.appendChild(s); }
  /* el: container; o = { c, decks, only (chapter id or ''), base (path to the course page, e.g. '../' or ''), hash (true = keep #l=id in the URL) } */
  async function render(el, o) {
    style();
    el.innerHTML = '<p style="color:var(--mute);text-align:center">טוען שיעורים…</p>';
    let d;
    try { d = await load(o.c); } catch (e) { el.innerHTML = `<div class="lempty"><h2>לא הצלחנו לטעון את השיעורים</h2><p>${esc(e.message)}</p></div>`; return; }
    const titles = {}; (o.decks || []).forEach(x => { titles[x.id] = (x.lab || ('פרק ' + x.num)) + ' · ' + x.title; });
    const order = (o.decks || []).map(x => x.id).concat(Object.keys(d.ch).filter(k => !(o.decks || []).some(x => x.id === k)));
    const chs = order.filter(k => d.ch[k] && (!o.only || k === o.only));
    const flat = []; chs.forEach(k => d.ch[k].forEach((l, i) => flat.push({ ...l, ch: k, i })));
    if (!flat.length) {
      el.innerHTML = `<div class="lempty"><h2>${o.only ? 'עוד אין שיעורים מוקלטים לפרק הזה' : 'השיעורים המוקלטים יעלו כאן בקרוב'}</h2><p>כשהשיעורים יעלו, הם יופיעו כאן לפי פרקים, עם נגן וקישור לשקפים ולתרגילים של כל שיעור.</p>${o.only ? `<p><a href="${o.base}lessons/">לכל השיעורים המוקלטים</a></p>` : ''}</div>`;
      return;
    }
    const dur = l => l.dur ? l.dur + ' דק׳' : '';
    const sum = k => { const ls = d.ch[k]; let s = 0; ls.forEach(l => { const [m, x] = (l.dur || '0:0').split(':').map(Number); s += m * 60 + x; }); return ls.length + ' שיעורים' + (s ? ' · ' + Math.round(s / 60) + ' דק׳' : ''); };
    el.innerHTML = `<div class="lsn"><div class="main"><div class="lp" id="lsP"></div><div class="ld" id="lsD"></div></div><nav class="side" aria-label="עץ השיעורים">${chs.map(k => `<div class="tch"><button type="button" aria-expanded="true"><span>${esc(titles[k] || k)}</span><small>${sum(k)}</small></button><ol>${d.ch[k].map((l, i) => `<li class="tl" tabindex="0" data-id="${esc(l.id)}"><span class="n">${i + 1}</span><span class="t">${esc(l.title)}${l.status !== 'pub' ? ' <span class="dr">טיוטה</span>' : ''}</span><span class="d">${esc(l.dur || '')}</span></li>`).join('')}</ol></div>`).join('')}</nav></div>`;
    el.querySelectorAll('.tch>button').forEach(b => b.onclick = () => { const p = b.parentElement; p.classList.toggle('shut'); b.setAttribute('aria-expanded', !p.classList.contains('shut')); });
    const show = (id, push) => {
      const k = Math.max(0, flat.findIndex(x => x.id === id)), l = flat[k];
      el.querySelectorAll('.tl').forEach(x => x.classList.toggle('on', x.dataset.id === l.id));
      el.querySelector('#lsP').innerHTML = player(l);
      const num = (o.decks || []).find(x => x.id === l.ch), chn = num ? num.num : (l.ch.match(/\d+/) || [''])[0];
      const lk = [];
      if (l.sf) lk.push(`<a href="${o.base}#${l.ch}/${l.sf}">לשקפים ${l.sf}${l.st && l.st > l.sf ? '–' + l.st : ''}</a>`);
      else lk.push(`<a href="${o.base}#${l.ch}">למצגת של הפרק</a>`);
      if (l.ex) lk.push(`<a href="${o.base}#${l.ch}/ex">לתרגילים של הפרק</a>`);
      (l.files || []).forEach(f => lk.push(`<a href="${esc(f.u)}" target="_blank" rel="noopener">📎 ${esc(f.n)}</a>`));
      el.querySelector('#lsD').innerHTML = `<h2>${esc(l.title)}</h2><div class="meta">${esc(titles[l.ch] || ('פרק ' + chn))}${l.dur ? ' · ' + dur(l) : ''}${l.status !== 'pub' ? ' · טיוטה (רק מנהל רואה)' : ''}</div>${l.desc ? `<p>${esc(l.desc)}</p>` : ''}<div class="lk">${lk.join('')}</div><div class="nav"><button type="button" data-go="${k - 1}" ${k ? '' : 'disabled'}>→ השיעור הקודם</button><button type="button" data-go="${k + 1}" ${k < flat.length - 1 ? '' : 'disabled'}>השיעור הבא ←</button></div>`;
      el.querySelectorAll('#lsD [data-go]').forEach(b => b.onclick = () => show(flat[+b.dataset.go].id, true));
      if (o.hash && push) history.replaceState(null, '', '#l=' + l.id);
      if (push) el.querySelector('#lsP').scrollIntoView({ block: 'nearest' });
    };
    el.querySelectorAll('.tl').forEach(x => { x.onclick = () => show(x.dataset.id, true); x.onkeydown = e => { if (e.key === 'Enter') x.click(); }; });
    const h = o.hash && (location.hash.match(/^#l=([a-z0-9]+)/) || [])[1];
    show(h || flat[0].id, false);
  }
  window.NGQALessons = { load, render };
})();
