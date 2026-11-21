/* NGQA – WhatsApp contact button (all pages). Questions to Nitzan, Sun–Thu 09:00–18:00. */
(function () {
  if (window.__ngqaWa) return; window.__ngqaWa = 1;
  var PHONE = '972526718757';
  var MSG = 'שלום ניצן, יש לי שאלה לגבי הקורס';
  var ICON = '<svg viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M16 3C8.8 3 3 8.7 3 15.8c0 2.5.7 4.9 2 7L3 29l6.4-2c2 1.1 4.3 1.7 6.6 1.7 7.2 0 13-5.7 13-12.8S23.2 3 16 3zm0 23.4c-2.1 0-4.1-.6-5.9-1.7l-.4-.3-3.8 1.2 1.2-3.7-.3-.4c-1.2-1.8-1.8-3.8-1.8-5.9C5 10 9.9 5.2 16 5.2S27 10 27 15.8s-4.9 10.6-11 10.6zm6-7.9c-.3-.2-2-1-2.3-1.1-.3-.1-.5-.2-.8.2-.2.3-.9 1.1-1.1 1.3-.2.2-.4.3-.7.1-.3-.2-1.4-.5-2.7-1.7-1-.9-1.7-2-1.9-2.3-.2-.3 0-.5.1-.7l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.6l-1.1-2.6c-.3-.7-.6-.6-.8-.6h-.7c-.2 0-.6.1-.9.4-.3.3-1.2 1.2-1.2 2.9s1.2 3.4 1.4 3.6c.2.2 2.4 3.7 5.9 5.2.8.4 1.5.6 2 .7.8.3 1.6.2 2.2.1.7-.1 2-.8 2.3-1.6.3-.8.3-1.5.2-1.6-.1-.2-.3-.3-.7-.4z"/></svg>';
  var css = '.ngwa{position:fixed;left:16px;bottom:16px;z-index:60;font-family:Heebo,Arial,sans-serif;direction:rtl}' +
    '.ngwa-b{width:54px;height:54px;border-radius:50%;border:0;background:#25D366;color:#fff;display:grid;place-items:center;box-shadow:0 6px 18px rgba(0,0,0,.25);cursor:pointer;padding:0}' +
    '.ngwa-b svg{width:30px;height:30px}.ngwa-b:hover{filter:brightness(1.06)}.ngwa-b:focus-visible{outline:3px solid #F38911;outline-offset:2px}' +
    '.ngwa-c{position:absolute;left:0;bottom:66px;width:min(290px,calc(100vw - 32px));background:#fff;color:#121133;border-radius:14px;box-shadow:0 12px 34px rgba(18,17,51,.28);padding:14px 16px;display:none;text-align:right}' +
    '.ngwa.open .ngwa-c{display:block}.ngwa-c b{display:block;font-size:16px;margin-bottom:4px}' +
    '.ngwa-c p{margin:0 0 10px;font-size:14px;line-height:1.5;color:#3d3c5c}.ngwa-h{display:inline-block;background:#eafbfa;color:#0E9F97;border-radius:8px;padding:2px 8px;font-weight:700;font-size:13px;margin-top:4px}' +
    '.ngwa-go{display:flex;align-items:center;justify-content:center;gap:8px;min-height:44px;border-radius:10px;background:#25D366;color:#fff;font-weight:700;text-decoration:none;font-size:15px}' +
    '.ngwa-go svg{width:20px;height:20px}.ngwa-x{position:absolute;top:6px;left:8px;border:0;background:none;font-size:18px;color:#8a89a6;cursor:pointer;width:32px;height:32px}' +
    'body.pfs-on .ngwa,body.m-play .ngwa{display:none}:fullscreen .ngwa{display:none}' +
    '@media print{.ngwa{display:none}}' +
    '@media(max-width:700px){.ngwa{left:12px;bottom:12px}.ngwa-b{width:48px;height:48px}.ngwa-b svg{width:27px;height:27px}body.feed .ngwa{bottom:70px}}';
  function init() {
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var w = document.createElement('div'); w.className = 'ngwa';
    w.innerHTML = '<div class="ngwa-c" role="dialog" aria-label="שאלות בוואטסאפ"><button class="ngwa-x" type="button" aria-label="סגירה">✕</button>' +
      '<b>יש שאלה?</b><p>אפשר לכתוב לניצן בוואטסאפ.<br><span class="ngwa-h">פניות בימים א׳–ה׳, 09:00–18:00</span></p>' +
      '<a class="ngwa-go" target="_blank" rel="noopener" href="https://wa.me/' + PHONE + '?text=' + encodeURIComponent(MSG) + '">' + ICON + 'פתיחת וואטסאפ</a></div>' +
      '<button class="ngwa-b" type="button" aria-label="שאלות בוואטסאפ לניצן (א׳–ה׳, 09:00–18:00)" title="שאלות בוואטסאפ · א׳–ה׳ 09:00–18:00" aria-expanded="false">' + ICON + '</button>';
    document.body.appendChild(w);
    var b = w.querySelector('.ngwa-b');
    function set(on) { w.classList.toggle('open', on); b.setAttribute('aria-expanded', on); }
    b.onclick = function (e) { e.stopPropagation(); set(!w.classList.contains('open')); };
    w.querySelector('.ngwa-x').onclick = function () { set(false); };
    w.querySelector('.ngwa-go').onclick = function () { set(false); };
    document.addEventListener('click', function (e) { if (!w.contains(e.target)) set(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
