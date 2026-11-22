import json, sys
L, CH = sys.argv[1], int(sys.argv[2])
exec(open(f'/home/claude/cfx/q{L}.py').read())
KEY = json.load(open('/home/claude/cfx/key.json'))[L]
LO = json.load(open('/home/claude/cfx/lo.json'))[L]
letters = 'abcde'
assert sorted(Q) == list(range(1, 41)), sorted(Q)
out = [{"L": "cover", "tag": f"CTFL 4.0 · Sample Exam {L}", "t": f"מבחן לדוגמא {L}",
        "en": f"ISTQB® Certified Tester Foundation Level v4.0 — Sample Exam {L}", "objh": "מבנה המבחן",
        "obj": ["40 שאלות — לכל שאלה שקף שאלה ושקף תשובה", "חלק מהשאלות דורשות בחירת שתי תשובות", "נסו לענות לפני מעבר לשקף התשובה",
                "בשקף התשובה מוסבר מדוע כל אפשרות נכונה או שגויה", "השאלות לפי ערכת מבחן לדוגמא " + L + " הרשמית של ISTQB, בתרגום ITCB"], "k": ""}]
for n in range(1, 41):
    x = Q[n]
    ans = [letters.index(c.strip()) for c in KEY[str(n)].split(',')]
    assert len(x['why']) == len(x['opts']), n
    ok = [i for i, w in enumerate(x['why']) if w.startswith('נכון')]
    assert ok == ans, (n, ok, ans)
    import re as _re
    _M = _re.compile(r'[A-Za-z\d(][\w\s.,+\-−×*/=^()$%:<>≤≥]*?[=×<>≤≥][\w\s.,+\-−×*/=^()$%:<>≤≥]*[\w)$%]', _re.A)
    def mw(t):
        t = t.replace('\u202a', '').replace('\u202c', '')
        return _M.sub(lambda m: '\u200e' + m.group(0).rstrip().replace(' ', '\u200e \u200e') + '\u200e' + (' ' if m.group(0).endswith(' ') else ''), t)
    x['why'] = [mw(w) for w in x['why']]
    if x.get('stem'): x['stem'] = [mw(t) for t in x['stem']]
    rl = lambda t: ('\u200f' + t) if t[:1].isascii() and t[:1].isalnum() else t
    x['opts'] = [rl(mw(o)) for o in x['opts']]; x['q'] = rl(mw(x['q']))
    pick = 'בחרו שתי תשובות' if len(ans) == 2 else 'בחרו תשובה אחת'
    base = {"L": "mcq", "k": f"שאלה {n} · {LO[str(n)]}", "t": f"שאלה {n} — {x['title']}", "q": x['q'], "opts": x['opts'], "pick": pick}
    if x.get('stem'): base['stem'] = ['  ' + t for t in x['stem']] if x.get('stem_plain') else x['stem']
    if x.get('img'): base['img'] = '/home/claude/cfx/img/' + x['img']
    for k in ('wide', 'ih'):
        if k in x: base[k] = x[k]
    out.append(dict(base))
    a = dict(base); a['ans'] = ans; a['exp'] = x['why'][ans[0]].split(' — ', 1)[1]; a['why'] = x['why']; a['t'] = f"שאלה {n} — תשובה"
    out.append(a)
out.append({"L": "summary", "k": "מבחן לדוגמא · סיכום", "t": "בהצלחה במבחן!", "sub": "טיפים לבחינת CTFL 4.0", "items": [
    {"h": "קראו בעיון", "x": "שימו לב ל\"אינו\", \"הטוב ביותר\" ו\"בחר שתי אפשרויות\""},
    {"h": "חלוקת זמן", "x": "40 שאלות ב-60 דקות — דלגו על שאלה קשה וחזרו אליה"},
    {"h": "טכניקות", "x": "תרגלו מחלקות שקילות, ערכי גבול, טבלאות החלטה ומעברי מצבים"},
    {"h": "מונחים", "x": "הבדילו בין שגיאה, פגם וכשל, ובין בדיקות אישוש לרגרסיה"},
    {"h": "חישובים", "x": "הערכת שלוש נקודות: E = (a + 4m + b) / 6"},
    {"h": "ציון עובר", "x": "65% — לפחות 26 תשובות נכונות"}]})
for j, s in enumerate(out, 1): s['i'] = j
open(f'/home/claude/cfx/spec/ch{CH}.jsonl', 'w').write('\n'.join(json.dumps(s, ensure_ascii=False) for s in out) + '\n')
print(len(out))
