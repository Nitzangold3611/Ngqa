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

def cards(cid):
    out = []
    def card(kind, title, text, links):
        acts = ''.join(f'<a{" class=\"pri\"" if i == 0 else ""} href="{h}"{x}>{t}</a>' for i, (t, h, x) in enumerate(links))
        out.append(f'      <div class="ax"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">{ICON[kind]}</svg></span><div><b>{title}</b><p>{text}</p><div class="acts">{acts}</div></div></div>')
    if cid == 'genai':
        card('book', 'ספר מסכם לקורס', 'כל החומר לפי פרקים ותתי-פרקים, עם מושגים והסברים בסוף כל פרק וסיכום במילים פשוטות.',
             [('קריאה', 'book/', ''), ('הורדת PDF', 'pdf/NGQA-CT-GenAI-book.pdf', ' download="NGQA-CT-GenAI-book.pdf"'), ('הדפסה', 'book/?print=1', ' target="_blank" rel="noopener"')])
        out.append('''      <div class="ax" id="recCard"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">''' + ICON['rec'] + '''</svg></span><div><b>שיעורים מוקלטים</b><p id="recTxt">השיעורים המוקלטים של הקורס, לפי פרקים.</p><div class="acts" id="recActs"><a class="pri" href="lessons/">לשיעורים</a></div></div></div>''')
        card('quiz', 'שאלות חזרה בין פרק לפרק', '20 שאלות אמריקאיות לכל פרק, עם הסבר לכל תשובה, ציון ותרגול חוזר של הטעויות. אפשר גם להדפיס.',
             [(f'פרק {n}', f'quiz/#ch{n}', '') for n in range(1, 6)])
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
.ax.lockd .ic{background:#6b6a8a}.ax.flash{outline:3px solid var(--orange);outline-offset:3px}
/*/aux*/'''

# recorded-lessons card: locked look + explanation for users without the "<course>-rec" level (v3.11)
REC_JS = '''<script>(async()=>{const A=window.NGQAAuth,c=document.getElementById('recCard');if(!A||!c)return;
  const i=A.info(await A.session()),q=new URLSearchParams(location.search),nr=q.get('norec');
  if(A.canRec(i,'__C__')){const e=A.recEnd(i,'__C__');if(e&&!i.admin)document.getElementById('recTxt').textContent+=' הגישה לשיעורים בתוקף עד '+A.dmy(e)+'.';return}
  c.classList.add('lockd');
  const ended=nr&&/^\\d{4}-\\d{2}-\\d{2}$/.test(nr);
  document.getElementById('recTxt').textContent=ended?'הגישה שלך לשיעורים המוקלטים הסתיימה ב-'+A.dmy(nr)+'. להארכה פנו לניצן.':'השיעורים המוקלטים לא כלולים בגישה שלך. לפרטים ולהוספה לגישה — פנו לניצן.';
  document.getElementById('recActs').innerHTML='<a class="pri" href="https://wa.me/972526718757" target="_blank" rel="noopener">וואטסאפ לניצן</a>';
  c.querySelector('b').textContent='שיעורים מוקלטים 🔒';
  if(nr!==null){history.replaceState(null,'',location.pathname+location.hash);c.scrollIntoView({block:'center'});c.classList.add('flash')}})();
/* "שיעורים מוקלטים" tab in the chapter viewer, next to מצגת / תרגילים (hash #<chapter>/rec) */
(()=>{const init=()=>{const S=document.getElementById('tabS'),E=document.getElementById('tabE');if(!S||!E||document.getElementById('tabR'))return;
  const st=document.createElement('style');st.textContent='#recview{display:none;max-width:980px;margin:16px auto 40px;padding:0 max(3vw,12px)}body.m-rec #recview{display:block}body.m-rec .stage,body.m-rec .rail,body.m-rec #feed,body.m-rec .fpill,body.m-rec #exlist,body.m-rec #exview{display:none!important}body.m-rec #fs,body.m-rec #prt,body.m-rec #tocb{display:none}#recview .rc{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px;text-align:center}#recview .rc h2{margin:0 0 8px}#recview .rc p{color:var(--mute);margin:6px auto 14px;max-width:56ch}#recview .rc a{display:inline-block;background:var(--orange);color:#fff;border-radius:10px;padding:8px 18px;font-weight:700;text-decoration:none}';
  document.head.appendChild(st);
  const R=document.createElement('button');R.type='button';R.setAttribute('role','tab');R.id='tabR';R.setAttribute('aria-selected','false');
  R.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="14" height="14" rx="2"/><path d="M17 10l4-2v8l-4-2z"/></svg>שיעורים מוקלטים';E.after(R);
  const pane=document.createElement('section');pane.id='recview';pane.setAttribute('aria-label','שיעורים מוקלטים');(document.getElementById('exview')||E).after(pane);
  const chOf=()=>(location.hash.match(/^#([^/]+)/)||[])[1];
  R.onclick=()=>{const c=chOf();if(c)location.hash=c+'/rec'};
  async function sync(){const m=location.hash.match(/^#([^/]+)\\/rec$/);document.body.classList.toggle('m-rec',!!m);R.setAttribute('aria-selected',!!m);if(!m)return;
    S.setAttribute('aria-selected',false);E.setAttribute('aria-selected',false);window.scrollTo(0,0);
    const A=window.NGQAAuth,i=A&&A.info(await A.session()),ok=A&&A.canRec(i,'__C__'),n=(m[1].match(/\\d+/)||[''])[0];
    pane.innerHTML=ok?'<div class="rc"><h2>שיעורים מוקלטים'+(n?' · פרק '+n:'')+'</h2><p>השיעורים המוקלטים של הפרק הזה יעלו כאן בקרוב — עם נגן, סימון "נצפה" והמשך מהמקום שבו עצרת.</p><a href="lessons/">לכל השיעורים המוקלטים</a></div>'
      :'<div class="rc"><h2>שיעורים מוקלטים 🔒</h2><p>השיעורים המוקלטים לא כלולים בגישה שלך. לפרטים ולהוספה לגישה — פנו לניצן.</p><a href="https://wa.me/972526718757" target="_blank" rel="noopener">וואטסאפ לניצן</a></div>'}
  addEventListener('hashchange',()=>setTimeout(sync,0));setTimeout(sync,0)};
  document.readyState==='loading'?document.addEventListener('DOMContentLoaded',init):init()})();</script>'''

def strip(src):
    src = re.sub(r'/\*aux\*/.*?/\*/aux\*/\n?', '', src, flags=re.S)
    src = re.sub(r'\.aux\{margin-bottom:34px\}.*?\.ax \.acts a\.pri\{[^}]*\}\n', '', src, flags=re.S)  # legacy (unmarked) css
    src = re.sub(r'<section class="aux".*?</section>\n\s*(<script>\(async\(\)=>\{const A=window.NGQAAuth,c=document.getElementById\(\'recCard\'\).*?</script>\n\s*)?', '', src, flags=re.S)
    return src

def apply(cid):
    p = ROOT / 'site/courses' / cid / 'index.html'
    src = strip(p.read_text(encoding='utf-8'))
    body = cards(cid)
    if body:
        src = src.replace('.hsr{display:flex', CSS + '\n.hsr{display:flex', 1)
        sec = f'<section class="aux" aria-labelledby="auxh"><h2 id="auxh">חומרי עזר</h2><div class="auxg">\n{body}\n    </div></section>\n    '
        if 'id="recCard"' in body: sec += REC_JS.replace('__C__', cid) + '\n    '
        m = re.search(r'<main class="band"><div class="wrap">\s*', src)
        assert m, cid
        src = src[:m.end()] + sec + src[m.end():]
    p.write_text(src, encoding='utf-8')
    print(cid, body.count('class="ax"'), 'cards')

if __name__ == '__main__':
    for c in (sys.argv[1:] or ['genai', 'ctfl', 'sql', 'ste', 'ai', 'mat', 'jobs']):
        apply(c)
