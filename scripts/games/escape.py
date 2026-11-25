#!/usr/bin/env python3
"""Generic NGQA escape-room builder. Usage: python3 escape.py <course-id> <LABEL> <content.py> [VER] [DATE]
Builds site/courses/<id>/escape/index.html (answers as salted SHA-256) and pdf/NGQA-<LABEL>-escape-solutions.pdf."""
import hashlib, json, re, pathlib, asyncio, sys, importlib.util
CID, LABEL, SRC = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
VER = sys.argv[4] if len(sys.argv) > 4 else '1.0'
DATE = sys.argv[5] if len(sys.argv) > 5 else '23.11.2026'
_spec = importlib.util.spec_from_file_location('content', SRC); _m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
TITLE, INTRO, ROOMS, FINAL_LOCK, FINAL = _m.TITLE, _m.INTRO, _m.ROOMS, _m.FINAL_LOCK, _m.FINAL
MINUTES, PENALTY = getattr(_m, 'MINUTES', 75), getattr(_m, 'PENALTY', 3)
CERT = getattr(_m, 'CERT', 'סקרתם, אימתתם ותיקנתם — בדיוק כמו שבודק תוכנה עושה.')
CERT_TITLE = getattr(_m, 'CERT_TITLE', 'יצאתם מהחדר! 🎉')
ROOT = pathlib.Path(__file__).resolve().parents[2]
R = SRC.parent
SITE = ROOT / 'site' / 'courses' / CID
SOL = f'NGQA-{LABEL}-escape-solutions.pdf'

norm = lambda s: re.sub(r'[^A-Z0-9]', '', s.upper())
h = lambda i, a: hashlib.sha256(f'ngqa-er|{i}|{norm(a)}'.encode()).hexdigest()

def pub_lock(l):
    return dict(id=l['id'], label=l['label'], fmt=l['fmt'], hash=h(l['id'], l['ans']), hints=l['hints'])

data = dict(minutes=MINUTES, penalty=PENALTY,
            rooms=[dict(id=r['id'], n=r['n'], title=r['title'], sub=r['sub'], body=r['body'], reward=r['reward'],
                        locks=[pub_lock(l) for l in r['locks']]) for r in ROOMS],
            final=pub_lock(FINAL_LOCK))
_rw = sorted((r['reward'][1], r['reward'][0]) for r in ROOMS)
assert [p for p, _ in _rw] == list(range(1, len(ROOMS) + 1)) and ''.join(c for _, c in _rw) == FINAL, ('rewards do not spell FINAL', _rw)
for r in ROOMS:
    for l in r['locks']:
        assert norm(l['ans']) == l['ans'] or l['id'] == 'r3b', l['id']

CSS = r'''
:root{color-scheme:light dark;--navy:#121133;--teal:#14DACD;--teal-d:#0E9F97;--orange:#F38911;--red:#e5484d;--green:#1fb57a;
--bg:light-dark(#f4f6fb,#0b0a24);--card:light-dark(#fff,#18173f);--ink:light-dark(#121133,#eef0ff);--mute:light-dark(#5d5c7c,#a9a8cf);--line:light-dark(#e1e3ef,#2a2960);--soft:light-dark(#eef9f8,#14304a)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16.5px/1.65 Heebo,Arial,sans-serif}
button,input{font:inherit}
.bar{position:sticky;top:0;z-index:20;background:var(--navy);color:#fff;display:flex;gap:10px;align-items:center;padding:10px max(3vw,14px);flex-wrap:wrap}
.bar b{flex:1;font-size:17px}
.bar a,.bar button{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:6px 14px;text-decoration:none;cursor:pointer;font-size:15px}
.clock{font:700 20px/1 ui-monospace,Consolas,monospace;direction:ltr;background:#000a;border-radius:10px;padding:8px 12px;color:var(--teal)}
.clock.late{color:var(--orange)}
.wrap{max-width:1440px;margin:auto;padding:26px max(3vw,14px)}
.hero{background:var(--navy);color:#fff;border-radius:18px;padding:clamp(22px,4vw,40px);margin-bottom:22px}
.hero h1{margin:0 0 8px;font-size:clamp(26px,4vw,40px);line-height:1.15}
.hero p{color:#c9cbf0;margin:8px 0;max-width:75ch}.hero q{color:#fff}
.hero .go{margin-top:12px;background:var(--orange);color:#fff;border:0;border-radius:12px;padding:10px 22px;font-weight:700;font-size:17px;cursor:pointer}
.slots{display:flex;gap:8px;direction:ltr;justify-content:center;margin:0 0 22px}
.slots span{width:52px;height:60px;border-radius:12px;border:2px dashed var(--line);display:grid;place-items:center;font:800 28px Heebo,Arial;position:relative;background:var(--card)}
.slots span small{position:absolute;bottom:2px;font-size:11px;color:var(--mute);font-weight:500}
.slots span.on{border:2px solid var(--teal);color:var(--teal-d)}
.rooms{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:22px}
@media(max-width:800px){.rooms{grid-template-columns:1fr 1fr}}@media(max-width:520px){.rooms{grid-template-columns:1fr}}
.rm{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;text-align:start;cursor:pointer;color:inherit;position:relative}
.rm:hover{border-color:var(--teal)}.rm.cur{border:2px solid var(--orange)}
.rm .n{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;font-weight:800;margin-inline-end:8px}
.rm b{font-size:17.5px}.rm small{display:block;color:var(--mute);font-size:13.5px;margin-top:4px}
.rm .st{position:absolute;inset-block-start:12px;inset-inline-end:14px;font-size:13px;font-weight:700;color:var(--mute)}
.rm.done .st{color:var(--green)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:clamp(18px,3vw,32px);margin-bottom:22px}
.panel h2{margin:0;font-size:26px}.panel .sub{color:var(--teal-d);font-weight:700;margin-bottom:12px}
q{quotes:"\201D" "\201C"}
.codebox,.cfg,.req,.runs,.fields{background:light-dark(#f6f7fc,#11103a);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:12px 0}
.codebox div{display:flex;gap:12px;align-items:center;margin:6px 0}
code{direction:ltr;unicode-bidi:isolate;font:15.5px ui-monospace,Consolas,monospace;background:var(--soft);padding:2px 8px;border-radius:6px}
pre{margin:0;font:14.5px/1.6 ui-monospace,Consolas,monospace;white-space:pre-wrap}
.lab{display:inline-grid;place-items:center;min-width:28px;height:28px;border-radius:8px;background:var(--orange);color:#fff;font-weight:800;font-size:15px;margin-inline-end:8px;flex:none}
.frags{display:grid;gap:8px;margin:12px 0}.frags div{border:1px solid var(--line);border-radius:10px;padding:8px 12px;display:flex;align-items:flex-start;background:light-dark(#fffdf8,#1b1a44)}
.cases{padding-inline-start:26px}.cases li{margin:6px 0}
.runs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}@media(max-width:700px){.runs{grid-template-columns:1fr}}
.runs ol{margin:4px 0;padding-inline-start:20px;font-size:14.5px}
.doc{background:light-dark(#f6f7fc,#11103a);border:1px solid var(--line);border-radius:12px;padding:10px 16px 10px 16px;padding-inline-start:40px;font-size:15px}
.fields{display:flex;flex-wrap:wrap;gap:8px}.fields span{border:1px solid var(--line);border-radius:8px;padding:4px 10px;background:var(--card)}
.req ul{margin:6px 0;padding-inline-start:22px}
.tw{overflow-x:auto;margin:12px 0}table{border-collapse:collapse;width:100%;font-size:15px}th{background:var(--navy);color:#fff;padding:7px 10px;text-align:start}td{border-bottom:1px solid var(--line);padding:7px 10px}
.lock{border-top:2px dashed var(--line);margin-top:18px;padding-top:16px}
.lock .q{font-weight:700}.lock .fmt{color:var(--mute);font-size:14px}
.lock form{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap}
.lock input{flex:1;min-width:180px;border:2px solid var(--line);border-radius:10px;padding:8px 12px;background:var(--bg);color:var(--ink);direction:ltr;text-align:center;font:700 18px ui-monospace,Consolas,monospace;letter-spacing:2px}
.lock button.try{background:var(--navy);color:#fff;border:0;border-radius:10px;padding:8px 20px;font-weight:700;cursor:pointer}
:root[data-theme=dark] .lock button.try{background:var(--teal-d)}
.lock .msg{min-height:1.4em;font-weight:700}.msg.bad{color:var(--red)}.msg.ok{color:var(--green)}
.lock.solved input{border-color:var(--green);background:light-dark(#ecfbf4,#123a2c)}
.shake{animation:sh .35s}@keyframes sh{25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
.hints{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.hints button{background:none;border:1px solid var(--line);color:var(--ink);border-radius:999px;padding:3px 12px;font-size:14px;cursor:pointer}
.hints button:disabled{opacity:.45;cursor:default}
.hint{background:light-dark(#fff4e6,#3a2a12);border-inline-start:4px solid var(--orange);border-radius:8px;padding:6px 12px;margin:6px 0;font-size:15px}
.reward{margin-top:14px;background:var(--soft);border-radius:12px;padding:10px 14px;font-weight:700}
.final{border:2px solid var(--orange)}
.cert{display:none;text-align:center;border:6px double var(--teal);border-radius:18px;padding:30px;background:var(--card);margin-bottom:22px}
.cert h2{font-size:32px;margin:6px 0}.cert .nm{font-size:28px;font-weight:800;color:var(--teal-d)}
.cert .row{display:flex;gap:26px;justify-content:center;flex-wrap:wrap;margin:14px 0;font-size:18px}
.cert button,.solbox a{background:var(--orange);color:#fff;border:0;border-radius:10px;padding:8px 18px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}
.solbox{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 18px;margin-bottom:22px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.solbox p{margin:0;flex:1;color:var(--mute)}
footer{text-align:center;color:var(--mute);font-size:14px;padding:22px}footer .ver{display:block}
@media print{.bar,.rooms,.panel,.slots,.hero,.solbox,footer{display:none!important}body{background:#fff}.cert{display:block!important;margin-top:40mm}}
'''

JS = r'''
const D=__DATA__,KEY='ngqa-escape-__CID__-v1',$=id=>document.getElementById(id);
let S;try{S=JSON.parse(localStorage.getItem(KEY))||{}}catch(e){S={}}
S.solved=S.solved||{};S.hints=S.hints||{};S.vals=S.vals||{};
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}};
const norm=s=>s.toUpperCase().replace(/[^A-Z0-9]/g,'');
async function sha(t){const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(t));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')}
const allLocks=()=>[...D.rooms.flatMap(r=>r.locks),D.final];
const hintCount=()=>Object.values(S.hints).reduce((a,b)=>a+b,0);
const roomDone=r=>r.locks.every(l=>S.solved[l.id]);
const elapsed=()=>S.start?((S.end||Date.now())-S.start)/1000+hintCount()*D.penalty*60:0;
const fmt=s=>{s=Math.max(0,Math.floor(s));const m=Math.floor(s/60),x=s%60;return String(m).padStart(2,'0')+':'+String(x).padStart(2,'0')};
let cur=null;
function tick(){const e=elapsed(),left=D.minutes*60-e;const c=$('clock');
  if(!S.start){c.textContent=fmt(D.minutes*60);return}
  c.textContent=left>=0?fmt(left):'+'+fmt(-left);c.classList.toggle('late',left<0);
  $('solbox').style.display=(S.end||left<0)?'flex':'none'}
function slots(){$('slots').innerHTML=[1,2,3,4,5,6].map(p=>{const r=D.rooms.find(r=>r.reward[1]===p);const on=r&&roomDone(r);return `<span class="${on?'on':''}">${on?r.reward[0]:''}<small>${p}</small></span>`}).join('')}
function grid(){$('rooms').innerHTML=D.rooms.map(r=>{const d=roomDone(r),k=r.locks.filter(l=>S.solved[l.id]).length;
  return `<button type="button" class="rm${d?' done':''}${cur===r.id?' cur':''}" data-r="${r.id}"><span class="n">${r.n}</span><b>${r.title}</b><small>${r.sub}</small><span class="st">${d?'✓ נפרץ':k+'/'+r.locks.length}</span></button>`}).join('')+
  `<button type="button" class="rm${S.end?' done':''}${cur==='fin'?' cur':''}" data-r="fin"><span class="n">★</span><b>דלת השחרור</b><small>${D.rooms.every(roomDone)?'כל המנעולים נפרצו — הזינו את הסיסמה':'נפתחת אחרי שכל ששת החדרים נפרצו'}</small><span class="st">${S.end?'✓ שוחרר':''}</span></button>`;
  document.querySelectorAll('.rm').forEach(b=>b.onclick=()=>{if(!S.start){alert('לחצו קודם על "מתחילים" — השעון יתחיל לרוץ.');return}open(b.dataset.r)})}
function lockHtml(l){const n=S.hints[l.id]||0,sv=S.solved[l.id];
  return `<div class="lock${sv?' solved':''}" id="L-${l.id}"><div class="q">${l.label}</div><div class="fmt">פורמט: ${l.fmt}</div>
  <form data-l="${l.id}"><input autocomplete="off" spellcheck="false" aria-label="קוד" value="${sv?(S.vals[l.id]||''):''}" ${sv?'disabled':''}><button class="try" ${sv?'disabled':''}>${sv?'✓ נפתח':'נסה לפתוח'}</button></form>
  <div class="msg ${sv?'ok':''}">${sv?'המנעול נפתח.':''}</div>
  <div class="hints">${sv?'':`<button type="button" data-h="${l.id}" ${n>=3?'disabled':''}>רמז ${Math.min(n+1,3)} מתוך 3 (+${D.penalty} דק׳)</button>`}</div>
  ${l.hints.slice(0,n).map((t,i)=>`<div class="hint"><b>רמז ${i+1}:</b> ${t}</div>`).join('')}</div>`}
function open(id){cur=id;grid();const p=$('panel');p.style.display='block';
  if(id==='fin'){p.className='panel final';const ready=D.rooms.every(roomDone);
    p.innerHTML=`<h2>דלת השחרור</h2><div class="sub">כל האותיות שאספתם — במקום הנכון</div>`+(ready?lockHtml(D.final):'<p>הדלת נעולה עד שכל ששת החדרים ייפרצו. האותיות שכבר אספתם מופיעות למעלה.</p>')}
  else{const r=D.rooms.find(r=>r.id===id);p.className='panel';
    p.innerHTML=`<h2>חדר ${r.n} · ${r.title}</h2><div class="sub">${r.sub}</div>${r.body}${r.locks.map(lockHtml).join('')}`+(roomDone(r)?`<div class="reward">🔓 החדר נפרץ! על הקיר מופיעה האות <b>${r.reward[0]}</b>, ולידה המספר <b>${r.reward[1]}</b>.</div>`:'')}
  bind();p.scrollIntoView({behavior:'smooth',block:'start'})}
function bind(){
  document.querySelectorAll('.lock form').forEach(f=>f.onsubmit=async e=>{e.preventDefault();const id=f.dataset.l,l=allLocks().find(x=>x.id===id),inp=f.querySelector('input'),v=norm(inp.value),m=f.parentNode.querySelector('.msg');
    if(!v){m.className='msg bad';m.textContent='הקלידו קוד.';return}
    if(await sha(`ngqa-er|${id}|${v}`)===l.hash){S.solved[id]=true;S.vals[id]=inp.value.trim();if(id==='fin'&&!S.end)S.end=Date.now();save();slots();open(cur);if(id==='fin')finish()}
    else{S.tries=(S.tries||0)+1;save();m.className='msg bad';m.textContent='המנעול לא זז. בדקו שוב — או קחו רמז.';f.classList.remove('shake');void f.offsetWidth;f.classList.add('shake')}});
  document.querySelectorAll('[data-h]').forEach(b=>b.onclick=()=>{const id=b.dataset.h;const n=S.hints[id]||0;if(n>=3)return;
    if(!confirm(`לחשוף את רמז ${n+1}? יתווספו ${D.penalty} דקות לזמן שלכם.`))return;S.hints[id]=n+1;save();open(cur);tick()})}
async function finish(){let name='';try{const i=NGQAAuth.info(await NGQAAuth.session());name=(i&&(i.name||i.email))||''}catch(e){}
  $('cn').textContent=name||'בודק/ת אמיץ/ה';$('ct').textContent=fmt(elapsed());$('ch').textContent=hintCount();
  $('cd').textContent=new Date(S.end).toLocaleDateString('he-IL');$('cert').style.display='block';$('cert').scrollIntoView({behavior:'smooth'})}
$('go').onclick=()=>{if(!S.start){S.start=Date.now();save()}$('go').style.display='none';tick();open(D.rooms[0].id)};
$('reset').onclick=()=>{if(confirm('לאפס את כל ההתקדמות ולהתחיל מחדש?')){S={solved:{},hints:{},vals:{}};save();location.reload()}};
$('cprint').onclick=()=>window.print();
if(S.start)$('go').textContent='ממשיכים';
slots();grid();tick();setInterval(tick,1000);if(S.end)finish();
'''

page = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<script src="/auth.js"></script>
<script>document.documentElement.style.visibility='hidden';NGQAAuth.guard('{CID}').then(ok=>{{if(ok)document.documentElement.style.visibility=''}}).catch(()=>{{document.documentElement.style.visibility=''}});</script>
<script>try{{const t=localStorage.getItem('ngqa-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>חדר בריחה · {LABEL} | NGQA</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="../favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="bar"><b>חדר בריחה · {LABEL}</b><span class="clock" id="clock" title="זמן שנותר (כולל קנס רמזים)">{MINUTES}:00</span><button type="button" id="reset">איפוס</button><a href="../">חזרה לקורס</a></div>
<div class="wrap">
<div class="hero"><h1>{TITLE}</h1>{INTRO}<button type="button" class="go" id="go">מתחילים — השעון רץ</button></div>
<div class="slots" id="slots" aria-label="סיסמת השחרור"></div>
<div class="rooms" id="rooms"></div>
<div class="panel" id="panel" style="display:none"></div>
<div class="cert" id="cert"><div>NGQA · {LABEL}</div><h2>{CERT_TITLE}</h2><div>תעודת בריחה · {TITLE}</div><div class="nm" id="cn"></div>
<div class="row"><span>זמן כולל: <b id="ct" dir="ltr"></b></span><span>רמזים: <b id="ch"></b></span><span>תאריך: <b id="cd"></b></span></div>
<p>{CERT}</p><button type="button" id="cprint">הדפסת התעודה</button></div>
<div class="solbox" id="solbox" style="display:none"><p>מדריך הפתרונות המלא — כל תשובה עם ההסבר שלה. הוא נפתח אחרי שמשתחררים מהחדר או כשהזמן נגמר.</p><a href="../pdf/{SOL}" download="{SOL}">הורדת מדריך הפתרונות</a></div>
</div>
<footer>כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה<span class="ver">חדר בריחה <bdi dir="ltr">v{VER} · {DATE}</bdi></span></footer>
<script>{JS.replace('__DATA__', json.dumps(data, ensure_ascii=False)).replace('__CID__', CID)}</script>
</body>
</html>
'''
out = SITE / 'escape'; out.mkdir(exist_ok=True)
(out / 'index.html').write_text(page, encoding='utf-8')

# ---- solutions guide ----
def sol_lock(l):
    return f'<div class="lk"><div class="q">{l["label"]}</div><div class="ans">תשובה: <b dir="ltr">{l["ans"]}</b></div><p>{l["why"]}</p></div>'
rooms_html = ''.join(f'<section><h2>חדר {r["n"]} · {r["title"]}</h2><div class="sub">{r["sub"]}</div>{r["body"]}{"".join(sol_lock(l) for l in r["locks"])}'
                     f'<div class="rw">פרס החדר: האות <b>{r["reward"][0]}</b> במיקום <b>{r["reward"][1]}</b></div></section>' for r in ROOMS)
sol = f'''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{CSS}
body{{background:#fff;color:#121133;font-size:11pt;line-height:1.6}}
@page{{size:A4;margin:15mm}}
.cv{{background:#121133;color:#fff;border-radius:14px;padding:26px 30px;margin-bottom:16px}}.cv h1{{margin:0 0 6px;font-size:26pt}}.cv p{{color:#c9cbf0;margin:4px 0}}
section{{break-before:page}}section h2{{color:#0E9F97;font-size:18pt;margin:0}}.sub{{color:#5d5c7c;font-weight:700;margin-bottom:8px}}
.lk{{border:2px solid #14DACD;border-radius:12px;padding:10px 14px;margin:12px 0;break-inside:avoid;background:#f3fdfc}}
.lk .q{{font-weight:700}}.ans{{font-size:13pt;margin:6px 0}}.ans b{{background:#F38911;color:#fff;border-radius:6px;padding:1px 10px;font-family:Consolas,monospace;letter-spacing:1px}}
.rw{{font-weight:700;background:#eef9f8;border-radius:10px;padding:8px 12px}}
.frags div,.codebox,.cfg,.req,.runs,.fields,.doc{{break-inside:avoid}}
</style></head><body>
<div class="cv"><h1>מדריך פתרונות — {TITLE}</h1><p>NGQA · {LABEL} · חדר בריחה v{VER} · {DATE}</p><p>לכל מנעול: התשובה, הדרך אליה, והקשר לחומר הקורס. מומלץ לקרוא אחרי המשחק.</p></div>
<h2>איך משחקים</h2>{INTRO}<p>החדרים פתוחים בכל סדר. כל חדר שנפרץ חושף אות ואת מיקומה בסיסמת השחרור. אפשר להשתמש בשלושה רמזים לכל מנעול, וכל רמז מוסיף {PENALTY} דקות. ההתקדמות נשמרת בדפדפן.</p>
<div class="rw">תקציר התשובות: {" · ".join(f"{l['id'].upper()}: {l['ans']}" for r in ROOMS for l in r["locks"])} · סיסמה: {FINAL}</div>
{rooms_html}
<section><h2>דלת השחרור</h2>{sol_lock(FINAL_LOCK)}</section>
</body></html>'''
(R / 'build').mkdir(exist_ok=True)
(R / 'build' / 'solutions.html').write_text(sol, encoding='utf-8')

async def pdf():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome'); pg = await b.new_page()
        await pg.goto((R / 'build' / 'solutions.html').as_uri(), wait_until='networkidle')
        await pg.pdf(path=str(SITE / 'pdf' / SOL), format='A4', print_background=True, display_header_footer=True,
                     header_template='<div></div>',
                     footer_template='<div style="width:100%;font:9px Arial;color:#888;text-align:center">NGQA · '+LABEL+' Escape Room · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
                     margin={'top': '15mm', 'bottom': '16mm', 'left': '14mm', 'right': '14mm'})
        await b.close()
asyncio.run(pdf())
print('ok', len(page), 'bytes;', sum(len(r['locks']) for r in ROOMS) + 1, 'locks')
