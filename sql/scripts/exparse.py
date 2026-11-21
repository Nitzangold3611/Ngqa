import re, json, glob, os
HEB = re.compile(r'[֐-׿]')
FILES = [('1', 'שאילתות'), ('2', 'אופרטורים תוויים'), ('3', 'פונקציות'), ('4', 'הוראות בשאילתות'), ('5', 'join'), ('6', 'תת שאילתות')]
out = {}
for ex, fn in FILES:
    L = [l.rstrip() for l in open(f'ex/{fn}.txt')]
    idx = max(i for i, l in enumerate(L) if 'פתרונות' in l and len(l) < 40)
    sol = [l for l in L[idx + 1:] if l.strip()]
    items, sec = [], ''
    i = 0
    while i < len(sol):
        l = sol[i].strip()
        if HEB.search(l) and not re.match(r'^\s*(SELECT|FROM|WHERE|--)', l, re.I):
            j = i + 1
            code = []
            while j < len(sol) and (not HEB.search(sol[j]) or re.match(r'^\s*(SELECT|FROM|WHERE|AND|OR|ORDER|GROUP|HAVING|JOIN|ON|INNER|LEFT|--)', sol[j].strip(), re.I)):
                code.append(sol[j].rstrip()); j += 1
            q = re.sub(r'^\d+\.\s*', '', l)
            if code:
                items.append({'sec': sec, 'q': q, 'a': '\n'.join(code)})
            else:
                sec = q.rstrip(':')
            i = j
        else:
            i += 1
    out[ex] = {'title': fn, 'items': items}
json.dump(out, open('ex/raw.json', 'w'), ensure_ascii=False, indent=1)
for ex in out:
    print('##', ex, out[ex]['title'], len(out[ex]['items']))
    for k, it in enumerate(out[ex]['items'], 1):
        print(k, '[' + it['sec'] + ']', it['q'], '||', it['a'].replace('\n', ' '))
