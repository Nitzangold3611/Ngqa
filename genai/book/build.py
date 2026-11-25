#!/usr/bin/env python3
"""Build the CT-GenAI summary book: src/ch*.md -> site/courses/genai/book/index.html (+ book.html for the PDF).
Run make_pdf.py afterwards to render site/courses/genai/pdf/NGQA-CT-GenAI-book.pdf with Chrome."""
import re, html, pathlib, markdown

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT.parents[1] / 'site' / 'courses' / 'genai'
OUT = SITE / 'book'
VER, DATE = '1.1', '23.11.2026'
PDF = '../pdf/NGQA-CT-GenAI-book.pdf'

def render(md_text, n):
    md_text = md_text.replace('<div class="plain">', '<div class="plain" markdown="1">')
    h = markdown.markdown(md_text, extensions=['tables', 'md_in_html', 'sane_lists'])
    toc, c = [], [0]
    def hid(m):
        lvl, body = int(m.group(1)), m.group(2)
        c[0] += 1; i = f'c{n}-{c[0]}'
        txt = re.sub('<[^>]+>', '', body)
        if lvl <= 3: toc.append((lvl, i, txt))
        return f'<h{lvl} id="{i}">{body}</h{lvl}>'
    h = re.sub(r'<h([1-4])>(.*?)</h\1>', hid, h)
    # the end-of-chapter blocks get their own look
    h = h.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
    return h, toc

chapters = []
for n in range(1, 6):
    body, toc = render((ROOT / 'src' / f'ch{n}.md').read_text(encoding='utf-8'), n)
    chapters.append((n, body, toc))

def toc_html():
    out = []
    for n, _, toc in chapters:
        items = ''.join(f'<li class="l{l}"><a href="#{i}">{html.escape(t)}</a></li>' for l, i, t in toc
                        if l < 3 or re.match(r'^\d', t))
        out.append(f'<ol>{items}</ol>')
    return ''.join(out)

CSS = r'''
:root{color-scheme:light dark;--navy:#121133;--teal:#14DACD;--teal-d:#0E9F97;--orange:#F38911;
--bg:light-dark(#f4f6fb,#0b0a24);--card:light-dark(#fff,#18173f);--ink:light-dark(#121133,#eef0ff);--mute:light-dark(#5d5c7c,#a9a8cf);--line:light-dark(#e1e3ef,#2a2960);--soft:light-dark(#eef9f8,#14304a)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.75 Heebo,Arial,sans-serif;overflow-x:clip}
a{color:inherit}
.bar{position:sticky;top:0;z-index:20;background:var(--navy);color:#fff;display:flex;gap:10px;align-items:center;padding:10px max(3vw,14px);flex-wrap:wrap}
.bar b{flex:1;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:600px){.bar{gap:6px;padding:8px 10px}.bar b{font-size:15px}.bar a,.bar button{padding:5px 10px!important;font-size:13.5px!important}}
.bar a,.bar button{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:7px 14px;font:inherit;font-size:15px;text-decoration:none;cursor:pointer;white-space:nowrap}
.bar a:hover,.bar button:hover{background:rgba(255,255,255,.2)}
.bar .pri{background:var(--orange);border-color:var(--orange)}
.lay{display:grid;grid-template-columns:320px minmax(0,1fr);gap:36px;max-width:1560px;margin:auto;padding:28px max(3vw,14px)}
@media(max-width:900px){.lay{grid-template-columns:1fr}.side{position:sticky!important;top:58px;z-index:10;max-height:70vh!important}}
.side{position:sticky;top:70px;align-self:start;max-height:calc(100vh - 90px);overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px}
.side summary{font-weight:800;font-size:16px;cursor:pointer;margin-bottom:8px}.side details:not([open]) summary{margin:0}
.side ol{list-style:none;margin:0 0 10px;padding:0}
.side li a{display:block;text-decoration:none;padding:3px 6px;border-radius:6px;font-size:14px;line-height:1.4}
.side li a:hover,.side li a.on{background:var(--soft);color:var(--teal-d)}
.side li.l1 a{font-weight:800;font-size:15px;margin-top:6px}
.side li.l3 a{padding-inline-start:20px;color:var(--mute)}
article{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:clamp(18px,4vw,48px)}
.cover{background:var(--navy);color:#fff;border-radius:18px;padding:clamp(28px,6vw,64px);margin-bottom:28px;position:relative;overflow:hidden}
.cover img{width:150px;display:block;margin-bottom:18px}
.cover h1{font-size:clamp(30px,5vw,46px);line-height:1.15;margin:0 0 10px;color:#fff;border:0;padding:0}
.cover .tag{color:var(--teal);font-weight:700}
.cover p{color:#c9cbf0;margin:6px 0;max-width:60ch}
.cover .ed{margin-top:18px;font-size:14px;color:#a9abda}
.how{border:1px dashed var(--line);border-radius:14px;padding:14px 18px;margin-bottom:28px;font-size:15.5px}
.how b{color:var(--orange)}
section.ch{margin-bottom:56px}
h1{font-size:30px;line-height:1.25;margin:0 0 4px;color:var(--ink);border-bottom:4px solid var(--teal);padding-bottom:10px}
p.en{margin:6px 0 18px;color:var(--mute);direction:ltr;text-align:right;font-style:italic}
h2{font-size:24px;margin:36px 0 10px;color:var(--teal-d)}
h3{font-size:20px;margin:26px 0 8px}
h4{font-size:17.5px;margin:20px 0 6px;color:var(--mute)}
p,li{margin:8px 0}
ul,ol{padding-inline-start:24px}
strong{color:light-dark(#0c0b33,#fff)}
code{direction:ltr;unicode-bidi:isolate;background:var(--soft);padding:1px 6px;border-radius:5px;font-size:.9em}
.tw{overflow-x:auto;margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:15.5px;line-height:1.5}
th{background:var(--navy);color:#fff;text-align:start;padding:9px 12px;font-weight:700}
td{border-bottom:1px solid var(--line);padding:8px 12px;vertical-align:top}
tr:nth-child(even) td{background:light-dark(#f8f9fd,#1d1c48)}
.exam{background:light-dark(#fff4e6,#3a2a12);border-inline-start:5px solid var(--orange);border-radius:10px;padding:10px 16px;margin:14px 0;font-weight:500}
.exam::before{content:"דגש לבחינה · ";font-weight:800;color:var(--orange)}
.plain{background:var(--soft);border-inline-start:5px solid var(--teal);border-radius:12px;padding:6px 20px;font-size:17.5px}
h2[id]+.plain{margin-top:6px}
footer{text-align:center;color:var(--mute);font-size:14px;padding:22px}
footer .ver{display:block;margin-top:4px}
@media print{
  @page{size:A4;margin:16mm 15mm 18mm}
  :root{color-scheme:light}
  body{background:#fff;color:#121133;font-size:11.5pt;line-height:1.6;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .bar,.side,.how,footer{display:none!important}
  .lay{display:block;padding:0;max-width:none}
  article{border:0;padding:0;border-radius:0;background:#fff}
  .cover{border-radius:0;margin:0 0 0;min-height:250mm;display:flex;flex-direction:column;justify-content:center;break-after:page}
  .ptoc{display:block!important;break-after:page}
  section.ch{break-before:page;margin:0}
  h1,h2,h3,h4{break-after:avoid}
  table,.exam,.plain,tr{break-inside:avoid}
  .tw{overflow:visible}
  a{text-decoration:none}
}
.ptoc{display:none}
.ptoc h2{margin-top:0}
.ptoc ol{list-style:none;padding:0;margin:0 0 8px}
.ptoc li{margin:2px 0;font-size:11pt}
.ptoc li.l1{font-weight:800;margin-top:10px;font-size:12.5pt}
.ptoc li.l3{padding-inline-start:18px;color:#5d5c7c}
.ptoc a{text-decoration:none}
'''

JS = r'''<script>
document.getElementById('prt').onclick=()=>window.print();
if(/[?&]print=1/.test(location.search))(document.fonts?document.fonts.ready:Promise.resolve()).then(()=>setTimeout(()=>window.print(),600));
const side=document.querySelector('.side'),det=side.querySelector('details');if(matchMedia('(max-width:900px)').matches)det.open=false;
const fixTop=()=>{side.style.top=matchMedia('(max-width:900px)').matches?(document.querySelector('.bar').offsetHeight+6)+'px':''};fixTop();addEventListener('resize',fixTop);
side.addEventListener('click',e=>{if(e.target.closest('a')&&matchMedia('(max-width:900px)').matches)det.open=false});
const links=[...document.querySelectorAll('.side a')],map=new Map(links.map(a=>[a.getAttribute('href').slice(1),a]));
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(l=>l.classList.remove('on'));const a=map.get(e.target.id);if(a){a.classList.add('on');if(side.scrollHeight>side.clientHeight+4&&getComputedStyle(side).position==='sticky'){const y=a.offsetTop;if(y<side.scrollTop||y>side.scrollTop+side.clientHeight-30)side.scrollTop=y-side.clientHeight/2}}}})},{rootMargin:'-80px 0px -70% 0px'});
document.querySelectorAll('article h1[id],article h2[id],article h3[id]').forEach(h=>{if(map.has(h.id))io.observe(h)});
</script>'''

def page(for_pdf=False):
    head_auth = '' if for_pdf else '''<script src="/auth.js"></script>
<script>document.documentElement.style.visibility='hidden';NGQAAuth.guard('genai').then(ok=>{if(ok)document.documentElement.style.visibility=''}).catch(()=>{document.documentElement.style.visibility=''});</script>
<script>try{const t=localStorage.getItem('ngqa-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>'''
    secs = ''.join(f'<section class="ch" id="ch{n}">{b}</section>' for n, b, _ in chapters)
    return f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
{head_auth}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ספר מסכם · CT-GenAI | NGQA</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="../favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="bar"><b>ספר מסכם · CT-GenAI</b>
  <a href="../">חזרה לקורס</a>
  <button type="button" id="prt">הדפסה</button>
  <a class="pri" href="{PDF}" download="NGQA-CT-GenAI-book.pdf">הורדת PDF</a>
</div>
<div class="lay">
<nav class="side" aria-label="תוכן העניינים"><details open><summary>תוכן העניינים</summary>{toc_html()}</details></nav>
<article>
<div class="cover"><img src="../logo.png" alt="NGQA">
<span class="tag">CT-GenAI · ISTQB Certified Tester – Testing with Generative AI</span>
<h1>ספר מסכם — בינה מלאכותית יוצרת בבדיקות תוכנה</h1>
<p>סיכום מלא של כל חמשת פרקי הקורס לפי פרקים ותתי-פרקים, עם דגשים לבחינה, מושגים והסברים בסוף כל פרק, וסיכום במילים פשוטות.</p>
<p class="ed">מהדורה {VER} · {DATE} · NGQA ייעוץ והדרכה בבדיקות תוכנה</p></div>
<div class="how">איך להשתמש בספר: כל פרק בנוי כמו המצגות — תתי-פרקים, טבלאות ודוגמאות. <b>דגש לבחינה</b> מסמן נקודות שחוזרות בשאלות, ובסוף כל פרק יש <b>דגשים לבחינה</b>, טבלת <b>מושגים והסברים</b> ו<b>סיכום במילים פשוטות</b>.</div>
<div class="ptoc"><h2>תוכן העניינים</h2>{toc_html()}</div>
{secs}
</article>
</div>
<footer>כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה · החומר לשימוש אישי של משתתפי הקורס בלבד<span class="ver">ספר מסכם <bdi dir="ltr">v{VER} · {DATE}</bdi></span></footer>
{JS}
</body>
</html>
'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(page(), encoding='utf-8')
(ROOT / 'build').mkdir(exist_ok=True)
(ROOT / 'build' / 'book.html').write_text(page(True).replace('../logo.png', str(SITE / 'logo.png')), encoding='utf-8')
print('ok', sum(len(t) for _, _, t in chapters), 'toc entries')
