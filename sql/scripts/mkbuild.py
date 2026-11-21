src = open('/home/claude/genai/gbuild.py').read()
src = src.replace('"""CT-GenAI decks', '"""SQL decks')
src = src.replace("""CHAPTER = {1: 'מבוא לבינה מלאכותית יוצרת בבדיקות תוכנה', 2: 'הנדסת פרומפטים לבדיקות תוכנה',
           3: 'ניהול סיכונים ב-GenAI', 4: 'LLMOps ותשתיות GenAI', 5: 'הטמעת GenAI בארגון'}""",
"""CHAPTER = {1: 'מבוא ל-SQL', 2: 'שאילתות', 3: 'אופרטורים', 4: 'פונקציות מוכללות', 5: 'הוראות בשאילתות',
           6: 'צירוף טבלאות – JOIN', 7: 'שאילתות משנה', 8: 'טיפול בנתונים', 9: 'פקודות DDL', 10: 'Views',
           11: 'Stored Procedures'}""")
src = src.replace("CH_OVR = json.load(open('/home/claude/genai/chapters.json')) if os.path.exists('/home/claude/genai/chapters.json') else {}", "CH_OVR = {}")
src = src.replace("f'<dc:title>CT-GenAI · פרק {N}</dc:title>'", "f'<dc:title>SQL לבודקי תוכנה · פרק {N}</dc:title>'")
src = src.replace("KREL = {'h': 1.12,", "KREL = {'d': 0.88, 'h': 1.12,")
src = src.replace("""        elif kd == 'k':
            out.append(P(t, pt * rel, col, False, 'r', bullet='check'""", """        elif kd == 'd':
            q = P(t, pt * rel, col, False, 'r', bullet='dash', bcol=GRAY, before=bef)
            ind = 0.24 * pt * rel / 16
            q = q.replace(f' marL="{emu(ind)}"', f' marL="{emu(ind + 0.32)}"', 1)
            out.append(q)
        elif kd == 'k':
            out.append(P(t, pt * rel, col, False, 'r', bullet='check'""")
assert "kd == 'd'" in src
src = src.replace("'indent': 0.2 if k in ('b', 'k', 'v') else 0", "'indent': 0.52 if k == 'd' else (0.2 if k in ('b', 'k', 'v') else 0)")
src = src.replace("[('מטרות למידה', 's')]", "[(sp.get('objh', 'מטרות למידה'), 's')]")
src = src.replace("    s.text('הנושא הבא', X0 + 0.3, 3.35, pw - 0.6, 0.35, 13, TEAL, True, 'ctr')",
                  "    s.box('Topic Name', X0 + 0.3, 3.0, pw - 0.6, 0.68, [(sp.get('t', ''), 'h')], 17, 10, al='ctr', anchor='b', hcol='FFFFFF', ins=(0.02, 0, 0.02, 0))")
assert "Topic Name" in src
extra = open('/home/claude/sql/sqlx.py').read()
assert src.rstrip().endswith('main()')
src = src.rstrip()[:-len('main()')] + extra + '\n\nmain()\n'
open('/home/claude/sql/sbuild.py', 'w').write(src)
