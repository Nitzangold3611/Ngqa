#!/usr/bin/env python3
"""Generic NGQA chapter-review quiz builder.
Usage: python3 quiz.py <course-id> <LABEL> <questions.py> [VER] [DATE] -> site/courses/<id>/quiz/index.html
questions.py: TITLE, CHAPTERS = [(n, title, [(q, [4 options], correct_index, [4 whys]), ...]), ...]
Option order is shuffled deterministically so the correct answers are spread evenly over א–ד."""
import json, pathlib, sys, random, importlib.util
CID, LABEL, SRC = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
VER = sys.argv[4] if len(sys.argv) > 4 else '1.0'
DATE = sys.argv[5] if len(sys.argv) > 5 else '23.11.2026'
_spec = importlib.util.spec_from_file_location('q', SRC); _m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
OUT = pathlib.Path(__file__).resolve().parents[2] / 'site' / 'courses' / CID / 'quiz'

chs = []
for n, title, qs in _m.CHAPTERS:
    rnd = random.Random(f'{CID}-{n}')
    # target positions: a balanced, shuffled sequence 0..3
    pos = [i % 4 for i in range(len(qs))]; rnd.shuffle(pos)
    out = []
    for (q, opts, ans, whys), p in zip(qs, pos):
        assert len(opts) == 4 and len(whys) == 4 and 0 <= ans < 4, q
        others = [i for i in range(4) if i != ans]; rnd.shuffle(others)
        order = others[:p] + [ans] + others[p:]
        out.append(dict(q=q, o=[opts[i] for i in order], w=[whys[i] for i in order], a=p))
    chs.append(dict(n=n, t=title, qs=out))

CSS = r'''
:root{color-scheme:light dark;--navy:#121133;--teal:#14DACD;--teal-d:#0E9F97;--orange:#F38911;--red:#e5484d;--green:#1fb57a;
--bg:light-dark(#f4f6fb,#0b0a24);--card:light-dark(#fff,#18173f);--ink:light-dark(#121133,#eef0ff);--mute:light-dark(#5d5c7c,#a9a8cf);--line:light-dark(#e1e3ef,#2a2960);--soft:light-dark(#eef9f8,#14304a)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16.5px/1.6 Heebo,Arial,sans-serif}
button{font:inherit;cursor:pointer}
.bar{position:sticky;top:0;z-index:20;background:var(--navy);color:#fff;display:flex;gap:10px;align-items:center;padding:10px max(3vw,14px);flex-wrap:wrap}
.bar b{flex:1;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar a,.bar button{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:6px 14px;text-decoration:none;font-size:15px}
.wrap{max-width:880px;margin:auto;padding:22px max(3vw,14px)}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.tabs button{border:2px solid var(--line);background:var(--card);color:var(--ink);border-radius:12px;padding:6px 14px;font-weight:700}
.tabs button small{display:block;font-weight:500;font-size:12px;color:var(--mute)}
.tabs button[aria-selected=true]{border-color:var(--orange);background:var(--orange);color:#fff}.tabs button[aria-selected=true] small{color:#fff}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:clamp(18px,3vw,30px)}
.head{display:flex;justify-content:space-between;gap:10px;color:var(--mute);font-weight:700;font-size:14.5px;margin-bottom:8px;flex-wrap:wrap}
.prog{height:6px;background:var(--line);border-radius:9px;overflow:hidden;margin-bottom:16px}.prog i{display:block;height:100%;background:var(--teal);transition:width .3s}
.q{font-size:20px;font-weight:700;margin:0 0 14px;line-height:1.45}
.opts{display:grid;gap:10px}
.opt{display:flex;gap:12px;align-items:flex-start;text-align:start;border:2px solid var(--line);background:var(--bg);color:var(--ink);border-radius:12px;padding:10px 14px;width:100%}
.opt:hover:not([disabled]){border-color:var(--teal)}
.opt .l{flex:none;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:var(--navy);color:#fff;font-weight:800}
.opt .tx{flex:1}.opt .why{display:none;font-size:14.5px;color:var(--mute);margin-top:4px}
.done .opt .why{display:block}.opt[disabled]{cursor:default}
.opt.ok{border-color:var(--green);background:light-dark(#ecfbf4,#123a2c)}.opt.ok .l{background:var(--green)}
.opt.bad{border-color:var(--red);background:light-dark(#fdecec,#3b1518)}.opt.bad .l{background:var(--red)}
.nav{display:flex;gap:10px;justify-content:space-between;margin-top:16px;align-items:center;flex-wrap:wrap}
.nav button{border:0;border-radius:10px;padding:9px 22px;font-weight:700}
.nav .next{background:var(--orange);color:#fff}.nav .sec{background:none;border:1px solid var(--line);color:var(--ink)}
.fb{font-weight:800;font-size:17px}.fb.ok{color:var(--green)}.fb.bad{color:var(--red)}
.res{text-align:center}.res .big{font-size:52px;font-weight:800;color:var(--teal-d);line-height:1.1}
.res ul{text-align:start;padding-inline-start:20px}.res li{margin:6px 0}
.res .acts{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:14px}
.res .acts button{border:0;border-radius:10px;padding:9px 20px;font-weight:700;background:var(--orange);color:#fff}.res .acts button.sec{background:none;border:1px solid var(--line);color:var(--ink)}
.print{display:none}
footer{text-align:center;color:var(--mute);font-size:14px;padding:22px}footer .ver{display:block}
@media(max-width:600px){.bar a,.bar button{padding:5px 10px;font-size:13.5px}.q{font-size:18px}}
@media print{@page{size:A4;margin:14mm}:root{color-scheme:light}body{background:#fff;font-size:10.5pt}
 .bar,.tabs,.card,footer{display:none!important}.print{display:block}
 .print h2{margin:0 0 8px}.print .pq{break-inside:avoid;margin:0 0 10px}.print .pq b{display:block}
 .print ol{margin:2px 0;padding-inline-start:22px;list-style:hebrew}.print .key{break-before:page}
 .print .key li{break-inside:avoid;margin:0 0 6px}}
'''

JS = r'''
const C=__DATA__,KEY='ngqa-quiz-__CID__-v1',$=id=>document.getElementById(id),L=['א','ב','ג','ד'];
let S;try{S=JSON.parse(localStorage.getItem(KEY))||{}}catch(e){S={}}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}};
let ch=null,st=null;
function tabs(){$('tabs').innerHTML=C.map(c=>{const b=S['best'+c.n];return `<button type="button" role="tab" data-n="${c.n}" aria-selected="${ch&&ch.n===c.n}">פרק ${c.n}<small>${b!=null?'שיא: '+b+'/'+c.qs.length:c.qs.length+' שאלות'}</small></button>`}).join('');
  document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>start(+b.dataset.n))}
function start(n,only){ch=C.find(c=>c.n===n);st={i:0,ans:[],ids:only||ch.qs.map((_,i)=>i)};history.replaceState(null,'','#ch'+n);tabs();show();printView()}
function show(){const k=st.ids[st.i],q=ch.qs[k],a=st.ans[st.i];
  $('card').innerHTML=`<div class="head"><span>פרק ${ch.n} · ${ch.t}</span><span>שאלה ${st.i+1} מתוך ${st.ids.length}</span></div>
  <div class="prog"><i style="width:${st.i/st.ids.length*100}%"></i></div><p class="q">${q.q}</p>
  <div class="opts ${a!=null?'done':''}">${q.o.map((o,j)=>`<button type="button" class="opt ${a!=null?(j===q.a?'ok':(j===a?'bad':'')):''}" data-j="${j}" ${a!=null?'disabled':''}><span class="l">${L[j]}</span><span class="tx">${o}<span class="why">${q.w[j]}</span></span></button>`).join('')}</div>
  <div class="nav"><span class="fb ${a==null?'':(a===q.a?'ok':'bad')}">${a==null?'':(a===q.a?'✓ נכון!':'✗ לא נכון — התשובה הנכונה: '+L[q.a])}</span>
  <span>${st.i>0?'<button type="button" class="sec" id="prev">הקודמת</button> ':''}${a!=null?`<button type="button" class="next" id="nx">${st.i<st.ids.length-1?'לשאלה הבאה':'לתוצאות'}</button>`:''}</span></div>`;
  document.querySelectorAll('.opt').forEach(b=>b.onclick=()=>{st.ans[st.i]=+b.dataset.j;show()});
  const nx=$('nx');if(nx){nx.onclick=()=>{if(st.i<st.ids.length-1){st.i++;show()}else result()};nx.focus()}
  const pv=$('prev');if(pv)pv.onclick=()=>{st.i--;show()}}
function result(){const wrong=st.ids.filter((k,i)=>st.ans[i]!==ch.qs[k].a),ok=st.ids.length-wrong.length;
  if(st.ids.length===ch.qs.length){S['best'+ch.n]=Math.max(S['best'+ch.n]||0,ok);save()}
  const pct=Math.round(ok/st.ids.length*100),next=C.find(c=>c.n===ch.n+1);
  $('card').innerHTML=`<div class="res"><div class="head"><span>פרק ${ch.n} · ${ch.t}</span><span>סיום</span></div><div class="big">${ok}/${st.ids.length}</div>
  <p>${pct>=80?'מצוין! אתם מוכנים לפרק הבא.':pct>=65?'יפה — כדאי לחזור על השאלות שטעיתם בהן.':'כדאי לחזור על הפרק בספר המסכם ובמצגת, ולנסות שוב.'}</p>
  ${wrong.length?`<ul>${wrong.map(k=>`<li>${ch.qs[k].q} — <b>${L[ch.qs[k].a]}. ${ch.qs[k].o[ch.qs[k].a]}</b></li>`).join('')}</ul>`:''}
  <div class="acts">${wrong.length?`<button type="button" id="rw">תרגול רק של הטעויות (${wrong.length})</button>`:''}<button type="button" class="sec" id="ra">מההתחלה</button>${next?`<button type="button" class="sec" id="nc">לפרק ${next.n}</button>`:''}</div></div>`;
  tabs();if($('rw'))$('rw').onclick=()=>start(ch.n,wrong);$('ra').onclick=()=>start(ch.n);if($('nc'))$('nc').onclick=()=>start(next.n)}
function printView(){$('print').innerHTML=`<h2>__LABEL__ · שאלות חזרה · פרק ${ch.n} — ${ch.t}</h2>`+ch.qs.map((q,i)=>`<div class="pq"><b>${i+1}. ${q.q}</b><ol>${q.o.map(o=>`<li>${o}</li>`).join('')}</ol></div>`).join('')+
  `<div class="key"><h2>תשובות והסברים — פרק ${ch.n}</h2><ol>${ch.qs.map(q=>`<li><b>${L[q.a]}.</b> ${q.o[q.a]} — ${q.w[q.a]}</li>`).join('')}</ol></div>`}
$('prt').onclick=()=>window.print();
const m=location.hash.match(/ch(\d+)/);start(m&&C.find(c=>c.n===+m[1])?+m[1]:C[0].n);
'''

page = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<script src="/auth.js"></script>
<script>document.documentElement.style.visibility='hidden';NGQAAuth.guard('{CID}').then(ok=>{{if(ok)document.documentElement.style.visibility=''}}).catch(()=>{{document.documentElement.style.visibility=''}});</script>
<script>try{{const t=localStorage.getItem('ngqa-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_m.TITLE} · {LABEL} | NGQA</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="../favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="bar"><b>{_m.TITLE} · {LABEL}</b><button type="button" id="prt">הדפסת הפרק</button><a href="../">חזרה לקורס</a></div>
<div class="wrap"><div class="tabs" id="tabs" role="tablist"></div><div class="card" id="card"></div><div class="print" id="print"></div></div>
<footer>כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה<span class="ver">שאלות חזרה <bdi dir="ltr">v{VER} · {DATE}</bdi></span></footer>
<script>{JS.replace('__DATA__', json.dumps(chs, ensure_ascii=False)).replace('__CID__', CID).replace('__LABEL__', LABEL)}</script>
</body>
</html>
'''
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(page, encoding='utf-8')
print('ok', [(c['n'], len(c['qs']), [q['a'] for q in c['qs']].count(0)) for c in chs])
