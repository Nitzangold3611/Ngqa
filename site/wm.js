/* NGQA – personal watermark on PDF downloads and printing (v3.8)
   Every PDF link on the course pages is downloaded through the browser, stamped on each page
   with the full name of the signed-in user (pdf-lib, the name drawn as an image so Hebrew renders correctly),
   and then saved / opened. Printing a course page shows the same name across the page. */
(function () {
  if (!location.pathname.startsWith('/courses/')) return;
  let lib = null, nameP = null;
  const loadLib = () => lib || (lib = new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = '/vendor/pdf-lib.min.js';
    s.onload = () => res(window.PDFLib); s.onerror = () => { lib = null; rej(new Error('pdf-lib')); };
    document.head.appendChild(s);
  }));
  const who = () => nameP || (nameP = (async () => {
    try { const i = NGQAAuth.info(await NGQAAuth.session()); return (i && (i.name || i.email)) || ''; } catch (e) { return ''; }
  })());

  function stampPng(name) {
    const c = document.createElement('canvas'), x = c.getContext('2d'), F = 'bold 96px Arial, "Segoe UI", sans-serif';
    x.font = F; const w = Math.ceil(x.measureText(name).width) + 60;
    c.width = w; c.height = 150;
    x.font = F; x.direction = 'rtl'; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillStyle = '#5A6275'; x.fillText(name, w / 2, 78);
    return new Promise(r => c.toBlob(b => b.arrayBuffer().then(r), 'image/png'));
  }
  async function stamp(url, name) {
    const [P, buf, png] = await Promise.all([
      loadLib(),
      fetch(url, { credentials: 'same-origin' }).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); }),
      stampPng(name)]);
    const doc = await P.PDFDocument.load(buf, { ignoreEncryption: true });
    const img = await doc.embedPng(png);
    for (const pg of doc.getPages()) {
      const { width: W, height: H } = pg.getSize();
      const a = Math.atan2(H, W), len = Math.hypot(W, H) * 0.62;
      const iw = Math.min(len, img.width * 0.75 * (len / 900)), ih = iw * img.height / img.width;
      const cx = W / 2, cy = H / 2, c = Math.cos(a), s = Math.sin(a);
      pg.drawImage(img, { x: cx - (iw / 2 * c - ih / 2 * s), y: cy - (iw / 2 * s + ih / 2 * c), width: iw, height: ih,
                          rotate: P.radians(a), opacity: 0.15 });
    }
    doc.setProducer('NGQA'); 
    return new Blob([await doc.save()], { type: 'application/pdf' });
  }

  let toastEl;
  function toast(msg, ms) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.style.cssText = 'position:fixed;bottom:22px;left:50%;transform:translateX(-50%);background:#1B2A4A;color:#fff;padding:10px 18px;border-radius:10px;font:15px Arial,sans-serif;z-index:99999;box-shadow:0 6px 20px rgba(0,0,0,.25);direction:rtl';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg; toastEl.style.display = 'block';
    clearTimeout(toastEl._t); if (ms) toastEl._t = setTimeout(() => { toastEl.style.display = 'none'; }, ms);
  }

  document.addEventListener('click', async e => {
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a || e.defaultPrevented) return;
    const href = a.getAttribute('href') || '';
    if (!/\.pdf([?#]|$)/i.test(href) || /^(https?:)?\/\//i.test(href) && !href.includes(location.host)) return;
    e.preventDefault(); e.stopPropagation();
    if (a.dataset.wmBusy) return;
    const dl = a.hasAttribute('download'), tab = !dl && (a.target === '_blank' || e.ctrlKey || e.metaKey);
    const win = tab ? window.open('', '_blank') : null;
    a.dataset.wmBusy = '1'; toast('מכין את הקובץ…');
    try {
      const name = await who();
      const blob = name ? await stamp(a.href, name) : await (await fetch(a.href, { credentials: 'same-origin' })).blob();
      const u = URL.createObjectURL(blob);
      if (win) win.location = u;
      else if (dl) { const t = document.createElement('a'); t.href = u; t.download = a.getAttribute('download') || href.split('/').pop(); document.body.appendChild(t); t.click(); t.remove(); }
      else location.href = u;
      setTimeout(() => URL.revokeObjectURL(u), 120000);
      toast('הקובץ מוכן', 1800);
    } catch (err) {
      if (win) win.close();
      toast('לא הצלחנו להכין את הקובץ. נסו שוב.', 4000);
    } finally { delete a.dataset.wmBusy; }
  }, true);

  /* printing a course page: the name across every printed page */
  who().then(name => {
    if (!name) return;
    const st = document.createElement('style');
    st.textContent = '#ngqa-wm{display:none}@media print{#ngqa-wm{display:flex;position:fixed;inset:0;z-index:2147483647;pointer-events:none;align-items:center;justify-content:center}#ngqa-wm span{transform:rotate(-35deg);font:bold 64px Arial,sans-serif;color:rgba(90,98,117,.16);white-space:nowrap}}';
    const d = document.createElement('div'); d.id = 'ngqa-wm'; const sp = document.createElement('span'); sp.textContent = name; d.appendChild(sp);
    const add = () => { document.head.appendChild(st); document.body.appendChild(d); };
    document.body ? add() : document.addEventListener('DOMContentLoaded', add);
  });
})();
