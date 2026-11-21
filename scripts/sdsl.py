import json, itertools
S = []
ICONS = ['target', 'layers', 'cogs', 'shield', 'search', 'list', 'check', 'info', 'sitemap', 'db', 'route', 'eye']
_ic = itertools.cycle(ICONS)
def _i(x):
    return x if x else next(_ic)
def _note(n):
    if not n: return None
    if isinstance(n, str): return {'lab': 'שימו לב', 'x': n}
    return {'lab': n[0], 'x': n[1]}
def _terms(tm):
    return {'lab': 'מושגים', 'x': ' · '.join(f'{a} — {b}' for a, b in tm)} if tm else None
def add(d, note=None, tm=None):
    n = _note(note) or _terms(tm)
    if n: d['note'] = n
    S.append(d)
def cover(tag, t, en, obj, objh=None):
    d = {'L': 'cover', 'tag': tag, 't': t, 'en': en, 'obj': obj, 'k': ''}
    if objh: d['objh'] = objh
    S.append(d)
def sec(num, k, t, en, x, pills, ic='layers'):
    S.append({'L': 'section', 'num': str(num), 'k': k, 't': t, 'en': en, 'x': x, 'pills': pills, 'ic': ic})
def cards(k, t, items, t2=None, lead=None, note=None, tm=None):
    d = {'L': 'cards', 'k': k, 't': t, 'items': [{'h': it[0], 's': it[1] if len(it) > 1 else '', 'ic': _i(it[2] if len(it) > 2 else None)} for it in items]}
    if t2: d['t2'] = t2
    if lead: d['lead'] = {'h': lead[0], 'x': lead[1]}
    add(d, note, tm)
def ld(k, t, items, tip=None, t2=None, note=None, tm=None, flow=None):
    d = {'L': 'list_dia', 'k': k, 't': t, 'items': [{'h': it[0], 'x': it[1] if len(it) > 1 else '', 'ic': _i(it[2] if len(it) > 2 else None)} for it in items]}
    if flow: d['dia'] = {'kind': 'vflow', 'nodes': flow}
    elif tip: d['dia'] = {'kind': 'tip', 'lab': tip[0], 'x': tip[1]}
    else: d['dia'] = {'kind': 'tip', 'lab': 'בקצרה', 'x': t}
    if t2: d['t2'] = t2
    add(d, note, tm)
def tbl(k, t, head, rows, t2=None, note=None, tm=None):
    d = {'L': 'table', 'k': k, 't': t, 'head': head, 'rows': rows}
    if t2: d['t2'] = t2
    add(d, note, tm)
def vs(k, t, a, b, t2=None, note=None, tm=None):
    d = {'L': 'vs', 'k': k, 't': t, 'cols': [{'h': a[0], 'rows': a[1], **({'s': a[2]} if len(a) > 2 else {})},
                                           {'h': b[0], 'rows': b[1], **({'s': b[2]} if len(b) > 2 else {})}]}
    if t2: d['t2'] = t2
    add(d, note, tm)
def steps(k, t, st, t2=None, note=None, tm=None):
    d = {'L': 'steps', 'k': k, 't': t, 'steps': [list(s) for s in st]}
    if t2: d['t2'] = t2
    add(d, note, tm)
def blocks(k, t, bl, flow=None, tip=None, t2=None, note=None, tm=None):
    B = []
    for b in bl:
        B.append({'h': b[0], 'pills': b[1]} if isinstance(b[1], list) else {'h': b[0], 'x': b[1]})
    d = {'L': 'blocks', 'k': k, 't': t, 'blocks': B}
    if flow: d['dia'] = {'kind': 'vflow', 'nodes': flow}
    elif tip: d['dia'] = {'kind': 'tip', 'lab': tip[0], 'x': tip[1]}
    if t2: d['t2'] = t2
    add(d, note, tm)
def summ(k, t, sub, items):
    S.append({'L': 'summary', 'k': k, 't': t, 'sub': sub, 'items': [{'h': a, 'x': b} for a, b in items]})
def save(path):
    for j, s in enumerate(S, 1): s['i'] = j
    open(path, 'w').write('\n'.join(json.dumps(s, ensure_ascii=False) for s in S) + '\n')
    print(path, len(S))
