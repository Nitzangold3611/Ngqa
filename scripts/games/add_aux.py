#!/usr/bin/env python3
"""Insert / refresh the "חומרי עזר" (support materials) box on a course page.
Usage: python3 add_aux.py <course-id> [...]   (all courses if none given)
The box is idempotent (replaced between markers). build_course.py strips it from the genai template."""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]

ICON = {
 'book': '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5"/><path d="M8 7h7M8 11h7"/>',
 'quiz': '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7"/><path d="M12 17h.01"/>',
 'escape': '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M12 14v3"/>',
 'rec': '<rect x="3" y="5" width="14" height="14" rx="2"/><path d="M17 10l4-2v8l-4-2z"/>',
 'puzzles': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
}
ESC = {
 'genai': ('חדר בריחה: ORACLE-7', 'שישה חדרים ו-75 דקות: טוקניזציה עם OpenAI Tokenizer, הנדסת פרומפטים וטכניקות הבדיקה מפרקים 2–3. משחק לבד, עם רמזים ומדריך פתרונות.'),
 'ctfl': ('חדר בריחה: ליל השחרור', 'שישה חדרים, אחד לכל פרק בסילבוס: טעות-פגם-כשל ועקרונות, רמות וסוגי בדיקה, סקירות, טכניקות, ניהול סיכונים וכלים. משחק לבד, עם רמזים ומדריך פתרונות.'),
 'sql': ('חדר בריחה: היהלום שנעלם', 'תעלומה במוזיאון שפותרים בשאילתות אמיתיות ב-SSMS: SELECT, ‏WHERE, פונקציות, GROUP BY, ‏JOIN ושאילתות משנה. משחק לבד, עם רמזים ומדריך פתרונות.'),
 'ste': ('חדר בריחה: מתקפה בלילה', 'צוות התגובה נעול בחוץ: CIA, ‏STRIDE, ‏OWASP, ‏CVSS, תקנים ודיווח ממצאים. משחק לבד, עם רמזים ומדריך פתרונות.'),
 'ai': ('חדר בריחה: המודל שהשתגע', 'מטריצת בלבול, מדדי ביצועים, איכות נתונים, הטיה, Metamorphic Testing ועוד. משחק לבד, עם רמזים ומדריך פתרונות.'),
 'mat': ('חדר בריחה: האפליקציה שקרסה', 'פרגמנטציה, הפרעות, סוללה ורשת, סוגי אפליקציות ואוטומציה במובייל. משחק לבד, עם רמזים ומדריך פתרונות.'),
 'jobs': ('חדר בריחה: הראיון', 'קורות חיים, לינקדאין, ראיון עבודה ושאלות מראיונות — שישה מנעולים בדרך להצעת העבודה. משחק לבד, עם רמזים ומדריך פתרונות.'),
}
XW = 'המונחים המקצועיים של הקורס בשני משחקים דיגיטליים: תשבץ הגדרות ותשחץ עם הגדרות היגיון. אפשר גם להדפיס.'

def quiz_info(cid):
    """(chapters, questions per chapter) of the course's review quiz, read from the built page; None if there is none."""
    p = ROOT / 'site/courses' / cid / 'quiz/index.html'
    if not p.exists(): return None
    t = p.read_text(encoding='utf-8'); i = t.find('const C=') + 8
    try: chs = json.JSONDecoder().raw_decode(t, i)[0]
    except Exception: return None
    return len(chs), max(len(c['qs']) for c in chs)

def cards(cid):
    out = []
    def card(kind, title, text, links):
        acts = ''.join(f'<a{" class=\"pri\"" if i == 0 else ""} href="{h}"{x}>{t}</a>' for i, (t, h, x) in enumerate(links))
        out.append(f'      <div class="ax"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">{ICON[kind]}</svg></span><div><b>{title}</b><p>{text}</p><div class="acts">{acts}</div></div></div>')
    if cid == 'genai':
        card('book', 'ספר מסכם לקורס', 'כל החומר לפי פרקים ותתי-פרקים, עם מושגים והסברים בסוף כל פרק וסיכום במילים פשוטות.',
             [('קריאה', 'book/', ''), ('הורדת PDF', 'pdf/NGQA-CT-GenAI-book.pdf', ' download="NGQA-CT-GenAI-book.pdf"'), ('הדפסה', 'book/?print=1', ' target="_blank" rel="noopener"')])
    qz = quiz_info(cid)
    if qz:
        card('quiz', 'שאלות חזרה בין פרק לפרק', f'{qz[1]} שאלות אמריקאיות לכל פרק, עם הסבר לכל תשובה, ציון ותרגול חוזר של הטעויות. אפשר גם להדפיס.',
             [(f'פרק {n}', f'quiz/#ch{n}', '') for n in range(1, qz[0] + 1)])
    out.append('''      <div class="ax" id="recCard" hidden><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">''' + ICON['rec'] + '''</svg></span><div><b>שיעורים מוקלטים</b><p id="recTxt">השיעורים המוקלטים של הקורס, לפי פרקים.</p><div class="acts" id="recActs"><a class="pri" href="lessons/">לשיעורים</a></div></div></div>''')
    if (ROOT / 'site/courses' / cid / 'escape/index.html').exists():
        t, x = ESC[cid]; card('escape', t, x, [('כניסה לחדר', 'escape/', '')])
    if (ROOT / 'site/courses' / cid / 'puzzles/index.html').exists():
        card('puzzles', 'תשבץ ותשחץ', XW, [('תשבץ', 'puzzles/', ''), ('תשחץ', 'puzzles/#cryptic', '')])
    return '\n'.join(out)

CSS = '''/*aux*/.aux{margin-bottom:34px}.aux h2{margin-bottom:12px}
.auxg{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:18px}
.ax{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;display:flex;gap:16px;align-items:flex-start}
.ax .ic{flex:none;width:54px;height:54px;border-radius:14px;background:var(--navy);display:grid;place-items:center}
.ax .ic svg{width:30px;height:30px;fill:none;stroke:var(--teal);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.ax b{display:block;font-size:19px;line-height:1.3}.ax p{margin:4px 0 12px;color:var(--mute);font-size:15px}
.ax .acts{display:flex;gap:8px;flex-wrap:wrap}
.ax .acts a{text-decoration:none;border:1px solid var(--line);border-radius:10px;padding:6px 14px;font-size:15px;font-weight:600;color:var(--ink)}
.ax .acts a:hover{border-color:var(--teal)}.ax .acts a.pri{background:var(--orange);border-color:var(--orange);color:#fff}
.ax[hidden]{display:none}.ax.lockd .ic{background:#6b6a8a}.ax.flash{outline:3px solid var(--orange);outline-offset:3px}
/*/aux*/'''

# recorded-lessons card: locked look + explanation for users without the "<course>-rec" level (v3.11)
REC_JS = '''<script>/* v3.13 site settings from the backoffice: recordings on/off per course, PDF downloads, edited course info */
(()=>{const C='__C__',A=window.NGQAAuth;if(!A)return;
  const ready=f=>document.readyState==='loading'?document.addEventListener('DOMContentLoaded',f):f();
  const esc=t=>String(t??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  Promise.all([A.session(),A.config()]).then(([s,cfg])=>ready(()=>{const i=A.info(s);
    /* edited "מידע על הקורס" texts */
    const inf=cfg.info&&cfg.info[C];
    if(inf){const set=(f,v)=>{const e=document.querySelector('#cinfo [data-f="'+f+'"]');if(e&&v!=null)e.innerHTML=v};
      if(inf.about)set('about',esc(inf.about));if(inf.audience&&inf.audience.length)set('audience',inf.audience.map(x=>'<li>'+esc(x)+'</li>').join(''));
      if(inf.prereq)set('prereq',esc(inf.prereq));if(inf.goals&&inf.goals.length)set('goals',inf.goals.map(x=>'<li>'+esc(x)+'</li>').join(''))}
    /* PDF downloads switched off for students */
    if(cfg.pdf&&cfg.pdf[C]===false&&!(i&&i.admin)){const st=document.createElement('style');st.textContent='#pdf,a[href^="pdf/"],a[href*="/pdf/"]{display:none!important}';document.head.appendChild(st)}
    if(!A.REC_COURSES.includes(C))return;
    recCard(i);recTab()}));
  function recCard(i){const c=document.getElementById('recCard');if(!c)return;c.hidden=false;
    const q=new URLSearchParams(location.search),nr=q.get('norec');
    if(A.canRec(i,C)){const e=A.recEnd(i,C);if(e&&!i.admin)document.getElementById('recTxt').textContent+=' הגישה לשיעורים בתוקף עד '+A.dmy(e)+'.';return}
    c.classList.add('lockd');
    const ended=nr&&/^\\d{4}-\\d{2}-\\d{2}$/.test(nr);
    document.getElementById('recTxt').textContent=ended?'הגישה שלך לשיעורים המוקלטים הסתיימה ב-'+A.dmy(nr)+'. להארכה פנו לניצן.':'השיעורים המוקלטים לא כלולים בגישה שלך. לפרטים ולהוספה לגישה — פנו לניצן.';
    document.getElementById('recActs').innerHTML='<a class="pri" href="https://wa.me/972526718757" target="_blank" rel="noopener">וואטסאפ לניצן</a>';
    c.querySelector('b').textContent='שיעורים מוקלטים 🔒';
    if(nr!==null){history.replaceState(null,'',location.pathname+location.hash);c.scrollIntoView({block:'center'});c.classList.add('flash')}}
  /* "שיעורים מוקלטים" tab in the chapter viewer, next to מצגת / תרגילים (hash #<chapter>/rec) */
  function recTab(){const S=document.getElementById('tabS'),E=document.getElementById('tabE');if(!S||!E||document.getElementById('tabR'))return;
    const st=document.createElement('style');st.textContent='#recview{display:none;max-width:1560px;margin:16px auto 40px;padding:0 max(3vw,12px)}body.m-rec #recview{display:block}body.m-rec .stage,body.m-rec .rail,body.m-rec #feed,body.m-rec .fpill,body.m-rec #exlist,body.m-rec #exview{display:none!important}body.m-rec #fs,body.m-rec #prt,body.m-rec #tocb{display:none}#recview .rc{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px;text-align:center}#recview .rc h2{margin:0 0 8px}#recview .rc p{color:var(--mute);margin:6px auto 14px;max-width:56ch}#recview .rc a{display:inline-block;background:var(--orange);color:#fff;border-radius:10px;padding:8px 18px;font-weight:700;text-decoration:none}';
    document.head.appendChild(st);
    const R=document.createElement('button');R.type='button';R.setAttribute('role','tab');R.id='tabR';R.setAttribute('aria-selected','false');
    R.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="14" height="14" rx="2"/><path d="M17 10l4-2v8l-4-2z"/></svg>שיעורים מוקלטים';E.after(R);
    const pane=document.createElement('section');pane.id='recview';pane.setAttribute('aria-label','שיעורים מוקלטים');(document.getElementById('exview')||E).after(pane);
    const chOf=()=>(location.hash.match(/^#([^/]+)/)||[])[1];
    R.onclick=()=>{const c=chOf();if(c)location.hash=c+'/rec'};
    let lib=null;const need=()=>lib||(lib=new Promise(r=>{if(window.NGQALessons)return r();const x=document.createElement('script');x.src='/lessons.js';x.onload=r;x.onerror=r;document.head.appendChild(x)}));
    let decks=null;const getDecks=async()=>decks||(decks=await fetch('decks.json').then(r=>r.json()).catch(()=>[]));
    async function sync(){const m=location.hash.match(/^#([^/]+)\\/rec$/);document.body.classList.toggle('m-rec',!!m);R.setAttribute('aria-selected',!!m);if(!m)return;
      S.setAttribute('aria-selected',false);E.setAttribute('aria-selected',false);window.scrollTo(0,0);
      const i=A.info(await A.session());
      if(!A.canRec(i,C)){pane.innerHTML='<div class="rc"><h2>שיעורים מוקלטים 🔒</h2><p>השיעורים המוקלטים לא כלולים בגישה שלך. לפרטים ולהוספה לגישה — פנו לניצן.</p><a href="https://wa.me/972526718757" target="_blank" rel="noopener">וואטסאפ לניצן</a></div>';return}
      await need();const d=await getDecks();if(window.NGQALessons)NGQALessons.render(pane,{c:C,decks:d,only:m[1],base:'',hash:false})}
    addEventListener('hashchange',()=>setTimeout(sync,0));setTimeout(sync,0)}
})();</script>'''

# ---------------------------------------------------------------- "מידע על הקורס" tab (v3.12)
import json, html as _h
INFO = json.loads((pathlib.Path(__file__).with_name('course_info.json')).read_text(encoding='utf-8'))

WIDE_CSS = """/*wide*/.hero .in,.wrap,.stage,.where,.tabs,#exlist,#recview{max-width:1560px}.rail{max-width:1584px}#exview{max-width:1240px}
@media(min-width:1100px){#exlist .exl{grid-template-columns:1fr 1fr}}
/*/wide*/"""
INFO_CSS = """/*info*/.ctabs{display:flex;gap:6px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:5px;width:max-content;max-width:100%;margin:0 0 26px}
.ctabs button{font:inherit;font-size:16px;font-weight:700;border:0;border-radius:10px;padding:9px 18px;background:none;color:var(--mute);cursor:pointer;display:flex;align-items:center;gap:8px}
.ctabs button svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.ctabs button[aria-selected=true]{background:var(--navy);color:#fff}.ctabs button[aria-selected=true] svg{stroke:var(--teal)}
#cinfo{display:none}body.m-info #cinfo{display:block}body.m-info .wrap>:not(.ctabs):not(#cinfo){display:none!important}
.ig{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:18px}
.ic2{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px}.ic2.wide{grid-column:1/-1}
.ic2 h3{margin:0 0 10px;font-size:19px;display:flex;align-items:center;gap:10px}.ic2 h3 i{width:10px;height:10px;border-radius:3px;background:var(--teal);flex:none}
.ic2 p{margin:0 0 10px;line-height:1.7}.ic2 ul{margin:0;padding-inline-start:20px;line-height:1.75}.ic2 .mu{color:var(--mute);font-size:14.5px}
.ic2 .pre{background:light-dark(#fff6ea,#3a2a14);border-radius:10px;padding:10px 14px;margin-top:12px;font-size:15px}
.chl{list-style:none;padding:0!important;margin:0;display:grid;gap:6px}
.chl li{display:flex;align-items:center;gap:12px;border:1px solid var(--line);border-radius:12px;padding:8px 12px;cursor:pointer}
.chl li:hover{border-color:var(--teal)}.chl .n{flex:none;min-width:64px;font-size:13.5px;font-weight:700;color:var(--mute)}
.chl .t{flex:1;font-weight:600}.chl .b{flex:none;font-size:13px;color:var(--mute)}.chl .x{flex:none;font-size:12.5px;font-weight:700;border-radius:999px;padding:2px 9px;background:light-dark(#eafbfa,#13324a)}
.chl li.e .x{background:light-dark(#fff1de,#3a2a14)}
.kp{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:10px;margin:4px 0 12px}
.kp div{border:1px solid var(--line);border-radius:12px;padding:10px 12px;text-align:center}.kp b{display:block;font-size:28px;line-height:1.1;color:var(--orange)}.kp span{font-size:13.5px;color:var(--mute)}
.ok2{list-style:none;padding:0!important}.ok2 li{padding-inline-start:26px;position:relative}.ok2 li:before{content:"";position:absolute;inset-inline-start:2px;top:.55em;width:12px;height:7px;border-inline-start:2.5px solid var(--teal);border-bottom:2.5px solid var(--teal);transform:rotate(-45deg)}
.wa2{display:inline-block;background:var(--orange);color:#fff!important;border-radius:10px;padding:8px 18px;font-weight:700;text-decoration:none;margin-top:4px}
@media(max-width:600px){.ctabs{width:100%}.ctabs button{flex:1;justify-content:center;padding:9px 8px;font-size:15px}.chl .b{display:none}}
/*/info*/"""

TAB_ICONS = ('<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
             '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/></svg>')

INFO_JS = """<script>(()=>{const b=document.getElementById('ctC'),i=document.getElementById('ctI');if(!b||!i)return;
  const sync=()=>{const on=location.hash==='#info';document.body.classList.toggle('m-info',on);i.setAttribute('aria-selected',on);b.setAttribute('aria-selected',!on)};
  i.onclick=()=>{if(location.hash!=='#info')location.hash='info'};
  b.onclick=()=>{if(location.hash==='#info')history.pushState(null,'',location.pathname+location.search);sync()};
  document.querySelectorAll('#cinfo .chl li[data-id]').forEach(li=>{li.onclick=()=>{location.hash=li.dataset.id};li.tabIndex=0;li.onkeydown=e=>{if(e.key==='Enter')li.click()}});
  addEventListener('hashchange',sync);addEventListener('popstate',sync);sync()})();</script>"""

def _is_exam(d): return 'מבחן' in d['title']
def _is_proj(d): return 'פרויקט' in d['title'] or 'הנחיות לפרויקט' in d['title']

def info_html(cid):
    cfg = INFO['courses'].get(cid)
    if not cfg: return ''
    e = _h.escape
    base = ROOT / 'site/courses' / cid
    decks = json.loads((base / 'decks.json').read_text(encoding='utf-8'))
    chs = [d for d in decks if not _is_exam(d) and not _is_proj(d)]
    exams = [d for d in decks if _is_exam(d)]; projs = [d for d in decks if _is_proj(d)]
    slides = sum(len(d.get('slides', [])) for d in decks)
    nex = sum(len(d.get('ex') or []) for d in decks)
    unit = 'חלקים' if cid == 'jobs' else 'פרקים'
    # -- structure list
    lis = []
    for d in decks:
        k = 'e' if (d in exams or d in projs) else ''
        x = ''
        if d.get('ex'): x = f'<span class="x">{len(d["ex"])} תרגילים</span>' if len(d['ex']) > 1 else '<span class="x">תרגיל</span>'
        if d in exams: x = '<span class="x">מבחן</span>'
        if d in projs: x = '<span class="x">פרויקט</span>'
        lab = d.get('lab') or f'פרק {d["num"]}'
        lis.append(f'<li class="{k}" data-id="{e(d["id"])}"><span class="n">{e(lab)}</span><span class="t">{e(d["title"])}</span>{x}<span class="b">{len(d.get("slides", []))} שקופיות</span></li>')
    # -- materials (computed from what is on the site)
    mats = [f'{len(chs)} {unit} במצגות — {slides:,} שקופיות, עם חיפוש בקורס, מסך מלא ותצוגת גלילה']
    if (base / 'pdf').is_dir(): mats.append('PDF של כל פרק להורדה ולהדפסה')
    if nex: mats.append(f'{nex} תרגילים מעשיים עם פתרונות')
    if exams: mats.append(f'{"מבחן לדוגמא" if len(exams) == 1 else str(len(exams)) + " מבחנים לדוגמא"} במבנה הבחינה הרשמית')
    if projs: mats.append('פרויקט גמר עם הנחיות')
    if cid == 'genai':
        mats += ['ספר מסכם לקורס — לקריאה, PDF והדפסה']
    qz = quiz_info(cid)
    if qz: mats.append(f'שאלות חזרה: {qz[1]} שאלות אמריקאיות לכל פרק')
    if (base / 'escape/index.html').exists(): mats.append('חדר בריחה דיגיטלי למשחק עצמאי')
    if (base / 'puzzles/index.html').exists(): mats.append('תשבץ ותשחץ של המונחים המקצועיים')
    dl = base / 'dl'
    if dl.is_dir() and any('Syllabus' in f.name for f in dl.iterdir()): mats.append('הסילבוס הרשמי להורדה')
    if dl.is_dir() and cid == 'sql': mats.append('דף עזר מסכם וקבצי מסד נתונים להתקנה')
    if dl.is_dir() and cid == 'jobs': mats.append('מסמכי קישורים לקבוצות ולאתרי חיפוש עבודה')
    kp = [(len(chs), unit), (f'{slides:,}', 'שקופיות')]
    if nex: kp.append((nex, 'תרגילים'))
    if exams: kp.append((len(exams), 'מבחנים לדוגמא' if len(exams) > 1 else 'מבחן לדוגמא'))
    kph = ''.join(f'<div><b>{a}</b><span>{b}</span></div>' for a, b in kp)
    out = [f'<div class="ic2 wide"><h3><i></i>על הקורס</h3><p data-f="about">{e(cfg["about"])}</p><div class="kp">{kph}</div></div>',
           '<div class="ic2"><h3><i></i>למי הקורס מתאים</h3><ul data-f="audience">' + ''.join(f'<li>{e(a)}</li>' for a in cfg['audience']) + f'</ul><div class="pre"><b>דרישות קדם:</b> <span data-f="prereq">{e(cfg["prereq"])}</span></div></div>',
           '<div class="ic2"><h3><i></i>מה לומדים</h3><ul class="ok2" data-f="goals">' + ''.join(f'<li>{e(a)}</li>' for a in cfg['goals']) + '</ul></div>',
           f'<div class="ic2 wide"><h3><i></i>מבנה הקורס</h3><ul class="chl">{"".join(lis)}</ul><p class="mu" style="margin:10px 0 0">לחיצה על פרק פותחת אותו.</p></div>',
           '<div class="ic2"><h3><i></i>מה כלול באתר</h3><ul class="ok2">' + ''.join(f'<li>{e(a)}</li>' for a in mats) + '</ul></div>']
    ex = INFO['exams'].get(cfg.get('exam') or '')
    if ex:
        src = INFO['exams_source']
        pct = round(100 * ex['pass'] / ex['pts'])
        out.append(f'<div class="ic2"><h3><i></i>בחינת ההסמכה · <bdi dir="ltr">{e(ex["name"])}</bdi></h3><div class="kp">'
                   f'<div><b>{ex["q"]}</b><span>שאלות אמריקאיות</span></div><div><b>{ex["pts"]}</b><span>נקודות</span></div>'
                   f'<div><b>{ex["pass"]}</b><span>לעבור ({pct}%)</span></div><div><b>{ex["min"]}</b><span>דקות</span></div></div>'
                   f'<p class="mu">למי שנבחן שלא בשפת האם — {ex["ext"]} דקות (תוספת 25%). חלק מהשאלות שוות יותר מנקודה אחת. '
                   f'המקור: <a href="{e(src["url"])}" target="_blank" rel="noopener">{e(src["label"])}</a>.</p></div>')
    out.append('<div class="ic2"><h3><i></i>שאלות, מועדים והרשמה</h3><p>לשאלות על הקורס, על הגישה לחומרים או על ההרשמה לבחינה — אפשר לפנות לניצן.</p>'
               '<a class="wa2" href="https://wa.me/972526718757" target="_blank" rel="noopener">וואטסאפ לניצן</a></div>')
    tabs = (f'<nav class="ctabs" role="tablist" aria-label="תצוגת הקורס"><button type="button" role="tab" id="ctC" aria-selected="true">{TAB_ICONS[0]}פרקי הקורס</button>'
            f'<button type="button" role="tab" id="ctI" aria-selected="false">{TAB_ICONS[1]}מידע על הקורס</button></nav>')
    return f'<!--info-->{tabs}\n    <section id="cinfo" aria-label="מידע על הקורס"><div class="ig">\n      ' + '\n      '.join(out) + f'\n    </div></section>\n    {INFO_JS}<!--/info-->\n    '

def strip(src):
    src = re.sub(r'/\*aux\*/.*?/\*/aux\*/\n?', '', src, flags=re.S)
    src = re.sub(r'/\*info\*/.*?/\*/info\*/\n?', '', src, flags=re.S)
    src = re.sub(r'/\*wide\*/.*?/\*/wide\*/\n?', '', src, flags=re.S)
    src = re.sub(r'<!--info-->.*?<!--/info-->\n?\s*', '', src, flags=re.S)
    src = re.sub(r'\.aux\{margin-bottom:34px\}.*?\.ax \.acts a\.pri\{[^}]*\}\n', '', src, flags=re.S)  # legacy (unmarked) css
    src = re.sub(r'<section class="aux".*?</section>\n\s*(<script>(?:\(async\(\)=>\{const A=window.NGQAAuth,c=document.getElementById\(\'recCard\'\)|/\* v3\.13 site settings).*?</script>\n\s*)?', '', src, flags=re.S)
    return src

def apply(cid):
    p = ROOT / 'site/courses' / cid / 'index.html'
    src = strip(p.read_text(encoding='utf-8'))
    body = cards(cid)
    inf = info_html(cid)
    if inf:
        src = src.replace('.hsr{display:flex', INFO_CSS + '\n.hsr{display:flex', 1)
    src = src.replace('.hsr{display:flex', WIDE_CSS + '\n.hsr{display:flex', 1)
    if body:
        src = src.replace('.hsr{display:flex', CSS + '\n.hsr{display:flex', 1)
        sec = f'<section class="aux" aria-labelledby="auxh"><h2 id="auxh">חומרי עזר</h2><div class="auxg">\n{body}\n    </div></section>\n    '
        sec += REC_JS.replace('__C__', cid) + '\n    '
        m = re.search(r'<main class="band"><div class="wrap">\s*', src)
        assert m, cid
        src = src[:m.end()] + sec + src[m.end():]
    if inf:
        m = re.search(r'<main class="band"><div class="wrap">\s*', src)
        src = src[:m.end()] + inf + src[m.end():]
    p.write_text(src, encoding='utf-8')
    print(cid, body.count('class="ax"'), 'cards')

if __name__ == '__main__':
    for c in (sys.argv[1:] or ['genai', 'ctfl', 'sql', 'ste', 'ai', 'mat', 'jobs']):
        apply(c)
