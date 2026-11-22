import json
exec(open('/home/claude/gx/qs.py').read())
exec(open('/home/claude/gx/why.py').read())
L=[{"L":"cover","tag":"CT-GenAI · מבחן לדוגמא | Sample Exam","t":"מבחן לדוגמא","en":"ISTQB® CT-GenAI — Testing with Generative AI","objh":"מבנה המבחן","obj":["40 שאלות — לכל שאלה שקף שאלה ושקף תשובה","חלק מהשאלות דורשות בחירת שתי תשובות","נסו לענות לפני מעבר לשקף התשובה","בשקף התשובה מופיעים סעיף הסילבוס והסבר קצר","השאלות מכסות את כל חמשת פרקי הסילבוס"],"k":""}]
for n,x in enumerate(Q,1):
    pick='בחרו שתי תשובות' if len(x['ans'])==2 else 'בחרו תשובה אחת'
    base={"L":"mcq","k":f"שאלה {n} · סעיף {x['topic']}","t":f"שאלה {n} — {x['title']}","q":x['q'],"opts":x['opts'],"pick":pick}
    if x.get('stem'): base['stem']=x['stem']
    L.append(dict(base)); a=dict(base); a['ans']=x['ans']; a['exp']=x['exp']; a['why']=W[n]; a['t']=f"שאלה {n} — תשובה"; L.append(a)
L.append({"L":"summary","k":"מבחן לדוגמא · סיכום","t":"בהצלחה במבחן!","sub":"טיפים לבחינת CT-GenAI","items":[{"h":"קראו בעיון","x":"שימו לב ל\"אינה נכונה\", \"הטובה ביותר\" ו\"בחרו שתי תשובות\""},{"h":"יסודות","x":"Tokenization, חלון הקשר, סוגי מודלים, Multimodal"},{"h":"מבנה הפרומפט","x":"Role, Context, Instruction, Input Data, Constraints, Output Format"},{"h":"טכניקות","x":"Few-Shot, Prompt Chaining, Meta Prompting, System Prompt"},{"h":"סיכונים","x":"Hallucination, Temperature, פרטיות, Data Poisoning, Shadow AI"},{"h":"תשתית וארגון","x":"RAG, Agents, Fine-Tuning, LLMOps, שלבי אימוץ"}]})
for j,s in enumerate(L,1): s['i']=j
open('/home/claude/gx/spec/ch6.jsonl','w').write('\n'.join(json.dumps(s,ensure_ascii=False) for s in L)+'\n')
print(len(L))
