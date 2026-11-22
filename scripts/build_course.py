#!/usr/bin/env python3
"""Build site/courses/<course> from generated decks.
usage: build_course.py COURSE VERSION DATE  (config: scripts/course_<COURSE>.json)"""
import json, glob, os, re, zipfile, subprocess, shutil, sys
from PIL import Image

C = sys.argv[1]
V = sys.argv[2] if len(sys.argv) > 2 else '1.0'
DATE = sys.argv[3] if len(sys.argv) > 3 else ''
CFG = json.load(open(os.path.dirname(os.path.abspath(__file__)) + f'/course_{C}.json'))
NAME = CFG['name']
ST = f'/home/claude/{C}'
REPO = '/home/claude/ngqa'
OUT = REPO + f'/site/courses/{C}'
GEN = REPO + '/site/courses/genai'
DL = f'/tmp/{C}dl'
S = glob.glob('/root/.claude/skills/synced/*/pptx')[0]
CH = {int(k): v for k, v in json.load(open(ST + '/chapters.json')).items()}
NCH = CFG['nch']
for k, v in CFG.get('chx', {}).items():
    CH[int(k)] = v
SUB = {int(k): v for k, v in CFG['sub'].items()}
LAB = {n: f'פרק {n}' for n in range(1, NCH + 1)}
for k, v in CFG.get('lab', {}).items():
    LAB[int(k)] = v

for d in ('sp', 'img', 'pdf', 'dl'):
    shutil.rmtree(f'{OUT}/{d}', ignore_errors=True)
    os.makedirs(f'{OUT}/{d}')
for f in ('logo.png', 'favicon.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png'):
    shutil.copy(f'{GEN}/{f}', OUT)
for f in os.listdir(DL):
    if f.endswith(('.pdf', '.docx')):
        shutil.copy(f'{DL}/{f}', f'{OUT}/dl/{f}')
BACK = {'x': 86.12, 'y': 94.67, 'w': 11.62, 'h': 4.0}
N = 6
decks = []
total = 0
for n in range(1, NCH + 1):
    pp = f'{ST}/out/ch{n}.pptx'
    z = zipfile.ZipFile(pp)
    site = json.load(open(f'{ST}/out/ch{n}.site.json'))
    pres = z.read('ppt/presentation.xml').decode()
    rels = z.read('ppt/_rels/presentation.xml.rels').decode()
    m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1)
         for r in re.findall(r'<Relationship [^>]*>', rels)}
    order = [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]
    out = subprocess.run(['python3', S + '/scripts/slide_text.py', pp], capture_output=True, text=True).stdout
    parts = re.split(r'<!-- Slide number: (\d+) -->', out)[1:]
    texts = {int(a): b.split('### Notes:')[0] for a, b in zip(parts[0::2], parts[1::2])}
    tmp = f'/tmp/{C}hr{n}'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    subprocess.run(['pdftoppm', '-jpeg', '-jpegopt', 'quality=92', '-scale-to-x', '1600', '-scale-to-y', '-1',
                    f'{ST}/out/ch{n}.pdf', tmp + '/s'], check=True, stderr=subprocess.DEVNULL)
    fs = sorted(glob.glob(tmp + '/s-*.jpg'))
    assert len(fs) == len(order), (n, len(fs), len(order))
    slides, ims = [], []
    for i, (f, target) in enumerate(zip(fs, order), 1):
        im = Image.open(f).convert('RGB')
        w = 1440
        h = round(im.height * w / im.width)
        ims.append(im.resize((w, h), Image.LANCZOS))
        lines = [l.strip('# |').strip() for l in texts.get(i, '').splitlines() if l.strip() and not l.strip().startswith('![')]
        lay = z.read(f'ppt/slides/_rels/{os.path.basename(target)}.rels').decode()
        links = []
        if i == 2:
            links += [dict(l) for l in site['toc_links']]
        if 'slideLayout2' in lay and i != 2:
            links.append(dict(BACK, slide=2))
        s = {'title': (lines[0] if lines else '')[:120], 'text': ' '.join(lines)[:700]}
        if links:
            s['links'] = links
        slides.append(s)
    total += len(slides)
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
    shutil.copy(f'{ST}/out/ch{n}.pdf', f'{OUT}/pdf/NGQA-{NAME}-ch{n}.pdf')
    decks.append({'id': f'ch{n}', 'num': n, 'lab': LAB[n], 'title': CH[n], 'sub': SUB[n], 'cover': f'img/ch{n}.jpg?v={V}',
                  'ratio': f'{w}/{h}', 'per': N, 'toc': site['toc'], 'ex': [], 'slides': slides})
json.dump(decks, open(f'{OUT}/decks.json', 'w'), ensure_ascii=False)

# ---------------------------------------------------------------- index (from the CT-GenAI page)
src = open(f'{GEN}/index.html', encoding='utf-8').read()
src = re.sub(r'const CHAPTERS=\[[\d,]+\]\.map', 'const CHAPTERS=[1,2,3,4,5].map', src, count=1)
rep = [
    ("NGQAAuth.guard('genai')", f"NGQAAuth.guard('{C}')"),
    ("const COURSE='genai';", f"const COURSE='{C}';"),
    ('<title>NGQA · CT-GenAI</title>', f'<title>NGQA · {NAME}</title>'),
    ("document.title='NGQA · CT-GenAI'", f"document.title='NGQA · {NAME}'"),
    ('const CHAPTERS=[1,2,3,4,5].map(n=>({num:n}));', f'const CHAPTERS={list(range(1, NCH + 1))}.map(n=>({{num:n}}));'),
    ("pdf/NGQA-CT-GenAI-ch${cur.num}.pdf", f"pdf/NGQA-{NAME}-ch${{cur.num}}.pdf"),
    (("`NGQA CT-GenAI פרק ${cur.num}.pdf`", "`NGQA CT-GenAI ${cur.lab}.pdf`"), f"`NGQA {NAME} ${{cur.lab}}.pdf`"),
    ("${d.ex.length?` · ${d.ex.length} תרגילים`:''}", ""),
]
for a, b in rep:
    a = next((x for x in (a if isinstance(a, tuple) else (a,)) if x in src), a)
    assert isinstance(a, str) and a in src, a
    src = src.replace(a, b)
# chapter label ("פרק 3" / "מבחן" / "פרויקט")
for v in ('cur', 'd', 'n'):
    src = src.replace(f'פרק ${{{v}.num}} · ', f'${{{v}.lab}} · ').replace(f'פרק ${{{v}.num}}: ', f'${{{v}.lab}}: ')
src = src.replace('פרק ${cur.num} | NGQA', '${cur.lab} | NGQA')
src = re.sub(r'<meta name="description" content="[^"]*">', lambda m: f'<meta name="description" content="{CFG["desc"]}">', src)
src = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: f'<meta property="og:title" content="NGQA · {NAME}">', src)
src = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: f'<meta property="og:description" content="{CFG["ogdesc"]}">', src)
src = re.sub(r'<span class="tag">[^<]*</span>', lambda m: f'<span class="tag">{CFG["tag"]}</span>', src, count=1)
src = re.sub(r'<h1>[^<]*</h1>', lambda m: f'<h1>{CFG["h1"]}</h1>', src, count=1)
src = re.sub(r'(<div class="in">\s*<div>.*?<h1>.*?</h1>\s*)<p>[^<]*</p>', lambda m: m.group(1) + f'<p>{CFG["lead"]}</p>', src, count=1, flags=re.S)
src = re.sub(r'<span class="ver">גרסה <bdi dir="ltr">[^<]*</bdi></span>',
             f'<span class="ver">גרסה <bdi dir="ltr">v{V} · {DATE}</bdi></span>', src)
boxes = '<div class="xbx">\n'
for b in CFG['boxes']:
    boxes += f'      <a class="xb" href="#ch{b[0]}"><span class="xi" aria-hidden="true">{b[1]}</span><span><b>{b[2]}</b><small>{b[3]}</small></span></a>\n'
boxes += '    </div>\n'
if not CFG['boxes']:
    boxes = ''
boxes += '    <div class="pdocs"><b>' + CFG['pdocs_title'] + '</b>\n'
for d in CFG['docs']:
    att = 'download' if d[0].endswith('.docx') else 'target="_blank" rel="noopener"'
    boxes += f'      <a href="dl/{d[0]}" {att}>{d[1]}</a>\n'
boxes += '    </div>\n    <div class="hsr">'
src = src.replace('<div class="hsr">', boxes, 1)
css = '''.xbx{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:0 0 14px}
.xb{display:flex;gap:14px;align-items:center;background:var(--navy);color:#fff;border-radius:16px;padding:18px 20px;text-decoration:none;border-inline-start:6px solid var(--teal);transition:transform .2s}
.xb+.xb{border-inline-start-color:var(--orange)}.xb:hover{transform:translateY(-2px)}
.xb .xi{font-size:30px;flex:none}.xb b{display:block;font-size:20px}.xb small{color:#c9cbf0;font-size:14px;line-height:1.4;display:block}
.pdocs{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin:0 0 30px}
.pdocs b{color:var(--teal-d);margin-inline-end:6px}
.pdocs a{display:inline-flex;align-items:center;min-height:38px;padding:0 12px;border-radius:10px;background:light-dark(#eafbfa,#13324a);color:inherit;text-decoration:none;font-weight:600;font-size:14.5px}
.pdocs a:hover{background:var(--teal);color:#121133}
#tabE{display:none}
.xbx:has(> :only-child){grid-template-columns:1fr}
@media(max-width:700px){.xbx{grid-template-columns:1fr}}
'''
src = src.replace('/* ---- tabs & exercises (CT-GenAI) ---- */', css + '/* ---- tabs ---- */', 1)
for a, b in CFG.get('terms', []):
    src = src.replace(a, b)
open(f'{OUT}/index.html', 'w', encoding='utf-8').write(src)
print('slides', total)
json.dump({'slides': total}, open(f'/tmp/{C}_total.json', 'w'))
