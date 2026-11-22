"""Add the four CTFL sample-exam decks (A–D = chapters 7–10) to site/courses/ctfl without rebuilding chapters 1-6.
usage: add_exams.py VERSION DATE   (decks are built in /home/claude/cfx/out from ctfl/exams)"""
import json, glob, os, re, zipfile, subprocess, shutil, sys
from PIL import Image
V, DATE = sys.argv[1], sys.argv[2]
SRC = '/home/claude/cfx/out'; OUT = '/home/claude/ngqa/site/courses/ctfl'
S = glob.glob('/root/.claude/skills/synced/*/pptx')[0]
BACK = {'x': 86.12, 'y': 94.67, 'w': 11.62, 'h': 4.0}
N = 6
EX = {7: 'A', 8: 'B', 9: 'C', 10: 'D'}
CTL = re.compile('[‎‏‪-‮]')
decks = [d for d in json.load(open(f'{OUT}/decks.json')) if d['num'] <= 6]
for d in decks: d['lab'] = f"פרק {d['num']}"
for n, L in EX.items():
    pp = f'{SRC}/ch{n}.pptx'; z = zipfile.ZipFile(pp); site = json.load(open(f'{SRC}/ch{n}.site.json'))
    pres = z.read('ppt/presentation.xml').decode(); rels = z.read('ppt/_rels/presentation.xml.rels').decode()
    m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1) for r in re.findall(r'<Relationship [^>]*>', rels)}
    order = [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]
    out = subprocess.run(['python3', S + '/scripts/slide_text.py', pp], capture_output=True, text=True).stdout
    parts = re.split(r'<!-- Slide number: (\d+) -->', out)[1:]
    texts = {int(a): b.split('### Notes:')[0] for a, b in zip(parts[0::2], parts[1::2])}
    tmp = f'/tmp/cfhr{n}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=92', '-scale-to-x', '1600', '-scale-to-y', '-1', f'{SRC}/ch{n}.pdf', tmp + '/s'], check=True)
    fs = sorted(glob.glob(tmp + '/s-*.jpg')); assert len(fs) == len(order)
    slides = []; ims = []
    for i, (f, target) in enumerate(zip(fs, order), 1):
        im = Image.open(f).convert('RGB'); w = 1440; h = round(im.height * w / im.width); ims.append(im.resize((w, h), Image.LANCZOS))
        lines = [CTL.sub('', l).strip('# |').strip() for l in texts.get(i, '').splitlines() if l.strip() and not l.strip().startswith('![')]
        lay = z.read(f'ppt/slides/_rels/{os.path.basename(target)}.rels').decode()
        links = []
        if i == 2: links += [dict(l) for l in site['toc_links']]
        if 'slideLayout2' in lay and i != 2: links.append(dict(BACK, slide=2))
        s = {'title': (lines[0] if lines else '')[:120], 'text': ' '.join(lines)[:700]}
        if links: s['links'] = links
        slides.append(s)
    for f in glob.glob(f'{OUT}/sp/ch{n}_*.jpg'): os.remove(f)
    for g in range(0, len(ims), N):
        c = Image.new('RGB', (w, h * N), 'white')
        for k, im in enumerate(ims[g:g + N]): c.paste(im, (0, k * h))
        name = f'sp/ch{n}_{g // N:02d}.jpg'; c.save(f'{OUT}/{name}', quality=80, optimize=True, progressive=True)
        for k in range(len(ims[g:g + N])): slides[g + k]['img'] = name + '?v=1'; slides[g + k]['k'] = k
    ims[0].resize((960, round(960 * h / w)), Image.LANCZOS).save(f'{OUT}/img/ch{n}.jpg', quality=82)
    shutil.copy(f'{SRC}/ch{n}.pdf', f'{OUT}/pdf/NGQA-ISTQB-ch{n}.pdf')
    decks.append({'id': f'ch{n}', 'num': n, 'lab': f'מבחן {L}', 'title': f'מבחן לדוגמא {L}', 'sub': f'Sample Exam {L} · 40 שאלות',
                  'cover': f'img/ch{n}.jpg?v=1', 'ratio': f'{w}/{h}', 'per': N, 'toc': site['toc'], 'slides': slides})
json.dump(decks, open(f'{OUT}/decks.json', 'w'), ensure_ascii=False)

p = f'{OUT}/index.html'; src = open(p, encoding='utf-8').read()
if "num:7" not in src:
    src = src.replace(" {num:6,title:'כלי בדיקה',sub:'Test Tools'}];",
        " {num:6,title:'כלי בדיקה',sub:'Test Tools'},\n" +
        ",\n".join(f" {{num:{n},badge:'{L}',title:'מבחן לדוגמא {L}',sub:'Sample Exam {L} · שקף שאלה ושקף תשובה'}}" for n, L in EX.items()) + "];")
    assert "num:10" in src
src = src.replace('<span class="num">${c.num}</span>', '<span class="num">${c.badge||c.num}</span>')
for v in ('cur', 'd', 'n'):
    src = src.replace(f'פרק ${{{v}.num}} · ', f'${{{v}.lab}} · ').replace(f'פרק ${{{v}.num}}: ', f'${{{v}.lab}}: ')
src = src.replace('NGQA ISTQB פרק ${d.num}.pdf', 'NGQA ISTQB ${d.lab}.pdf').replace('NGQA ISTQB פרק ${cur.num}.pdf', 'NGQA ISTQB ${cur.lab}.pdf')
src = src.replace('סיימתם את פרק ${cur.num}', 'סיימתם את ${cur.lab}').replace('פרק ${cur.num} | NGQA', '${cur.lab} | NGQA')
src = src.replace("lab:`מעבר לפרק ${n.num}: ${n.title}`", "lab:`מעבר ל${n.lab}: ${n.title}`")
src = re.sub(r'<span class="ver">גרסה <bdi dir="ltr">[^<]*</bdi></span>', f'<span class="ver">גרסה <bdi dir="ltr">v{V} · {DATE}</bdi></span>', src)
open(p, 'w', encoding='utf-8').write(src)
print(sum(len(d['slides']) for d in decks), 'slides total;', len(decks), 'decks')
