#!/usr/bin/env python3
"""Build site/courses/sql from the generated decks + exercise data.
usage: build_site.py VERSION DATE"""
import json, glob, os, re, zipfile, subprocess, shutil, sys, html
from PIL import Image

V = sys.argv[1] if len(sys.argv) > 1 else '1.0'
DATE = sys.argv[2] if len(sys.argv) > 2 else ''
SQ = '/home/claude/sql'
REPO = '/home/claude/ngqa'
OUT = REPO + '/site/courses/sql'
GEN = REPO + '/site/courses/genai'
S = glob.glob('/root/.claude/skills/synced/*/pptx')[0]
UP = '/mnt/user-data/uploads/sql'
CH = {1: 'מבוא ל-SQL', 2: 'שאילתות', 3: 'אופרטורים', 4: 'פונקציות מוכללות', 5: 'הוראות בשאילתות',
      6: 'צירוף טבלאות – JOIN', 7: 'שאילתות משנה', 8: 'טיפול בנתונים', 9: 'פקודות DDL', 10: 'Views',
      11: 'Stored Procedures'}
SUB = {1: 'Introduction & Getting Started', 2: 'SELECT … FROM', 3: 'Operators', 4: 'Built-in Functions',
       5: 'Query Clauses', 6: 'JOIN', 7: 'Subqueries', 8: 'Data Manipulation (DML)', 9: 'Data Definition Language',
       10: 'Views', 11: 'Stored Procedures'}
EXCH = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7}
EXS = json.load(open(SQ + '/ex/exercises.json'))
SUM = json.load(open(SQ + '/sum/summary.json'))
esc = html.escape

for d in ('sp', 'img', 'pdf', 'dl'):
    shutil.rmtree(f'{OUT}/{d}', ignore_errors=True)
    os.makedirs(f'{OUT}/{d}')
for f in ('logo.png', 'favicon.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png'):
    shutil.copy(f'{GEN}/{f}', OUT)
BACK = {'x': 86.12, 'y': 94.67, 'w': 11.62, 'h': 4.0}
N = 6
decks = []
for n in range(1, 12):
    pp = f'{SQ}/out/ch{n}.pptx'
    z = zipfile.ZipFile(pp)
    site = json.load(open(f'{SQ}/out/ch{n}.site.json'))
    pres = z.read('ppt/presentation.xml').decode()
    rels = z.read('ppt/_rels/presentation.xml.rels').decode()
    m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1)
         for r in re.findall(r'<Relationship [^>]*>', rels)}
    order = [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]
    out = subprocess.run(['python3', S + '/scripts/slide_text.py', pp], capture_output=True, text=True).stdout
    parts = re.split(r'<!-- Slide number: (\d+) -->', out)[1:]
    texts = {int(a): b.split('### Notes:')[0] for a, b in zip(parts[0::2], parts[1::2])}
    tmp = f'/tmp/sqhr{n}'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=92', '-scale-to-x', '1600', '-scale-to-y', '-1',
                    f'{SQ}/out/ch{n}.pdf', tmp + '/s'], check=True, stderr=subprocess.DEVNULL)
    fs = sorted(glob.glob(tmp + '/s-*.jpg'))
    assert len(fs) == len(order), (n, len(fs), len(order))
    exlinks = {}
    for eid, boxes in site.get('ex', {}).items():
        for b in boxes:
            exlinks.setdefault(b['slide'], []).append({'x': b['x'], 'y': b['y'], 'w': b['w'], 'h': b['h'], 'ex': eid})
    slides, ims = [], []
    for i, (f, target) in enumerate(zip(fs, order), 1):
        im = Image.open(f).convert('RGB')
        w = 1440
        h = round(im.height * w / im.width)
        ims.append(im.resize((w, h), Image.LANCZOS))
        lines = [l.strip('# |').strip() for l in texts.get(i, '').splitlines() if l.strip() and not l.strip().startswith('![')]
        lay = z.read(f'ppt/slides/_rels/{os.path.basename(target)}.rels').decode()
        content = 'slideLayout2' in lay
        links = []
        if i == 2:
            links += [dict(l) for l in site['toc_links']]
        if content and i != 2:
            links.append(dict(BACK, slide=2))
        links += exlinks.get(i, [])
        s = {'title': (lines[0] if lines else '')[:120], 'text': ' '.join(lines)[:700]}
        if links:
            s['links'] = links
        slides.append(s)
    for g in range(0, len(ims), N):
        c = Image.new('RGB', (w, h * N), 'white')
        for k, im in enumerate(ims[g:g + N]):
            c.paste(im, (0, k * h))
        name = f'sp/ch{n}_{g // N:02d}.jpg'
        c.save(f'{OUT}/{name}', quality=80, optimize=True, progressive=True)
        for k in range(len(ims[g:g + N])):
            slides[g + k]['img'] = name + '?v=' + V
            slides[g + k]['k'] = k
    ims[0].resize((960, round(960 * h / w)), Image.LANCZOS).save(f'{OUT}/img/ch{n}.jpg', quality=82)
    shutil.copy(f'{SQ}/out/ch{n}.pdf', f'{OUT}/pdf/NGQA-SQL-ch{n}.pdf')
    exs = []
    for eid, ch in EXCH.items():
        if ch != n:
            continue
        e = EXS[eid]
        sl = sorted(b['slide'] for b in site.get('ex', {}).get(eid, []))
        exs.append({'id': eid, 'label': f'תרגיל {eid}', 'title': e['title'], 'n': len(e['items']), 'slides': sl,
                    'items': e['items']})
    decks.append({'id': f'ch{n}', 'num': n, 'title': CH[n], 'sub': SUB[n], 'cover': f'img/ch{n}.jpg?v={V}',
                  'ratio': f'{w}/{h}', 'per': N, 'toc': site['toc'], 'ex': exs, 'slides': slides})
json.dump(decks, open(f'{OUT}/decks.json', 'w'), ensure_ascii=False)

# ---------------------------------------------------------------- downloads
shutil.copy(f'{UP}/../68f6f513-northwind_2.bak' if os.path.exists(f'{UP}/../68f6f513-northwind_2.bak')
            else '/mnt/user-data/uploads/68f6f513-northwind_2.bak', f'{OUT}/dl/northwind.bak')
for f in ('college_setup.sql', 'party_setup.sql'):
    shutil.copy(f'{SQ}/sum/dl/{f}', f'{OUT}/dl/{f}')
im = Image.open(f'{UP}/חומר עזר/Northwind diagram.png').convert('RGB')
im.save(f'{OUT}/dl/northwind-diagram.png', optimize=True)

# ---------------------------------------------------------------- index (from the CT-GenAI page)
src = open(f'{GEN}/index.html', encoding='utf-8').read()
rep = [
    ("NGQAAuth.guard('genai')", "NGQAAuth.guard('sql')"),
    ("const COURSE='genai';", "const COURSE='sql';"),
    ('<title>NGQA · CT-GenAI</title>', '<title>NGQA · SQL לבודקי תוכנה</title>'),
    ("document.title='NGQA · CT-GenAI'", "document.title='NGQA · SQL לבודקי תוכנה'"),
    ('const CHAPTERS=[1,2,3,4,5].map(n=>({num:n}));', 'const CHAPTERS=[1,2,3,4,5,6,7,8,9,10,11].map(n=>({num:n}));'),
    ("pdf/NGQA-CT-GenAI-ch${cur.num}.pdf", "pdf/NGQA-SQL-ch${cur.num}.pdf"),
    ("`NGQA CT-GenAI פרק ${cur.num}.pdf`", "`NGQA SQL פרק ${cur.num}.pdf`"),
    ('${e.pages} עמודים', '${e.n} שאלות'),
    ('אין תרגילים מעשיים בפרק זה.<br>התרגילים מתחילים בפרק 2.',
     'אין דף תרגילים לפרק זה.<br>לתרגול נוסף: התרגילים המסכמים בעמוד הבית של הקורס.'),
    ("${d.ex.length?` · ${d.ex.length} תרגילים`:''}", "${d.ex.length?` · ${d.ex[0].n} שאלות תרגול`:''}"),
]
for a, b in rep:
    assert a in src, a
    src = src.replace(a, b)
src = re.sub(r'<meta name="description" content="[^"]*">',
             '<meta name="description" content="מצגות, תרגילים וחומרי עזר לקורס SQL לבודקי תוכנה של NGQA ייעוץ והדרכה בבדיקות תוכנה.">', src)
src = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="NGQA · SQL לבודקי תוכנה">', src)
src = re.sub(r'<meta property="og:description" content="[^"]*">',
             '<meta property="og:description" content="כל פרקי קורס SQL, התרגילים וחומרי העזר במקום אחד.">', src)
src = re.sub(r'<span class="tag">[^<]*</span>', '<span class="tag">SQL · Microsoft SQL Server · T-SQL</span>', src, 1)
src = re.sub(r'<h1>[^<]*</h1>', '<h1>SQL לבודקי תוכנה</h1>', src, 1)
src = re.sub(r'(<div class="in">\s*<div>.*?<h1>.*?</h1>\s*)<p>[^<]*</p>',
             r'\1<p>כל פרקי הקורס, התרגילים וחומרי העזר במקום אחד. בוחרים פרק, עוברים על השקופיות, ומשקף של תרגיל קופצים ישר לשאלות ולפתרונות.</p>',
             src, 1, flags=re.S)
src = re.sub(r'<span class="ver">גרסה <bdi dir="ltr">[^<]*</bdi></span>',
             f'<span class="ver">גרסה <bdi dir="ltr">v{V} · {DATE}</bdi></span>', src)
# home boxes: reference material + summary exercises
boxes = '''<div class="xbx">
      <a class="xb" href="ref/"><span class="xi" aria-hidden="true">🧰</span><span><b>חומר עזר</b><small>מדריך התקנה (SQL Server 2025 + SSMS 22), שחזור Northwind, סרטון הדגמה, תרשים המסד ודף פקודות</small></span></a>
      <a class="xb" href="summary/"><span class="xi" aria-hidden="true">🏁</span><span><b>תרגילים מסכמים</b><small>College · Party · Human Resources, עם קובצי הקמה ופתרונות</small></span></a>
    </div>
    <div class="hsr">'''
src = src.replace('<div class="hsr">', boxes, 1)
css = '''.exttl .lab{direction:rtl}
.xbx{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:0 0 30px}
.xb{display:flex;gap:14px;align-items:center;background:var(--navy);color:#fff;border-radius:16px;padding:18px 20px;text-decoration:none;border-inline-start:6px solid var(--teal);transition:transform .2s}
.xb+.xb{border-inline-start-color:var(--orange)}.xb:hover{transform:translateY(-2px)}
.xb .xi{font-size:30px;flex:none}.xb b{display:block;font-size:20px}.xb small{color:#c9cbf0;font-size:14px;line-height:1.4;display:block}
@media(max-width:700px){.xbx{grid-template-columns:1fr}}
.qa{list-style:none;margin:0;padding:0;display:grid;gap:12px;counter-reset:q}
.qa>li{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;counter-increment:q;border-inline-start:5px solid var(--teal)}
.qa .sec{counter-increment:none;margin:12px 2px 0;color:var(--teal-d);font-weight:800;font-size:15px;list-style:none;background:none;border:0;padding:0}
.qa .q{display:flex;gap:10px;font-weight:600}.qa .q::before{content:counter(q);flex:none;width:28px;height:28px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center;font-size:13px;font-weight:800}
.qa details{margin-top:10px}.qa summary{cursor:pointer;display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 14px;border-radius:10px;background:var(--orange);color:#fff;font-weight:700;list-style:none}
.qa summary::-webkit-details-marker{display:none}.qa details[open] summary{background:var(--teal-d)}
.qa details[open] summary .s1,.qa details:not([open]) summary .s2{display:none}
pre.sql{position:relative;direction:ltr;text-align:left;background:#121133;color:#fff;border-radius:12px;padding:14px 16px;margin:10px 0 0;overflow-x:auto;font:14.5px/1.55 Consolas,"Cascadia Mono",Menlo,monospace;white-space:pre}
pre.sql .k{color:#14DACD;font-weight:700}pre.sql .s{color:#F7B267}pre.sql .n{color:#B5E8A0}pre.sql .c{color:#8A93A6;font-style:italic}pre.sql .f{color:#FFD580}
.fixn{margin-top:8px;font-size:13.5px;color:var(--mute);background:light-dark(#fff6ea,#2a2340);border-radius:10px;padding:8px 12px;border-inline-start:4px solid var(--orange)}
.cpy{position:absolute;top:8px;right:8px;font-size:12px;border:1px solid #3b3a78;background:transparent;color:#c9cbf0;border-radius:8px;padding:2px 8px}
'''
src = src.replace('/* ---- tabs & exercises (CT-GenAI) ---- */', css + '/* ---- tabs & exercises ---- */', 1)
# exercise view: questions + hidden solutions
new_show = r'''function showEx(e){const d=cur,k=d.ex.indexOf(e),b=backSlide(e),pv=d.ex[k-1],nx=d.ex[k+1];
  document.title=`${e.label} · ${e.title} | NGQA`;let last='';
  const qs=e.items.map(it=>{let h='';if(it.sec&&it.sec!==last){last=it.sec;h+=`<li class="sec">${esc(it.sec)}</li>`}
    return h+`<li><div class="q">${esc(it.q)}</div><details><summary><span class="s1">הצג פתרון</span><span class="s2">הסתר פתרון</span></summary><pre class="sql"><button class="cpy" type="button">העתקה</button>${hlSql(it.a)}</pre>${it.fixed?`<div class="fixn">הערה: ${esc(it.fixed)}</div>`:''}</details></li>`}).join('');
  $('exview').innerHTML=`<div class="exhead">${b?`<a class="back" href="#${d.id}/${b}">→ חזרה לשקף ${b}</a>`:`<a class="back" href="#${d.id}">→ חזרה למצגת</a>`}<a class="dl" href="#${d.id}/ex">כל התרגילים</a></div>
    <div class="exttl"><span class="lab">${e.label} · מסד הנתונים Northwind</span><h2>${e.title}</h2></div>
    <ol class="qa">${qs}</ol>
    <div class="exnav">${nx?`<a href="#${d.id}/ex/${nx.id}">→ ${nx.label}</a>`:'<span></span>'}${pv?`<a href="#${d.id}/ex/${pv.id}">${pv.label} ←</a>`:''}</div>
    ${b?`<div class="exhead" style="position:static;justify-content:center"><a class="back" href="#${d.id}/${b}">→ חזרה לשקף ${b}</a></div>`:''}`}
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const SQLKW=new Set('SELECT FROM WHERE ORDER BY GROUP HAVING INSERT INTO VALUES UPDATE SET DELETE CREATE ALTER DROP TABLE VIEW PROCEDURE AND OR NOT IN LIKE BETWEEN IS NULL AS ON JOIN INNER LEFT RIGHT FULL OUTER CROSS UNION ALL DISTINCT TOP ASC DESC EXISTS ANY CASE WHEN THEN ELSE END BEGIN DECLARE EXEC RETURN IF COLUMN VARCHAR INT'.split(' '));
function hlSql(a){return a.split('\n').map(l=>{const m=l.match(/^(.*?)(--.*)?$/);let c=m[2]||'';
  let t=esc(m[1]).replace(/('[^']*'?)|(\b\d+(?:\.\d+)?\b)|(\b[A-Za-z_]\w*\b)(?=\s*\()|(\b[A-Za-z_]+\b)/g,(x,s,n,f,w)=>s?`<span class="s">${s}</span>`:n?`<span class="n">${n}</span>`:f?(SQLKW.has(f.toUpperCase())?`<span class="k">${f}</span>`:`<span class="f">${f}</span>`):SQLKW.has(w.toUpperCase())?`<span class="k">${w}</span>`:w);
  return t+(c?`<span class="c">${esc(c)}</span>`:'')}).join('\n')}
document.addEventListener('click',ev=>{const b=ev.target.closest('.cpy');if(!b)return;const p=b.parentElement.cloneNode(true);p.querySelector('.cpy').remove();
  navigator.clipboard&&navigator.clipboard.writeText(p.textContent).then(()=>{b.textContent='הועתק ✓';setTimeout(()=>b.textContent='העתקה',1500)})});'''
a = src.index('function showEx(e){')
b2 = src.index("$('tabS').onclick")
src = src[:a] + new_show + '\n' + src[b2:]
# exercise list: drop the "lvl" chip and pdf references
src = src.replace("${e.lvl?`<span class=\"chip lvl\">${e.lvl}</span>`:''}", '')
open(f'{OUT}/index.html', 'w', encoding='utf-8').write(src)

# ---------------------------------------------------------------- shared page shell for ref/ and summary/
HEAD = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<script src="/auth.js"></script>
<script>document.documentElement.style.visibility='hidden';NGQAAuth.guard('sql').then(ok=>{if(ok)document.documentElement.style.visibility=''}).catch(()=>{document.documentElement.style.visibility=''});</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__T__ · SQL לבודקי תוכנה | NGQA</title>
<meta name="theme-color" content="#121133">
<script src="/wa.js" defer></script>
<link rel="icon" type="image/png" href="../favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
:root{color-scheme:light dark;--navy:#121133;--teal:#14DACD;--teal-d:#0E9F97;--orange:#F38911;
--bg:light-dark(#f4f6fb,#0b0a24);--card:light-dark(#fff,#18173f);--ink:light-dark(#121133,#eef0ff);--mute:light-dark(#5d5c7c,#a9a8cf);--line:light-dark(#e1e3ef,#2a2960)}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Heebo,Arial,sans-serif}
a{color:var(--teal-d)}
.hero{background:var(--navy);color:#fff;padding:clamp(22px,4vw,46px) max(5vw,16px)}
.hero .in{max-width:1000px;margin:auto;display:flex;gap:20px;align-items:center;justify-content:space-between}
.hero h1{margin:6px 0 6px;font-size:clamp(28px,4.4vw,44px);line-height:1.1}
.hero p{margin:0;color:#c9cbf0;max-width:60ch}
.hero img{width:clamp(110px,16vw,180px)}
.allc{display:inline-block;color:#c9cbf0;text-decoration:none;font-size:14px;font-weight:600;border:1px solid #3b3a78;border-radius:999px;padding:4px 12px}
.allc:hover{color:var(--teal);border-color:var(--teal)}
main{max-width:1000px;margin:auto;padding:26px max(4vw,14px) 50px}
nav.toc{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
nav.toc a{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:6px 14px;text-decoration:none;color:var(--ink);font-weight:600;font-size:14px}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px clamp(16px,3vw,28px);margin:0 0 20px;scroll-margin-top:16px}
section>h2{margin:0 0 4px;font-size:23px}
section>.sub{color:var(--mute);margin:0 0 14px}
.steps{counter-reset:s;list-style:none;padding:0;margin:0;display:grid;gap:10px}
.steps>li{counter-increment:s;display:flex;gap:12px;align-items:flex-start}
.steps>li::before{content:counter(s);flex:none;width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center;font-weight:800;font-size:14px;margin-top:1px}
.steps b{color:var(--ink)}
code,kbd{direction:ltr;unicode-bidi:isolate;background:light-dark(#eef0f8,#26255a);border-radius:6px;padding:1px 6px;font:14px Consolas,Menlo,monospace}
.tip{background:light-dark(#eafbfa,#13324a);border-inline-start:4px solid var(--teal);border-radius:10px;padding:10px 14px;margin:14px 0 0}
.warn{background:light-dark(#fff6ea,#2a2340);border-inline-start:4px solid var(--orange);border-radius:10px;padding:10px 14px;margin:14px 0 0}
.btn{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 18px;border-radius:10px;background:var(--orange);color:#fff;font-weight:700;text-decoration:none;margin:6px 0 0 8px}
.btn.alt{background:var(--navy)}
.vid{position:relative;aspect-ratio:16/9;border-radius:14px;overflow:hidden;background:#000;margin-top:12px}
.vid iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
img.dia{width:100%;height:auto;border-radius:12px;border:1px solid var(--line);background:#fff;margin-top:10px}
table.cmd{width:100%;border-collapse:collapse;font-size:14.5px}
table.cmd th{background:var(--navy);color:#fff;padding:8px 10px;text-align:start}
table.cmd td{border-bottom:1px solid var(--line);padding:8px 10px;vertical-align:top}
table.cmd td:first-child{font-weight:700;white-space:nowrap}
table.cmd td.x{direction:ltr;text-align:left;font:13.5px/1.5 Consolas,Menlo,monospace;white-space:pre-wrap}
table.cmd tr.g td{background:light-dark(#eafbfa,#1d1c4a);color:var(--teal-d);font-weight:800}
.tbls{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0}.tbls code{font-size:13px}
.qa{list-style:none;margin:16px 0 0;padding:0;display:grid;gap:12px;counter-reset:q}
.qa>li{background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:12px 14px;counter-increment:q}
.qa .q{display:flex;gap:10px;font-weight:600}.qa .q::before{content:counter(q);flex:none;width:28px;height:28px;border-radius:50%;background:var(--navy);color:#fff;display:grid;place-items:center;font-size:13px;font-weight:800}
.qa details{margin-top:8px}.qa summary{cursor:pointer;display:inline-flex;align-items:center;min-height:38px;padding:0 14px;border-radius:10px;background:var(--orange);color:#fff;font-weight:700;list-style:none}
.qa summary::-webkit-details-marker{display:none}.qa details[open] summary{background:var(--teal-d)}
.qa details[open] summary .s1,.qa details:not([open]) summary .s2{display:none}
pre.sql{direction:ltr;text-align:left;background:#121133;color:#fff;border-radius:12px;padding:12px 14px;margin:10px 0 0;overflow-x:auto;font:14px/1.55 Consolas,Menlo,monospace;white-space:pre}
pre.sql .k{color:#14DACD;font-weight:700}pre.sql .s{color:#F7B267}pre.sql .n{color:#B5E8A0}pre.sql .c{color:#8A93A6;font-style:italic}pre.sql .f{color:#FFD580}
.fixn{margin-top:8px;font-size:13.5px;color:var(--mute);background:light-dark(#fff6ea,#2a2340);border-radius:10px;padding:8px 12px;border-inline-start:4px solid var(--orange)}
.credit{color:var(--mute);font-size:14px;margin:4px 0 0}
footer{text-align:center;color:var(--mute);font-size:13px;padding:24px 10px 34px}
footer .ver{display:block;margin-top:4px}
@media(max-width:600px){.hero img{display:none}table.cmd td:first-child{white-space:normal}}
</style>
</head>
<body>
<header class="hero"><div class="in"><div><a class="allc" href="../">→ לקורס SQL</a><h1>__T__</h1><p>__P__</p></div><img src="../logo.png" alt="NGQA Software Testing Services"></div></header>
<main>
'''
FOOT = f'''</main>
<footer>כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה<span class="ver">גרסה <bdi dir="ltr">v{V} · {DATE}</bdi></span></footer>
<script>
const SQLKW=new Set('SELECT FROM WHERE ORDER BY GROUP HAVING INSERT INTO VALUES UPDATE SET DELETE CREATE ALTER DROP TABLE VIEW PROCEDURE AND OR NOT IN LIKE BETWEEN IS NULL AS ON JOIN INNER LEFT RIGHT FULL OUTER CROSS UNION ALL DISTINCT TOP ASC DESC EXISTS CASE WHEN THEN ELSE END BEGIN DECLARE EXEC RETURN IF COLUMN VARCHAR INT'.split(' '));
const E=s=>s.replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));
document.querySelectorAll('pre.sql').forEach(p=>{{p.innerHTML=p.textContent.split('\\n').map(l=>{{const m=l.match(/^(.*?)(--.*)?$/);
  const t=E(m[1]).replace(/('[^']*'?)|(\\b\\d+(?:\\.\\d+)?\\b)|(\\b[A-Za-z_]\\w*\\b)(?=\\s*\\()|(\\b[A-Za-z_]+\\b)/g,(x,s,n,f,w)=>s?`<span class="s">${{s}}</span>`:n?`<span class="n">${{n}}</span>`:f?(SQLKW.has(f.toUpperCase())?`<span class="k">${{f}}</span>`:`<span class="f">${{f}}</span>`):SQLKW.has(w.toUpperCase())?`<span class="k">${{w}}</span>`:w);
  return t+(m[2]?`<span class="c">${{E(m[2])}}</span>`:'')}}).join('\\n')}});
</script>
</body>
</html>
'''


def page(path, title, lead, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(HEAD.replace('__T__', title).replace('__P__', lead) + body + FOOT)


def qa(items):
    out = []
    for it in items:
        fx = f'<div class="fixn">הערה: {esc(it["fixed"])}</div>' if it.get('fixed') else ''
        out.append(f'<li><div class="q">{esc(it["q"])}</div><details><summary><span class="s1">הצג פתרון</span>'
                   f'<span class="s2">הסתר פתרון</span></summary><pre class="sql">{esc(it["a"])}</pre>{fx}</details></li>')
    return '<ol class="qa">' + ''.join(out) + '</ol>'


# summary page
body = '<nav class="toc">' + ''.join(f'<a href="#{s["id"]}">{esc(s["title"])}</a>' for s in SUM) + '</nav>'
for s in SUM:
    dl = f'<a class="btn" href="../dl/{s["setup"]}" download>⬇ קובץ הקמה ({s["setup"]})</a>' if s['setup'] else ''
    tb = '<div class="tbls">' + ''.join(f'<code>{esc(t)}</code>' for t in s['tables']) + '</div>'
    cr = f'<p class="credit">{esc(s["credit"])}</p>' if s.get('credit') else ''
    body += (f'<section id="{s["id"]}"><h2>{esc(s["title"])}</h2><p class="sub">{esc(s["sub"])} · {len(s["items"])} שאלות</p>'
             f'<p>{esc(s["about"])}</p>{tb}{dl}{cr}{qa(s["items"])}</section>')
page(f'{OUT}/summary/index.html', 'תרגילים מסכמים',
     'שלושה תרגילים שמסכמים את כל הקורס. מקימים את הטבלאות מקובץ ההקמה, פותרים לבד, ורק אז פותחים את הפתרון.', body)

# reference page
CMD = [
    ('g', 'שליפה'),
    ('SELECT … FROM', 'אילו עמודות לשלוף ומאיזו טבלה', 'SELECT FirstName, LastName\nFROM Employees;'),
    ('WHERE', 'סינון שורות לפי תנאי', "WHERE Country = 'USA'"),
    ('DISTINCT', 'ביטול שורות כפולות בתוצאה', 'SELECT DISTINCT Country FROM Customers;'),
    ('AS', 'כינוי (Alias) לעמודה או לטבלה', 'SELECT UnitPrice * 0.9 AS SalePrice'),
    ('TOP', 'רק N השורות הראשונות', 'SELECT TOP 5 * FROM Products ORDER BY UnitPrice DESC;'),
    ('ORDER BY', 'מיון: ASC עולה (ברירת מחדל), DESC יורד', 'ORDER BY Country, City DESC'),
    ('g', 'אופרטורים'),
    ('= <> < > <= >=', 'השוואה (<> וגם != = שונה מ-)', 'WHERE UnitPrice >= 20'),
    ('AND / OR / NOT', 'שילוב תנאים; AND קודם ל-OR, לכן כדאי סוגריים', "WHERE (City = 'London' OR City = 'Paris') AND Fax IS NOT NULL"),
    ('BETWEEN', 'טווח, כולל הקצוות', 'WHERE UnitPrice BETWEEN 10 AND 50'),
    ('IN', 'אחד מתוך רשימה (קיצור ל-OR)', "WHERE Country IN ('UK', 'France')"),
    ('LIKE', "% = כל רצף תווים, _ = תו אחד", "WHERE CompanyName LIKE 'A%'"),
    ('IS NULL / IS NOT NULL', 'בדיקת ערך חסר (לא = NULL!)', 'WHERE Region IS NULL'),
    ('g', 'פונקציות'),
    ('COUNT / SUM / AVG / MIN / MAX', 'פונקציות צבירה', 'SELECT COUNT(*), AVG(UnitPrice) FROM Products;'),
    ('UPPER / LOWER / LEN', 'אותיות גדולות/קטנות, אורך מחרוזת', 'SELECT UPPER(LastName), LEN(LastName)'),
    ('SUBSTRING / LEFT / RIGHT', 'חלק ממחרוזת', 'SUBSTRING(City, 1, 4)'),
    ('REPLACE / LTRIM / RTRIM', 'החלפה וניקוי רווחים', "REPLACE(City, 'London', 'Londinium')"),
    ('ROUND / CEILING / FLOOR', 'עיגול מספרים', 'ROUND(UnitPrice, 2)'),
    ('GETDATE / DATEADD / DATEDIFF', 'תאריך נוכחי, הוספה והפרש', 'DATEDIFF(DAY, OrderDate, ShippedDate)'),
    ('YEAR / MONTH / DAY / DATENAME', 'חלקי תאריך', 'YEAR(OrderDate), DATENAME(MONTH, OrderDate)'),
    ('ISNULL / CAST / CONVERT', 'ערך חלופי ל-NULL, המרת טיפוסים', "ISNULL(Fax, N'אין'), CAST(UnitPrice AS INT)"),
    ('g', 'קיבוץ'),
    ('GROUP BY', 'קיבוץ שורות לפי ערך משותף', 'SELECT Country, COUNT(*)\nFROM Customers\nGROUP BY Country;'),
    ('HAVING', 'תנאי על קבוצות (אחרי GROUP BY)', 'HAVING COUNT(*) > 5'),
    ('g', 'צירוף טבלאות'),
    ('INNER JOIN', 'רק שורות עם התאמה בשתי הטבלאות', 'SELECT p.ProductName, c.CategoryName\nFROM Products p\nINNER JOIN Categories c ON p.CategoryID = c.CategoryID;'),
    ('LEFT / RIGHT JOIN', 'כל השורות מטבלה אחת, ומהשנייה רק מה שמתאים', 'FROM Customers c\nLEFT JOIN Orders o ON c.CustomerID = o.CustomerID'),
    ('FULL / CROSS JOIN', 'כל השורות משתי הטבלאות / מכפלה קרטזית', 'FROM Customers c FULL JOIN Orders o ON …'),
    ('UNION', 'איחוד תוצאות של שתי שאילתות (UNION ALL משאיר כפולים)', 'SELECT City FROM Customers\nUNION\nSELECT City FROM Suppliers;'),
    ('תת-שאילתה', 'שאילתה בתוך שאילתה', 'WHERE UnitPrice > (SELECT AVG(UnitPrice) FROM Products)'),
    ('g', 'שינוי נתונים ומבנה'),
    ('INSERT', 'הוספת שורה', "INSERT INTO Shippers (CompanyName, Phone)\nVALUES ('Fast Ship', '03-5551234');"),
    ('UPDATE', 'עדכון שורות (בלי WHERE – כל הטבלה!)', "UPDATE Products SET UnitPrice = 20\nWHERE ProductID = 1;"),
    ('DELETE', 'מחיקת שורות (בלי WHERE – כל הטבלה!)', 'DELETE FROM Shippers WHERE ShipperID = 4;'),
    ('CREATE / ALTER / DROP TABLE', 'יצירה, שינוי ומחיקה של טבלה', 'ALTER TABLE Student ADD Email varchar(50);\nALTER TABLE Student DROP COLUMN Email;'),
    ('VIEW', 'שאילתה שמורה שמתנהגת כמו טבלה', 'CREATE VIEW UK_Customers AS\nSELECT * FROM Customers WHERE Country = \'UK\';'),
    ('PROCEDURE', 'קוד שמור שמריצים בשם', 'CREATE PROCEDURE GetEmployees AS\nSELECT * FROM Employees;\nEXEC GetEmployees;'),
]
rows = ''
for r in CMD:
    if r[0] == 'g':
        rows += f'<tr class="g"><td colspan="3">{esc(r[1])}</td></tr>'
    else:
        rows += f'<tr><td><bdi dir="ltr">{esc(r[0])}</bdi></td><td>{esc(r[1])}</td><td class="x">{esc(r[2])}</td></tr>'
body = f'''<nav class="toc"><a href="#install">התקנת SQL Server</a><a href="#ssms">התקנת SSMS</a><a href="#restore">שחזור Northwind</a><a href="#video">סרטון הדגמה</a><a href="#diagram">תרשים Northwind</a><a href="#cmd">דף פקודות</a></nav>
<section id="install"><h2>1. התקנת SQL Server 2025 Express</h2><p class="sub">שרת מסד הנתונים · גרסה חינמית · Windows 10/11</p>
<ol class="steps">
<li><span>נכנסים לדף ההורדות של מיקרוסופט: <a href="https://www.microsoft.com/sql-server/sql-server-downloads" target="_blank" rel="noopener">microsoft.com/sql-server/sql-server-downloads</a>, ובאזור <b>Express</b> לוחצים <b>Download now</b>.</span></li>
<li><span>מריצים את הקובץ שירד (<code>SQL2025-SSEI-Expr.exe</code>) ובוחרים בסוג ההתקנה <b>Basic</b>.</span></li>
<li><span>מאשרים את תנאי הרישיון (<b>Accept</b>), משאירים את תיקיית ההתקנה המוצעת ולוחצים <b>Install</b>.</span></li>
<li><span>ממתינים לסיום ההורדה וההתקנה (כמה דקות). במסך הסיום מופיע שם השרת, בדרך כלל <code>localhost\\SQLEXPRESS</code>. כדאי לרשום אותו.</span></li>
</ol>
<div class="tip">במסך הסיום יש כפתור <b>Install SSMS</b>. הוא פותח את דף ההורדה של כלי הניהול, השלב הבא.</div>
</section>
<section id="ssms"><h2>2. התקנת SQL Server Management Studio 22</h2><p class="sub">הכלי הגרפי שבו כותבים ומריצים שאילתות</p>
<ol class="steps">
<li><span>נכנסים ל-<a href="https://learn.microsoft.com/ssms/install/install" target="_blank" rel="noopener">learn.microsoft.com/ssms/install/install</a> ומורידים את <b>SSMS 22</b> (הקובץ <code>vs_SSMS.exe</code>).</span></li>
<li><span>מריצים את הקובץ. נפתח <b>Visual Studio Installer</b>; משאירים את ברירת המחדל ולוחצים <b>Install</b>.</span></li>
<li><span>בסיום פותחים את SSMS מתפריט Start (מקלידים <kbd>SSMS</kbd>). בפתיחה הראשונה אפשר לדלג על ההתחברות לחשבון מיקרוסופט.</span></li>
<li><span>בחלון <b>Connect to Server</b>: Server type = <b>Database Engine</b>, Server name = <code>localhost\\SQLEXPRESS</code>, Authentication = <b>Windows Authentication</b>. אם מופיעה שגיאת תעודה, מסמנים <b>Trust Server Certificate</b>. לוחצים <b>Connect</b>.</span></li>
</ol>
<div class="tip">מומלץ להצמיד את SSMS לשורת המשימות: נשתמש בו בכל שיעור.</div>
</section>
<section id="restore"><h2>3. שחזור מסד הנתונים Northwind</h2><p class="sub">מסד הנתונים שאיתו עובדים בכל הקורס</p>
<a class="btn" href="../dl/northwind.bak" download>⬇ הורדת northwind.bak</a>
<ol class="steps" style="margin-top:14px">
<li><span>מעתיקים את הקובץ לתיקייה פשוטה, למשל <code>C:\\SQLBackups</code> (תיקיית ההורדות לפעמים חסומה לשרת).</span></li>
<li><span>ב-SSMS, בחלון <b>Object Explorer</b>: קליק ימני על <b>Databases</b> ← <b>Restore Database…</b></span></li>
<li><span>תחת <b>Source</b> מסמנים <b>Device</b>, לוחצים על <b>…</b> ← <b>Add</b> ← בוחרים את <code>northwind.bak</code> ← <b>OK</b>.</span></li>
<li><span>בעמוד <b>Files</b> (בצד שמאל של החלון) מסמנים <b>Relocate all files to folder</b>. הקובץ נוצר במחשב אחר, ובלי הסימון הזה השחזור נכשל על נתיב שלא קיים.</span></li>
<li><span>לוחצים <b>OK</b>. אחרי ההודעה <i>Database 'Northwind' restored successfully</i> מרעננים (F5) את Databases ומופיע המסד <b>Northwind</b>.</span></li>
<li><span>בודקים: <b>New Query</b>, בוחרים את Northwind ברשימת המסדים, ומריצים <code>SELECT * FROM Customers;</code></span></li>
</ol>
<div class="warn">אם מתקבלת שגיאה על גרסה: קובץ גיבוי אפשר לשחזר רק לגרסת שרת שווה או חדשה יותר. עם SQL Server 2025 אין בעיה.</div>
</section>
<section id="video"><h2>סרטון הדגמה: שחזור קובץ גיבוי</h2><p class="sub">אותם שלבים, צעד אחר צעד</p>
<div class="vid"><iframe src="https://www.youtube-nocookie.com/embed/wVFGJqigGk0" title="שחזור קובץ גיבוי ב-SQL Server" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>
<p><a href="https://www.youtube.com/watch?v=wVFGJqigGk0" target="_blank" rel="noopener">לפתיחה ב-YouTube</a></p>
</section>
<section id="diagram"><h2>תרשים מסד הנתונים Northwind</h2><p class="sub">הטבלאות והקשרים ביניהן</p>
<a class="btn alt" href="../dl/northwind-diagram.png" download>⬇ הורדת התרשים</a>
<img class="dia" src="../dl/northwind-diagram.png" alt="תרשים מסד הנתונים Northwind" loading="lazy">
</section>
<section id="cmd"><h2>דף פקודות SQL</h2><p class="sub">ריכוז הפקודות של הקורס בתחביר SQL Server (T-SQL)</p>
<div style="overflow-x:auto"><table class="cmd"><thead><tr><th>פקודה</th><th>מה היא עושה</th><th>דוגמה</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="tip">פונקציות מהדף הישן כמו <code>FIRST()</code>, <code>LAST()</code>, <code>UCASE()</code> ו-<code>NOW()</code> לא קיימות ב-SQL Server. במקומן: <code>TOP</code> עם <code>ORDER BY</code>, <code>UPPER()</code> ו-<code>GETDATE()</code>.</div>
</section>
'''
page(f'{OUT}/ref/index.html', 'חומר עזר',
     'כל מה שצריך כדי להתחיל: התקנת הסביבה, שחזור מסד הנתונים Northwind, תרשים המסד ודף פקודות.', body)
print(sum(len(d['slides']) for d in decks), 'slides,', sum(len(d['ex']) for d in decks), 'exercise pages')
