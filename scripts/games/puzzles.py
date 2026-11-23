#!/usr/bin/env python3
"""Generic NGQA crossword (תשבץ) + cryptic crossword (תשחץ) builder.
Usage: python3 puzzles.py <course-id> <LABEL> <words.py> [VER] [DATE]  ->  site/courses/<id>/puzzles/index.html"""
import json, base64, pathlib, sys, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen import layout
CID, LABEL, SRC = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
VER = sys.argv[4] if len(sys.argv) > 4 else '1.0'
DATE = sys.argv[5] if len(sys.argv) > 5 else '23.11.2026'
_spec = importlib.util.spec_from_file_location('words', SRC); _m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
CROSS, CRYPTIC = _m.CROSS, _m.CRYPTIC
IC = getattr(_m, 'INTRO_CROSS', 'תשבץ הגדרות: התשובות הן המונחים המקצועיים באנגלית, כפי שהם מופיעים בקורס. התשבץ נקרא משמאל לימין.')
IY = getattr(_m, 'INTRO_CRYPTIC', 'תשחץ: הגדרות היגיון, עם משחקי מילים ומשמעות כפולה. גם כאן התשובות הן מונחים באנגלית — חשבו פעמיים לפני שאתם כותבים!')
OUT = pathlib.Path(__file__).resolve().parents[2] / 'site' / 'courses' / CID / 'puzzles'

def pack(L):
    # answers are lightly obfuscated so they are not readable at a glance in the page source
    e = [dict(n=x['n'], d=x['d'], r=x['r'], c=x['c'], len=len(x['ans']), clue=x['clue'],
              a=base64.b64encode(x['ans'][::-1].encode()).decode()) for x in L['entries']]
    return dict(H=L['H'], W=L['W'], entries=e)

P = dict(cross=pack(layout(CROSS)), cryptic=pack(layout(CRYPTIC)))

CSS = r'''
:root{color-scheme:light dark;--navy:#121133;--teal:#14DACD;--teal-d:#0E9F97;--orange:#F38911;--red:#e5484d;--green:#1fb57a;
--bg:light-dark(#f4f6fb,#0b0a24);--card:light-dark(#fff,#18173f);--ink:light-dark(#121133,#eef0ff);--mute:light-dark(#5d5c7c,#a9a8cf);--line:light-dark(#e1e3ef,#2a2960);--soft:light-dark(#eef9f8,#14304a)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Heebo,Arial,sans-serif}
button{font:inherit;cursor:pointer}
.bar{position:sticky;top:0;z-index:20;background:var(--navy);color:#fff;display:flex;gap:10px;align-items:center;padding:10px max(3vw,14px);flex-wrap:wrap}
.bar b{flex:1;font-size:17px}
.bar a{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:6px 14px;text-decoration:none;font-size:15px}
.wrap{max-width:1240px;margin:auto;padding:22px max(3vw,14px)}
.tabs{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.tabs button{border:2px solid var(--line);background:var(--card);color:var(--ink);border-radius:12px;padding:8px 18px;font-weight:700}
.tabs button[aria-selected=true]{border-color:var(--orange);background:var(--orange);color:#fff}
.intro{color:var(--mute);margin:0 0 14px}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.tools button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:10px;padding:6px 14px;font-size:15px}
.tools button:hover{border-color:var(--teal)}
.tools .st{margin-inline-start:auto;font-weight:700;color:var(--teal-d);align-self:center}
.lay{display:grid;grid-template-columns:minmax(0,auto) minmax(280px,1fr);gap:24px;align-items:start}
@media(max-width:980px){.lay{grid-template-columns:1fr}}
.gwrap{overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px}
.grid{display:grid;direction:ltr;gap:0;width:max-content}
.cell{width:var(--cs,34px);height:var(--cs,34px);position:relative}
.cell.on{background:light-dark(#fff,#0f0e2e);outline:1px solid light-dark(#9aa0bd,#4b4a85)}
.cell input{width:100%;height:100%;border:0;background:transparent;text-align:center;font:800 calc(var(--cs,34px)*.52) Arial,sans-serif;text-transform:uppercase;color:var(--ink);padding:0;padding-top:4px;caret-color:transparent}
.cell input:focus{outline:none}
.cell .nm{position:absolute;top:1px;left:2px;font:700 9.5px Arial;color:var(--mute);pointer-events:none}
.cell.word{background:light-dark(#e6fbf9,#163b4d)}.cell.focus{background:light-dark(#ffe2bf,#5a3a10)}
.cell.bad input{color:var(--red)}.cell.good input{color:var(--green)}.cell.rev input{color:var(--orange)}
.cur{background:var(--navy);color:#fff;border-radius:12px;padding:10px 14px;margin-bottom:12px;min-height:46px}
.cur b{color:var(--teal)}
.clues{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:600px){.clues{grid-template-columns:1fr}}
.clues h3{margin:0 0 6px;font-size:18px}
.clues ol{list-style:none;margin:0;padding:0}
.clues li{padding:5px 8px;border-radius:8px;cursor:pointer;font-size:15px;line-height:1.45}
.clues li:hover{background:var(--soft)}.clues li.on{background:light-dark(#ffe2bf,#5a3a10)}
.clues li.done{color:var(--mute);text-decoration:line-through}
.clues li b{display:inline-block;min-width:26px;color:var(--orange)}
.clues li i{font-style:normal;color:var(--mute);font-size:13px;direction:ltr;unicode-bidi:isolate}
.done-msg{display:none;background:light-dark(#ecfbf4,#123a2c);border:2px solid var(--green);border-radius:12px;padding:10px 14px;margin-bottom:12px;font-weight:700}
footer{text-align:center;color:var(--mute);font-size:14px;padding:22px}footer .ver{display:block}
.ponly{display:none}
@media print{
  @page{size:A4;margin:12mm}
  :root{color-scheme:light}
  body{background:#fff;font-size:10pt;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .bar,.tabs,.tools,.cur,footer,.intro,.done-msg{display:none!important}
  .ponly{display:block;margin:0 0 6px}
  .lay{display:block}.gwrap{border:0;padding:0;margin:0 auto 10px;width:max-content}
  .cell{--cs:28px}.cell.on{background:#fff!important;outline:1px solid #555}
  body:not(.psol) .cell input{color:transparent!important}
  .cell.word,.cell.focus{background:#fff!important}
  .clues li{padding:1px 4px;font-size:9.5pt;text-decoration:none!important;color:#121133!important;background:none!important}
  .clues{break-inside:auto}
}
'''

JS = r'''
const P=__DATA__,$=id=>document.getElementById(id),KEY='ngqa-xw-__CID__-v1';
let St;try{St=JSON.parse(localStorage.getItem(KEY))||{}}catch(e){St={}}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(St))}catch(e){}};
const dec=s=>[...atob(s)].reverse().join('');
let cur='cross',G,sel=null,dir='A';
function build(){const p=P[cur];St[cur]=St[cur]||{v:{},rev:{}};const v=St[cur].v;
  G={p,cells:{},words:p.entries.map(e=>({...e,ans:dec(e.a),cells:[...Array(e.len)].map((_,i)=>[e.r+(e.d==='D'?i:0),e.c+(e.d==='A'?i:0)])}))};
  G.words.forEach(w=>w.cells.forEach(([r,c],i)=>{const k=r+','+c;(G.cells[k]=G.cells[k]||{ch:w.ans[i],w:[]}).w.push(w)}));
  const cs=Math.max(24,Math.min(36,Math.floor((Math.min(innerWidth,1240)-(innerWidth<980?60:420))/p.W)));
  const g=$('grid');g.style.setProperty('--cs',cs+'px');g.style.gridTemplateColumns=`repeat(${p.W},${cs}px)`;
  let h='';for(let r=0;r<p.H;r++)for(let c=0;c<p.W;c++){const k=r+','+c,x=G.cells[k];
    if(!x){h+='<div class="cell"></div>';continue}
    const n=G.words.find(w=>w.r===r&&w.c===c);
    h+=`<div class="cell on${St[cur].rev[k]?' rev':''}" data-k="${k}">${n?`<span class="nm">${n.n}</span>`:''}<input maxlength="1" inputmode="latin" autocomplete="off" autocapitalize="characters" aria-label="תא ${k}" value="${v[k]||''}"></div>`}
  g.innerHTML=h;
  const li=d=>G.words.filter(w=>w.d===d).map(w=>`<li data-w="${w.d}${w.n}"><b>${w.n}.</b> ${w.clue} <i>(${w.len})</i></li>`).join('');
  $('ca').innerHTML=li('A');$('cd').innerHTML=li('D');
  document.querySelectorAll('.clues li').forEach(l=>l.onclick=()=>{const w=G.words.find(w=>w.d+w.n===l.dataset.w);dir=w.d;focusCell(w.cells.find(([r,c])=>!v[r+','+c])||w.cells[0])});
  document.querySelectorAll('.cell.on input').forEach(inp=>{const k=inp.parentNode.dataset.k;
    inp.onfocus=()=>{sel=k.split(',').map(Number);const ws=G.cells[k].w;if(!ws.some(w=>w.d===dir))dir=ws[0].d;hl()};
    inp.onmousedown=()=>{if(sel&&sel.join()===k&&G.cells[k].w.length>1){dir=dir==='A'?'D':'A';setTimeout(hl)}};
    inp.oninput=()=>{const ch=(inp.value.slice(-1)||'').toUpperCase().replace(/[^A-Z]/g,'');inp.value=ch;set(k,ch);if(ch)step(1)};
    inp.onkeydown=e=>{const [r,c]=sel;
      if(e.key==='Backspace'){if(!inp.value){e.preventDefault();step(-1);const k2=sel.join(),i2=q(k2);if(i2){i2.value='';set(k2,'')}}else{inp.value='';set(k,'');e.preventDefault()}}
      else if(e.key==='ArrowRight'){e.preventDefault();mv(0,1)}else if(e.key==='ArrowLeft'){e.preventDefault();mv(0,-1)}
      else if(e.key==='ArrowDown'){e.preventDefault();mv(1,0)}else if(e.key==='ArrowUp'){e.preventDefault();mv(-1,0)}
      else if(e.key==='Enter'||e.key===' '){e.preventDefault();if(G.cells[k].w.length>1){dir=dir==='A'?'D':'A';hl()}}}});
  status();$('intro').innerHTML=cur==='cross'?__IC__:__IY__;
  $('ptitle').textContent=(cur==='cross'?'תשבץ':'תשחץ')+' __LABEL__ · NGQA'}
const q=k=>document.querySelector(`.cell[data-k="${k}"] input`);
function set(k,ch){St[cur].v[k]=ch;if(!ch)delete St[cur].v[k];const c=q(k).parentNode;c.classList.remove('bad','good');save();status()}
function word(){return G.words.find(w=>w.d===dir&&w.cells.some(([r,c])=>r===sel[0]&&c===sel[1]))}
function step(s){const w=word();if(!w)return;const i=w.cells.findIndex(([r,c])=>r===sel[0]&&c===sel[1])+s;if(i>=0&&i<w.cells.length)focusCell(w.cells[i])}
function mv(dr,dc){let [r,c]=sel;for(let t=0;t<30;t++){r+=dr;c+=dc;if(r<0||c<0||r>=G.p.H||c>=G.p.W)return;if(G.cells[r+','+c]){if(dr)dir='D';else dir='A';focusCell([r,c]);return}}}
function focusCell([r,c]){sel=[r,c];const i=q(r+','+c);i&&i.focus();hl()}
function hl(){document.querySelectorAll('.cell.word,.cell.focus').forEach(x=>x.classList.remove('word','focus'));document.querySelectorAll('.clues li.on').forEach(x=>x.classList.remove('on'));
  if(!sel)return;const w=word();if(w){w.cells.forEach(([r,c])=>q(r+','+c).parentNode.classList.add('word'));const l=document.querySelector(`li[data-w="${w.d}${w.n}"]`);l.classList.add('on');
  $('cur').innerHTML=`<b>${w.n} ${w.d==='A'?'מאוזן':'מאונך'}</b> · ${w.clue} <span dir="ltr">(${w.len})</span>`}
  q(sel.join()).parentNode.classList.add('focus')}
function status(){const v=St[cur].v;let ok=0;const all=Object.keys(G.cells);all.forEach(k=>{if(v[k]===G.cells[k].ch)ok++});
  G.words.forEach(w=>{const d=w.cells.every(([r,c])=>v[r+','+c]===G.cells[r+','+c].ch);const l=document.querySelector(`li[data-w="${w.d}${w.n}"]`);l&&l.classList.toggle('done',d)});
  $('st').textContent=`${G.words.filter(w=>w.cells.every(([r,c])=>v[r+','+c]===G.cells[r+','+c].ch)).length}/${G.words.length} מילים`;
  $('done').style.display=ok===all.length?'block':'none'}
function check(){Object.keys(G.cells).forEach(k=>{const v=St[cur].v[k];const c=q(k).parentNode;c.classList.remove('bad','good');if(v)c.classList.add(v===G.cells[k].ch?'good':'bad')})}
function reveal(ks){ks.forEach(k=>{St[cur].v[k]=G.cells[k].ch;St[cur].rev[k]=1;const i=q(k);i.value=G.cells[k].ch;i.parentNode.classList.add('rev')});save();status()}
$('bchk').onclick=check;
$('blet').onclick=()=>{if(sel)reveal([sel.join()])};
$('bwrd').onclick=()=>{const w=sel&&word();if(w)reveal(w.cells.map(x=>x.join()))};
$('ball').onclick=()=>{if(confirm('לחשוף את כל הפתרון?'))reveal(Object.keys(G.cells))};
$('bclr').onclick=()=>{if(confirm('לנקות את התשבץ?')){St[cur]={v:{},rev:{}};save();build()}};
$('bprt').onclick=()=>{document.body.classList.remove('psol');window.print()};
$('bsol').onclick=()=>{document.body.classList.add('psol');const v=St[cur].v,keep={...v};Object.keys(G.cells).forEach(k=>q(k).value=G.cells[k].ch);window.print();setTimeout(()=>{Object.keys(G.cells).forEach(k=>q(k).value=keep[k]||'');document.body.classList.remove('psol')},500)};
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{cur=b.dataset.t;document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b));sel=null;$('cur').innerHTML='בחרו תא או הגדרה כדי להתחיל.';build();history.replaceState(null,'','#'+cur)});
if(location.hash==='#cryptic')document.querySelector('[data-t=cryptic]').click();else build();
addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(build,200)});
'''

page = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<script src="/auth.js"></script>
<script>document.documentElement.style.visibility='hidden';NGQAAuth.guard('{CID}').then(ok=>{{if(ok)document.documentElement.style.visibility=''}}).catch(()=>{{document.documentElement.style.visibility=''}});</script>
<script>try{{const t=localStorage.getItem('ngqa-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>תשבץ ותשחץ · {LABEL} | NGQA</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="../favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="bar"><b>תשבץ ותשחץ · {LABEL}</b><a href="../">חזרה לקורס</a></div>
<div class="wrap">
<div class="tabs" role="tablist"><button type="button" role="tab" data-t="cross" aria-selected="true">תשבץ — מונחי הקורס</button><button type="button" role="tab" data-t="cryptic" aria-selected="false">תשחץ — הגדרות היגיון</button></div>
<p class="intro" id="intro"></p>
<h2 class="ponly" id="ptitle"></h2>
<div class="tools"><button type="button" id="bchk">בדיקה</button><button type="button" id="blet">חשיפת אות</button><button type="button" id="bwrd">חשיפת מילה</button><button type="button" id="ball">פתרון מלא</button><button type="button" id="bclr">ניקוי</button><button type="button" id="bprt">הדפסה</button><button type="button" id="bsol">הדפסת פתרון</button><span class="st" id="st"></span></div>
<div class="done-msg" id="done">🎉 כל הכבוד — פתרתם את כל התשבץ!</div>
<div class="lay">
<div><div class="cur" id="cur">בחרו תא או הגדרה כדי להתחיל.</div><div class="gwrap"><div class="grid" id="grid"></div></div></div>
<div class="clues"><div><h3>מאוזן <small>(משמאל לימין)</small></h3><ol id="ca"></ol></div><div><h3>מאונך</h3><ol id="cd"></ol></div></div>
</div>
</div>
<footer>כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה<span class="ver">תשבץ ותשחץ <bdi dir="ltr">v{VER} · {DATE}</bdi></span></footer>
<script>{JS.replace('__DATA__', json.dumps(P, ensure_ascii=False)).replace('__IC__', json.dumps(IC, ensure_ascii=False)).replace('__IY__', json.dumps(IY, ensure_ascii=False)).replace('__LABEL__', LABEL).replace('__CID__', CID)}</script>
</body>
</html>
'''
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(page, encoding='utf-8')
print('ok', {k: (v['H'], v['W'], len(v['entries'])) for k, v in P.items()})
