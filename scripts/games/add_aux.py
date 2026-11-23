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
/*/aux*/'''

def strip(src):
    src = re.sub(r'/\*aux\*/.*?/\*/aux\*/\n?', '', src, flags=re.S)
    src = re.sub(r'\.aux\{margin-bottom:34px\}.*?\.ax \.acts a\.pri\{[^}]*\}\n', '', src, flags=re.S)  # legacy (unmarked) css
    src = re.sub(r'<section class="aux".*?</section>\n\s*', '', src, flags=re.S)
    return src

def apply(cid):
    p = ROOT / 'site/courses' / cid / 'index.html'
    src = strip(p.read_text(encoding='utf-8'))
    body = cards(cid)
    if body:
        src = src.replace('.hsr{display:flex', CSS + '\n.hsr{display:flex', 1)
        sec = f'<section class="aux" aria-labelledby="auxh"><h2 id="auxh">חומרי עזר</h2><div class="auxg">\n{body}\n    </div></section>\n    '
        m = re.search(r'<main class="band"><div class="wrap">\s*', src)
        assert m, cid
        src = src[:m.end()] + sec + src[m.end():]
    p.write_text(src, encoding='utf-8')
    print(cid, body.count('class="ax"'), 'cards')

if __name__ == '__main__':
    for c in (sys.argv[1:] or ['genai', 'ctfl', 'sql', 'ste', 'ai', 'mat', 'jobs']):
        apply(c)
