import json, glob, os, re, zipfile, subprocess, shutil, sys
from PIL import Image
G = '/home/claude/genai'; OUT = G + '/site'; CTFL = '/home/claude/work/site'
S = glob.glob('/root/.claude/skills/synced/*/pptx')[0]
V = sys.argv[1] if len(sys.argv) > 1 else '1'
CH = json.load(open(G + '/chapters.json'))
SUB = {1: 'Introduction to GenAI for Software Testing', 2: 'Prompt Engineering for Effective Software Testing',
       3: 'Managing Risks of Generative AI in Software Testing', 4: 'LLM-Powered Test Infrastructure',
       5: 'Deploying and Integrating GenAI in Test Organizations'}
EXD = '/mnt/user-data/uploads/CT-GenAI/תרגילים מעשיים/'
# id, chapter, label, level, title, pdf
EX = [
 ('2.1.1', 2, 'HO-2.1.1', 'H0', 'צפייה וניתוח רכיבי פרומפט', 'פרק מס 2/תרגיל מעשי 2.1.1 צפייה וניתוח רכיבי פרומפט.pdf'),
 ('2.1.2a', 2, 'HO-2.1.2a', 'H0', 'צפייה ודיון בשרשור פרומפטים, Few-Shot Prompting ו-Meta Prompting', 'פרק מס 2/תרגיל מעשי 2.1.2a שרשור פרומפטים.pdf'),
 ('2.1.2b', 2, 'HO-2.1.2b', 'H1', 'זיהוי טכניקות הנדסת פרומפטים', 'פרק מס 2/HO_2_1_2b_זיהוי_טכניקות_הנדסת_פרומפטים_RTL_2002e477a55b4c09a4dab528760f31e9.pdf'),
 ('2.2.1a', 2, 'HO-2.2.1a', 'H2', 'יצירת פרומפטים מולטימודליים מובנים ליצירת קריטריוני קבלה מתוך User Story ו-Wireframe', 'פרק מס 2/HO_2_2_1a_פרומפטים_מולטימודליים_Wireframe_RTL_5eb0251a0bbd4d87a8f58b8e621452a2.pdf'),
 ('2.2.2', 2, 'HO-2.2.2', 'H2', 'יצירת מקרי בדיקה בסגנון Gherkin באמצעות Few-Shot Prompting', 'פרק מס 2/HO_2_2_2_Gherkin_Few_Shot.pdf'),
 ('2.2.2a', 2, 'HO-2.2.2a', 'H2', 'יצירת מקרי בדיקה פונקציונליים מסיפורי משתמש באמצעות בינה מלאכותית', 'פרק מס 2/HO_2_2_2a_מקרי_בדיקה_פונקציונליים.pdf'),
 ('2.2.2c', 2, 'HO-2.2.2c', '', 'תעדוף מקרי בדיקה באמצעות בינה מלאכותית יוצרת', 'פרק מס 2/תעדוף מקרי בדיקה 222c.pdf'),
 ('2.2.3', 2, 'HO-2.2.3', 'H2', 'כתיבת פרומפטים מובנים לניתוח דוחות בדיקה בהקשר של בדיקות רגרסיה', 'פרק מס 3/תרגיל_מעשי_2_2_3_ניתוח_דוחות_רגרסיה.pdf'),
 ('2.2.3p', 2, 'HO-2.2.3', 'H2', 'תעדוף מקרי בדיקה באמצעות שרשור פרומפטים, סיכונים ותלויות', 'פרק מס 2/תרגיל מעשי 2.2.3 שרשור מקרי בדיקה העזרת פרומפטים.pdf'),
 ('2.2.3a', 2, 'HO-2.2.3a', 'H2', 'יצירה וניהול של סקריפטי בדיקה מבוססי מילות מפתח בעזרת Few-Shot Prompting', 'פרק מס 2/HO_2_2_3a_Keyword_Driven_Tests.pdf'),
 ('2.2.4', 2, 'HO-2.2.4', 'H0', 'צפייה במדדי ניטור בדיקות שנוצרו באמצעות בינה מלאכותית מתוך נתוני בדיקה', 'פרק מס 2/HO_2_2_4_מדדי_ניטור_בדיקות_GenAI.pdf'),
 ('2.2.5', 2, 'HO-2.2.5', 'H1', 'בחירת טכניקות פרומפטינג מתאימות להקשר עבור משימות בדיקה נתונות', 'פרק מס 2/HO_2_2_5_בחירת_טכניקות_פרומפטינג.pdf'),
 ('2.3.1', 2, 'HO-2.3.1', 'H0', 'הערכת תוצרי GenAI במשימות בדיקות תוכנה', 'פרק מס 2/HO_2_3_1_הערכת_תוצרי_GenA.pdf'),
 ('3.1.2', 3, 'HO-3.1.2', 'H1', 'התנסות בהזיות של בינה מלאכותית יוצרת בהקשר של משימת בדיקות תוכנה', 'פרק מס 3/HO_3_1_2_Hallucinations_GenA.pdf'),
 ('4.1.2', 4, 'HO-4.1.2', 'H1', 'התנסות ביצירה מונחית אחזור (RAG) עבור משימת בדיקה נתונה', 'פרק מס 4/HO_4_1_2_RAG_Testing.pdf'),
 ('4.1.3', 4, 'HO-4.1.3', 'H0', 'צפייה כיצד סוכן מבוסס מודל שפה גדול מסייע באוטומציה של משימת בדיקה חוזרת', 'פרק מס 4/HO_4_1_3_LLM_Agent_Testing.pdf'),
 ('4.2.1', 4, 'HO-4.2.1', 'H0', 'צפייה בדוגמה לתהליך כיוונון עדין עבור משימת בדיקה ומודל שפה', 'פרק מס 4/HO_4_2_1_Fine_Tuning_Testing.pdf'),
 ('5.1.3', 5, 'HO-5.1.3', 'H1', 'הערכת העלויות החוזרות של שימוש בבינה מלאכותית יוצרת עבור משימת בדיקה נתונה', 'פרק מס 5/HO_5_1_3_GenAI_Recurring_Costs.pdf'),
]
for d in ('sp', 'img', 'pdf', 'ex'):
    shutil.rmtree(f'{OUT}/{d}', ignore_errors=True); os.makedirs(f'{OUT}/{d}')
for f in ('logo.png', 'favicon.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png', '404.html'):
    shutil.copy(f'{CTFL}/{f}', OUT)
BACK = {'x': 86.12, 'y': 94.67, 'w': 11.62, 'h': 4.0}
N = 6; decks = []
for n in range(1, 6):
    pp = f'{G}/out/g{n}.pptx'; z = zipfile.ZipFile(pp)
    site = json.load(open(f'{G}/out/g{n}.site.json'))
    pres = z.read('ppt/presentation.xml').decode()
    rels = z.read('ppt/_rels/presentation.xml.rels').decode()
    m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1) for r in re.findall(r'<Relationship [^>]*>', rels)}
    order = [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]
    out = subprocess.run(['python3', S + '/scripts/slide_text.py', pp], capture_output=True, text=True).stdout
    parts = re.split(r'<!-- Slide number: (\d+) -->', out)[1:]
    texts = {int(a): b.split('### Notes:')[0] for a, b in zip(parts[0::2], parts[1::2])}
    tmp = f'/tmp/hr{n}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=92', '-scale-to-x', '1600', '-scale-to-y', '-1', f'{G}/out/r{n}/g{n}.pdf', tmp + '/s'], check=True)
    fs = sorted(glob.glob(tmp + '/s-*.jpg')); assert len(fs) == len(order), (n, len(fs), len(order))
    exlinks = {}
    for eid, boxes in site.get('ex', {}).items():
        for b in boxes:
            exlinks.setdefault(b['slide'], []).append({'x': b['x'], 'y': b['y'], 'w': b['w'], 'h': b['h'], 'ex': eid})
    slides = []; ims = []
    for i, (f, target) in enumerate(zip(fs, order), 1):
        im = Image.open(f).convert('RGB'); w = 1440; h = round(im.height * w / im.width); ims.append(im.resize((w, h), Image.LANCZOS))
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
        if links: s['links'] = links
        slides.append(s)
    for g in range(0, len(ims), N):
        c = Image.new('RGB', (w, h * N), 'white')
        for k, im in enumerate(ims[g:g + N]): c.paste(im, (0, k * h))
        name = f'sp/ch{n}_{g // N:02d}.jpg'; c.save(f'{OUT}/{name}', quality=80, optimize=True, progressive=True)
        for k in range(len(ims[g:g + N])): slides[g + k]['img'] = name + '?v=' + V; slides[g + k]['k'] = k
    ims[0].resize((960, round(960 * h / w)), Image.LANCZOS).save(f'{OUT}/img/ch{n}.jpg', quality=82)
    shutil.copy(f'{G}/out/r{n}/g{n}.pdf', f'{OUT}/pdf/NGQA-CT-GenAI-ch{n}.pdf')
    # exercises of this chapter
    exs = []
    for eid, ch, lab, lvl, title, pdf in EX:
        if ch != n: continue
        src = EXD + pdf; d = f'{OUT}/ex/{eid}'; os.makedirs(d)
        shutil.copy(src, f'{OUT}/ex/{eid}.pdf')
        subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=85', '-scale-to-x', '1240', '-scale-to-y', '-1', src, d + '/p'], check=True)
        pages = sorted(glob.glob(d + '/p-*.jpg'))
        for k, p in enumerate(pages, 1): os.rename(p, f'{d}/{k}.jpg')
        sz = Image.open(f'{d}/1.jpg').size
        sl = sorted(b['slide'] for b in site.get('ex', {}).get(eid, []))
        exs.append({'id': eid, 'label': lab, 'lvl': lvl, 'title': title, 'pages': len(pages), 'ratio': f'{sz[0]}/{sz[1]}',
                    'slides': sl})
    decks.append({'id': f'ch{n}', 'num': n, 'title': CH[str(n)], 'sub': SUB[n], 'cover': f'img/ch{n}.jpg?v={V}', 'ratio': f'{w}/{h}',
                  'per': N, 'toc': site['toc'], 'ex': exs, 'slides': slides})
json.dump(decks, open(f'{OUT}/decks.json', 'w'), ensure_ascii=False)
print(sum(len(d['slides']) for d in decks), 'slides', sum(len(d['ex']) for d in decks), 'exercises')
