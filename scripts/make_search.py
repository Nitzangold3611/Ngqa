#!/usr/bin/env python3
"""Build search indexes: site/courses/<course>/search.json (slide text, no speaker notes; GenAI also exercise PDFs).
usage: make_search.py  (paths below)"""
import json, re, subprocess, glob, os
SKILL = glob.glob('/root/.claude/skills/synced/*/pptx')[0]
SITE = '/home/claude/ngqa/site'
SRC = {'ctfl': [f'/home/claude/work/d{n}_toc.pptx' for n in range(1, 7)],
       'genai': [f'/home/claude/genai/out/g{n}.pptx' for n in range(1, 6)],
       'sql': [f'/home/claude/sql/out/ch{n}.pptx' for n in range(1, 12)],
       'ste': [f'/home/claude/ste/out/ch{n}.pptx' for n in range(1, 12)],
       'ai': [f'/home/claude/ai/out/ch{n}.pptx' for n in range(1, 11)],
       'mat': [f'/home/claude/mat/out/ch{n}.pptx' for n in range(1, 8)],
       'jobs': [f'/home/claude/jobs/out/ch{n}.pptx' for n in range(1, 5)]}
DROP = re.compile(r'^(\d+\s*/\s*\d+|☰?\s*תוכן עניינים|כל הזכויות שמורות.*|לתרגיל .*←|לפתיחת התרגיל.*)$')

def clean(block):
    block = block.split('### Notes:')[0]
    out = []
    for l in block.splitlines():
        l = l.strip()
        if not l or l.startswith('![') or re.match(r'^\|?\s*-{3}', l): continue
        l = re.sub(r'^#+\s*', '', l)
        if l.startswith('|'): l = ' '.join(c.strip() for c in l.strip('|').split('|') if c.strip())
        l = re.sub(r'\*\*|__', '', l).strip()
        if l and not DROP.match(l): out.append(l)
    return out

for course, decks in SRC.items():
    slides = []
    for n, pp in enumerate(decks, 1):
        txt = subprocess.run(['python3', SKILL + '/scripts/slide_text.py', pp], capture_output=True, text=True).stdout
        parts = re.split(r'<!-- Slide number: (\d+) -->', txt)[1:]
        for a, b in zip(parts[0::2], parts[1::2]):
            ls = clean(b)
            if not ls: continue
            t = ls[0]
            # kicker line (small grey topic) comes before the real title on some slides
            if len(ls) > 1 and len(t) < 40 and course == 'ctfl' and ('טכניקות' in t or 'קופסא' in t): t = ls[1]
            slides.append({'c': n, 's': int(a), 't': t[:120], 'x': ' · '.join(ls)})
    out = {'slides': slides}
    if course == 'genai':
        decks_json = json.load(open(f'{SITE}/courses/genai/decks.json'))
        ex = []
        for d in decks_json:
            for e in d.get('ex', []):
                pdf = f'{SITE}/courses/genai/ex/{e["id"]}.pdf'
                t = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
                t = re.sub(r'[‎‏‪-‮]', '', t)
                t = re.sub(r'[ \t]+', ' ', t); t = ' · '.join(l.strip() for l in t.splitlines() if l.strip())
                ex.append({'c': d['num'], 'id': e['id'], 'label': e['label'], 't': e['title'], 'x': t[:20000]})
        out['ex'] = ex
    if course == 'sql':
        ex = []
        for d in json.load(open(f'{SITE}/courses/sql/decks.json')):
            for e in d.get('ex', []):
                t = ' · '.join(i['q'] + ' ' + i['a'].replace('\n', ' ') for i in e['items'])
                ex.append({'c': d['num'], 'id': e['id'], 'label': e['label'], 't': e['title'], 'x': t[:20000]})
        out['ex'] = ex
    p = f'{SITE}/courses/{course}/search.json'
    json.dump(out, open(p, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(course, len(slides), 'slides', len(out.get('ex', [])), 'exercises', os.path.getsize(p) // 1024, 'KB')
