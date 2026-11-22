"""Add the sample-exam deck (chapter 6) to site/courses/genai without rebuilding chapters 1-5.
usage: add_exam.py VERSION DATE"""
import json, glob, os, re, zipfile, subprocess, shutil, sys
from PIL import Image
V, DATE = sys.argv[1], sys.argv[2]
SRC = '/home/claude/gx/out'; OUT = '/home/claude/ngqa/site/courses/genai'
S = glob.glob('/root/.claude/skills/synced/*/pptx')[0]
BACK = {'x': 86.12, 'y': 94.67, 'w': 11.62, 'h': 4.0}
N = 6; n = 6
pp = f'{SRC}/ch6.pptx'; z = zipfile.ZipFile(pp); site = json.load(open(f'{SRC}/ch6.site.json'))
pres = z.read('ppt/presentation.xml').decode(); rels = z.read('ppt/_rels/presentation.xml.rels').decode()
m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1) for r in re.findall(r'<Relationship [^>]*>', rels)}
order = [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]
out = subprocess.run(['python3', S + '/scripts/slide_text.py', pp], capture_output=True, text=True).stdout
parts = re.split(r'<!-- Slide number: (\d+) -->', out)[1:]
texts = {int(a): b.split('### Notes:')[0] for a, b in zip(parts[0::2], parts[1::2])}
tmp = '/tmp/gxhr6'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=92', '-scale-to-x', '1600', '-scale-to-y', '-1', f'{SRC}/ch6.pdf', tmp + '/s'], check=True)
fs = sorted(glob.glob(tmp + '/s-*.jpg')); assert len(fs) == len(order)
slides = []; ims = []
for i, (f, target) in enumerate(zip(fs, order), 1):
    im = Image.open(f).convert('RGB'); w = 1440; h = round(im.height * w / im.width); ims.append(im.resize((w, h), Image.LANCZOS))
    lines = [l.strip('# |').strip() for l in texts.get(i, '').splitlines() if l.strip() and not l.strip().startswith('![')]
    lay = z.read(f'ppt/slides/_rels/{os.path.basename(target)}.rels').decode()
    links = []
    if i == 2: links += [dict(l) for l in site['toc_links']]
    if 'slideLayout2' in lay and i != 2: links.append(dict(BACK, slide=2))
    s = {'title': (lines[0] if lines else '')[:120], 'text': ' '.join(lines)[:700]}
    if links: s['links'] = links
    slides.append(s)
for f in glob.glob(f'{OUT}/sp/ch6_*.jpg'): os.remove(f)
for g in range(0, len(ims), N):
    c = Image.new('RGB', (w, h * N), 'white')
    for k, im in enumerate(ims[g:g + N]): c.paste(im, (0, k * h))
    name = f'sp/ch6_{g // N:02d}.jpg'; c.save(f'{OUT}/{name}', quality=80, optimize=True, progressive=True)
    for k in range(len(ims[g:g + N])): slides[g + k]['img'] = name + '?v=1'; slides[g + k]['k'] = k
ims[0].resize((960, round(960 * h / w)), Image.LANCZOS).save(f'{OUT}/img/ch6.jpg', quality=82)
shutil.copy(f'{SRC}/ch6.pdf', f'{OUT}/pdf/NGQA-CT-GenAI-ch6.pdf')
decks = [d for d in json.load(open(f'{OUT}/decks.json')) if d['num'] != 6]
for d in decks: d['lab'] = f"פרק {d['num']}"
decks.append({'id': 'ch6', 'num': 6, 'lab': 'מבחן', 'title': 'מבחן לדוגמא — 40 שאלות', 'sub': 'Sample Exam · שקף שאלה ושקף תשובה',
              'cover': 'img/ch6.jpg?v=1', 'ratio': f'{w}/{h}', 'per': N, 'toc': site['toc'], 'ex': [], 'slides': slides})
json.dump(decks, open(f'{OUT}/decks.json', 'w'), ensure_ascii=False)
# index.html: 6 chapters + chapter labels
p = f'{OUT}/index.html'; src = open(p, encoding='utf-8').read()
src = src.replace('const CHAPTERS=[1,2,3,4,5].map(n=>({num:n}));', 'const CHAPTERS=[1,2,3,4,5,6].map(n=>({num:n}));')
src = src.replace("`NGQA CT-GenAI פרק ${cur.num}.pdf`", "`NGQA CT-GenAI ${cur.lab}.pdf`")
for v in ('cur', 'd', 'n'):
    src = src.replace(f'פרק ${{{v}.num}} · ', f'${{{v}.lab}} · ').replace(f'פרק ${{{v}.num}}: ', f'${{{v}.lab}}: ')
src = src.replace('פרק ${cur.num} | NGQA', '${cur.lab} | NGQA').replace("lab:`מעבר לפרק ${n.num}: ${n.title}`", "lab:`מעבר ל${n.lab}: ${n.title}`")
src = re.sub(r'<span class="ver">גרסה <bdi dir="ltr">[^<]*</bdi></span>', f'<span class="ver">גרסה <bdi dir="ltr">v{V} · {DATE}</bdi></span>', src)
open(p, 'w', encoding='utf-8').write(src)
print(len(slides), 'exam slides;', sum(len(d['slides']) for d in decks), 'total')
