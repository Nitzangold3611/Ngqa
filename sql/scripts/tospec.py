#!/usr/bin/env python3
"""model.json -> spec/ch{N}.jsonl for sbuild.py"""
import json, re, os, sys
sys.path.insert(0, '/home/claude/sql')
from extract import is_code, HEB
from PIL import Image

D = json.load(open('/home/claude/sql/model.json'))
CH = [(1, 1, 38), (2, 39, 59), (3, 60, 131), (4, 132, 238), (5, 239, 264), (6, 265, 319), (7, 320, 361),
      (8, 362, 428), (9, 429, 481), (10, 482, 498), (11, 499, 520)]
NAMES = {1: 'מבוא ל-SQL', 2: 'שאילתות', 3: 'אופרטורים', 4: 'פונקציות מוכללות', 5: 'הוראות בשאילתות',
         6: 'צירוף טבלאות – JOIN', 7: 'שאילתות משנה', 8: 'טיפול בנתונים', 9: 'פקודות DDL', 10: 'Views',
         11: 'Stored Procedures'}
EN = {1: 'Introduction & Getting Started', 2: 'SELECT … FROM', 3: 'Operators', 4: 'Built-in Functions',
      5: 'Query Clauses', 6: 'JOIN', 7: 'Subqueries', 8: 'Data Manipulation (DML)', 9: 'Data Definition Language',
      10: 'Views', 11: 'Stored Procedures'}
EXNAME = {1: 'שאילתות', 2: 'אופרטורים', 3: 'פונקציות', 4: 'הוראות בשאילתות', 5: 'JOIN', 6: 'תת שאילתות'}
IMG = '/home/claude/sql/imgs'
CONV = '/home/claude/sql/imgconv'
os.makedirs(CONV, exist_ok=True)
NORTHWIND = '/mnt/user-data/uploads/sql/חומר עזר/Northwind diagram.png'
FIX = [(r'SQL Server 2008', 'SQL Server'), (r'\s+', ' ')]
EXAMPLE = re.compile(r'^(ל?דוגמ[הא]|דוגמאות|התוצאה|נקבל את התוצאה הבאה|התוצאה תהיה|תחביר|הפקודה|הפלט|פלט)[^.]{0,40}:$')


OVR = {}


def ovr(n):
    def deco(fn):
        OVR[n] = fn
        return fn
    return deco


@ovr(74)
def _o74(flow):
    return [['p', [['סדר הקדימות של החישוב:', 'b'], ['סוגריים, חזקות, כפל/חילוק/שארית, חיבור/חיסור', 'd'], ['דוגמאות:', 's']]],
            ['code', '2 * 6 + 9 / 3        -- = 12 + 3 = 15\n2 * (6 + 9) / 3      -- = 2 * 15 / 3 = 10']]


@ovr(21)
def _o21(flow):
    return [['p', [['במהלך הקורס נעבוד עם SQL Server של חברת Microsoft', 'b'],
                   ['SQL Server 2025 Express – גרסה חינמית להורדה מאתר מיקרוסופט', 'b'],
                   ['ממשק העבודה: SQL Server Management Studio (SSMS 22)', 'b'],
                   ['מסד הנתונים לתרגול: Northwind – מידע על חברה המייבאת ומייצאת מזון ייחודי', 'b'],
                   ['מדריך ההתקנה המלא, קובץ הגיבוי של Northwind וסרטון ההדגמה נמצאים בלשונית "חומר עזר" באתר הקורס', 's']]]]


@ovr(23)
def _o23(flow):
    return [['p', [['פותחים את תפריט Start ומקלידים SSMS', 'b'],
                   ['בוחרים ב-SQL Server Management Studio 22', 'b']]]] + [f for f in flow if f[0] == 'img']


@ovr(24)
def _o24(flow):
    return [['p', [['בחלון Connect to Server מזינים את הפרטים הבאים:', 'b'],
                   ['Server Type: Database Engine', 'd'], ['Server Name: localhost\\SQLEXPRESS (או שם המחשב שלכם)', 'd'],
                   ['Authentication: Windows Authentication', 'd'],
                   ['Encryption: Optional, או סימון Trust Server Certificate', 'd'], ['לוחצים Connect', 'd']]]] + \
        [f for f in flow if f[0] == 'img']


@ovr(26)
def _o26(flow):
    return {'t': 'שחזור Northwind מקובץ הגיבוי', 't2': 'Restore Database',
            'flow': [['p', [['מורידים את הקובץ northwind.bak מלשונית "חומר עזר" באתר הקורס', 'b'],
                            ['מעתיקים אותו לתיקייה פשוטה, למשל C:\\SQLBackups', 'b'],
                            ['ב-Object Explorer: קליק ימני על Databases ← Restore Database…', 'b'],
                            ['Source: מסמנים Device ← לוחצים … ← Add ← בוחרים את הקובץ', 'b'],
                            ['בעמוד Files מסמנים Relocate all files to folder', 'b'],
                            ['לוחצים OK, והמסד Northwind יופיע תחת Databases', 'b']]],
                     ['note', [['סרטון הדגמה של השחזור, שלב אחר שלב, נמצא בלשונית "חומר עזר" באתר הקורס', 'x']]]]}


SS = '/home/claude/sql/ssms/'


def _ss(n, img, text=None, t2=None):
    def f(flow):
        fl = [x for x in flow if x[0] not in ('img', 'note')] if text is None else text
        im = Image.open(SS + img + '.png')
        r = {'flow': fl + [['img', SS + img + '.png', im.width / im.height]]}
        if t2:
            r['t2'] = t2
        return r
    OVR[n] = f


_o23_text = [['p', [['פותחים את תפריט Start ומקלידים SSMS', 'b'], ['בוחרים ב-SQL Server Management Studio 22', 'b'],
                    ['טיפ: מומלץ להצמיד את SSMS לשורת המשימות', 's']]]]
OVR[23] = lambda flow: _o23_text
_ss(24, 'connect', [['p', [['בחלון Connect to Server מזינים את הפרטים הבאים:', 'b'],
                           ['Server type: Database Engine', 'd'], ['Server name: localhost\\SQLEXPRESS', 'd'],
                           ['Authentication: Windows Authentication', 'd'],
                           ['מסמנים Trust server certificate', 'd'], ['לוחצים Connect', 'd']]]])
_ss(25, 'oe_nw', [['p', [['ב-Object Explorer פותחים את Databases', 'b'], ['ובוחרים ב-Northwind', 'b']]]])
_ss(34, 'oe_nw', None, 'ב-SSMS 22')
_ss(35, 'newq', None, 'ב-SSMS 22')
_ss(36, 'editor', None, 'ב-SSMS 22')
_ss(37, 'exec', None, 'ב-SSMS 22')

for _n in (27, 28):
    OVR[_n] = lambda flow: None


def fx(t):
    for a, b in FIX:
        t = re.sub(a, b, t)
    return t.strip()


def ft(t):
    return fx(t).rstrip(':').strip()


def img_path(i):
    if i['h'] == '7857f1b9' and os.path.exists(NORTHWIND):
        return NORTHWIND
    p = os.path.join(IMG, i['f'])
    if not p.endswith('.png') and not p.endswith('.jpg'):
        q = os.path.join(CONV, i['h'] + '.png')
        if not os.path.exists(q):
            Image.open(p).convert('RGB').save(q)
        p = q
    return p


def as_table(raws):
    """plain-text result grids -> table rows"""
    if len(raws) < 3 or any(HEB.search(r) for r in raws):
        return None
    if all('\t' in r for r in raws):
        rows = [[c.strip() for c in re.split(r'\t+', r.strip())] for r in raws]
    else:
        rows = [r.split() for r in raws]
    n = len(rows[0])
    if n < 2 or any(len(r) != n for r in rows[1:] if not re.match(r'^[.…]+$', ' '.join(r))):
        return None
    return [r if len(r) == n else [r[0]] + [''] * (n - 1) for r in rows]


def para_flow(paras, flow, as_note=False):
    """paragraph list -> flow entries (text groups and code panels)"""
    cur, code = [], []
    pend_blank = 0

    raws = []

    def flush_text():
        nonlocal cur, raws
        if cur:
            tb = as_table(raws)
            if tb:
                flow.append(['table', tb])
            else:
                flow.append(['note' if as_note else 'p', cur])
            cur = []
            raws = []

    def flush_code():
        nonlocal code
        while code and not code[-1].strip():
            code.pop()
        if code:
            flow.append(['code', '\n'.join(code)])
            code = []

    for p in paras:
        raw = p['raw'].replace('\t', '    ').rstrip()
        t = p['t']
        if not t:
            if code:
                code.append('')
            continue
        if is_code(t) or (code and not HEB.search(t) and len(t) < 120):
            flush_text()
            # keep relative indentation inside code
            code.append(raw.lstrip() if not code else raw.replace(' ', ' ').rstrip())
            continue
        flush_code()
        t = fx(t)
        if EXAMPLE.match(t) or (len(t) < 22 and t.endswith(':')):
            kind = 's'
        elif as_note:
            kind = 'x'
        else:
            kind = 'b' if p['lvl'] == 0 else 'd'
        cur.append([t, kind])
        raws.append(p['raw'])
    flush_text()
    flush_code()


def norm_code(c):
    lines = c.split('\n')
    # strip common leading indentation of non-first lines
    ind = [len(l) - len(l.lstrip()) for l in lines[1:] if l.strip()]
    m = min(ind) if ind else 0
    out = [lines[0].strip()] + [('  ' + l[m:].rstrip()) if (l[:m].strip() == '' and m) else l.rstrip() for l in lines[1:]]
    # indented lines with excessive spaces
    out = [re.sub(r'^\s{6,}', '    ', l) for l in out]
    out = [l.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"') for l in out]
    return '\n'.join(out)


def agenda_items(m):
    items = []
    for b in m['body'] + m['notes']:
        for p in b['paras']:
            if p['t']:
                items.append(ft(p['t']))
    return items


def build_chapter(N, a, b):
    specs = []
    slides = D[a - 1:b]
    agenda = None
    occ = 0
    sec = None
    cover = slides[0]
    i = 1
    # cover objectives: topics of the first agenda
    first_ag = next((m for m in slides if m['t'].strip() == 'נושאים'), None)
    global AY, ASTEP
    AY = sorted({round(m['agenda_arrow_y'], 2) for m in slides if m['t'].strip() == 'נושאים' and m.get('agenda_arrow_y')})
    dif = [b_ - a_ for a_, b_ in zip(AY, AY[1:]) if b_ - a_ > 0.3]
    ASTEP = min(dif) if dif else 0.82
    topics = agenda_items(first_ag) if first_ag else []
    specs.append({'i': i, 'L': 'cover', 'tag': 'SQL לבודקי תוכנה', 't': NAMES[N], 'en': f'פרק {N} · {EN[N]}',
                  'obj': topics[:6], 'objh': 'נושאי הפרק'})
    for m in slides[1:]:
        t = ft(m['t'])
        if t == 'נושאים':
            items = agenda_items(m)
            occ += 1
            idx = occ
            if m.get('agenda_arrow_y') is not None and items and AY:
                idx = max(1, min(len(items), round((m['agenda_arrow_y'] - AY[0]) / ASTEP) + 1))
            if N == 1 and occ == 1:
                idx = 1
            new_sec = (f'{N}.{idx}', items[idx - 1] if idx <= len(items) else '')
            if sec and idx <= int(sec[0].split('.')[1]) and N != 1:
                continue
            sec = new_sec
            i += 1
            specs.append({'i': i, 'L': 'section', 'k': sec[0], 't': sec[1], 'en': f'פרק {N} · {NAMES[N]}',
                          'topics': items, 'cur': idx, 'ic': 'layers'})
            continue
        txt = [fx(p['t']) for bb in m['body'] + m['notes'] for p in bb['paras'] if p['t']]
        i += 1
        if t == 'תרגיל':
            mm = re.search(r'תרגיל (\d+) בחוברת', ' '.join(txt))
            dur = next((x for x in txt if 'דקות' in x), '')
            if mm:
                ex = int(mm.group(1))
                sp = {'i': i, 'L': 'exercise', 't': 'תרגיל מעשי', 'k': sec[0] if sec else '',
                      'meta': [['משך מומלץ', dur or '30 דקות']]}
                if ex in EXNAME:
                    sp['meta'].insert(0, ['תרגיל', f'תרגיל {ex} · {EXNAME[ex]}'])
                    sp['ex'] = str(ex)
                    sp['goal'] = 'לכתוב את השאילתות לפי השאלות בדף התרגיל, להריץ אותן ב-SSMS על מסד הנתונים Northwind ולהשוות לפתרון'
                else:
                    sp['meta'].insert(0, ['תרגול', 'תרגילים מסכמים'])
                    sp['goal'] = ('לתרגל את נושאי הפרק בתרגילים המסכמים (College · Party) '
                                  'שבעמוד הבית של הקורס')
                specs.append(sp)
                continue
            # in-class exercise (chapter 1)
            code = [x for x in txt if is_code(x)]
            specs.append({'i': i, 'L': 'exercise', 't': 'תרגיל בכיתה', 'k': sec[0] if sec else '',
                          'meta': [['סביבה', 'SQL Server + SSMS'], ['מסד נתונים', 'Northwind']],
                          'goal_list': [x for x in txt if not is_code(x)], 'goal_lab': 'שלבים',
                          'code': '\n'.join(code)})
            continue
        flow = []
        body = m['body']
        notes = m['notes']
        if not body and notes:
            # biggest text box acts as body
            notes = sorted(notes, key=lambda b: -sum(len(p['t']) for p in b['paras']))
            body, notes = notes[:1], notes[1:]
        for bb in body:
            para_flow(bb['paras'], flow)
        for bb in notes:
            para_flow(bb['paras'], flow, as_note=True)
        for f in flow:
            if f[0] == 'code':
                f[1] = norm_code(f[1])
            if f[0] == 'note' and all(k == 's' for _, k in f[1]):
                f[0] = 'p'
        tiny = [f for f in flow if f[0] == 'note' and len(f[1]) == 1 and len(f[1][0][0]) <= 14]
        if len(tiny) >= 2 or (tiny and any(f[0] == 'code' for f in flow)):
            labs = [f[1][0][0] for f in tiny]
            flow = [f for f in flow if f not in tiny] + [['pills', labs]]
        for f in flow:
            if f[0] == 'pills' and set(f[1]) <= {"טבלה א'", "טבלה ב'", 'טבלה א', 'טבלה ב'} and len(f[1]) == 2:
                tt = (m['t'] + ' ' + m['t2']).upper()
                kind = ('left' if ('LEFT' in tt or 'שמאלי' in tt) else 'right' if ('RIGHT' in tt or 'ימני' in tt) else
                        'full' if ('FULL' in tt or 'מלא' in tt) else 'inner' if ('INNER' in tt or 'פנימי' in tt) else 'all')
                f[0], f[1] = 'venn', kind
        for j, f in enumerate(flow):
            if f[0] in ('note', 'p') and all(not HEB.search(t) and re.search(r"[(),'=+]", t) for t, _ in f[1]):
                nb = [flow[k][0] for k in (j - 1, j + 1) if 0 <= k < len(flow)]
                if 'code' in nb:
                    flow[j] = ['code', '\n'.join('    ' + t for t, _ in f[1])]
        RES = re.compile(r'^(נקבל|התוצאה|יחזיר|תתקבל|נקבל את)')
        for j in range(len(flow) - 1):
            f, g = flow[j], flow[j + 1]
            if f[0] == 'p' and g[0] == 'code' and len(f[1]) > 1 and RES.match(f[1][-1][0]) and f[1][-1][1] == 's':
                last = f[1].pop()
                flow.insert(j + 2, ['p', [last]])
        merged = []
        for f in flow:
            if merged and f[0] == 'code' and merged[-1][0] == 'code' and \
                    len(f[1].split('\n')) + len(merged[-1][1].split('\n')) <= 14:
                merged[-1][1] += '\n' + f[1]
            elif merged and f[0] == 'p' and merged[-1][0] == 'p':
                merged[-1][1] += f[1]
            else:
                merged.append(f)
        flow = merged
        for tb in m['tables']:
            rows = [[fx(c) for c in r] for r in tb['rows']]
            rows = [r for r in rows if any(c for c in r)]
            if rows:
                flow.append(['table', rows])
        for im in m['imgs']:
            if im['h'] in ('5b5d8c72', 'd4f100e8'):
                flow.append(['venn', 'right' if im['h'] == '5b5d8c72' else 'left'])
                continue
            p = img_path(im)
            w, h = Image.open(p).size
            flow.append(['img', p, w / h])
        extra = {}
        if m['n'] in OVR:
            r = OVR[m['n']](flow)
            if r is None:
                i -= 1
                continue
            if isinstance(r, dict):
                extra = r
                flow = r.get('flow', flow)
            else:
                flow = r
        sp = {'i': i, 'L': 'auto', 't': t or (sec[1] if sec else NAMES[N]), 'flow': flow, 'src': m['n']}
        if m['t2']:
            sp['t2'] = fx(m['t2'])
        if sec:
            sp['k'] = f'{sec[0]} · {sec[1]}'
        for kk in ('t', 't2'):
            if kk in extra:
                sp[kk] = extra[kk]
        if sp.get('t2') and re.search(r'\s(של|בין|את|ה|ו)$', sp['t']):
            sp['t'] = sp['t'] + ' ' + sp.pop('t2')
        specs.append(sp)
    secs = [sp for sp in specs if sp['L'] == 'section']
    if secs:
        remap = {sp['k']: f'{N}.{j}' for j, sp in enumerate(secs, 1)}
        titles = [sp['t'] for sp in secs]
        for j, sp in enumerate(secs, 1):
            sp['topics'] = titles
            sp['cur'] = j
        for sp in specs:
            k = sp.get('k')
            if k:
                head = k.split(' · ')[0]
                if head in remap:
                    sp['k'] = remap[head] + k[len(head):]
        specs[0]['obj'] = titles[:7]
    if not any(sp['L'] == 'section' for sp in specs):
        # no agenda slides: number topics by distinct titles
        k = 0
        last = None
        for sp in specs[1:]:
            if sp['L'] != 'auto':
                if sp.get('k') == '' or 'k' in sp:
                    sp['k'] = f'{N}.{k}' if k else ''
                continue
            base = re.sub(r'\s*[-–(].*$', '', sp['t']).strip() or sp['t']
            if base != last:
                k += 1
                last = base
                sp['toc'] = base
            sp['k'] = f'{N}.{k} · {base}'
    os.makedirs('/home/claude/sql/spec', exist_ok=True)
    with open(f'/home/claude/sql/spec/ch{N}.jsonl', 'w') as f:
        for sp in specs:
            f.write(json.dumps(sp, ensure_ascii=False) + '\n')
    return len(specs)


if __name__ == '__main__':
    for N, a, b in CH:
        print(N, build_chapter(N, a, b))
