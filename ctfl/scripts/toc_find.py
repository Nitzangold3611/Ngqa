import zipfile,re,json,difflib
exec(open('toc_scan.py').read().split('out={}')[0])
TOPICS={
1:[('1.1','מהן בדיקות תוכנה?'),('1.2','הצורך בבדיקות תוכנה'),('1.3','עקרונות מנחים בבדיקות תוכנה'),('1.4','תהליך הבדיקות, בודקה ובעלי תפקידים'),('1.5','מיומנויות חיוניות ושיטות עבודה בבדיקות תוכנה')],
2:[('2.1','בדיקות בהקשר של מודלים לפיתוח תוכנה'),('2.2','רמות בדיקה'),('2.3','סוגי בדיקות'),('2.4','בדיקות תחזוקה')],
3:[('3.1','יסודות הבדיקות הסטטיות'),('3.2','תהליך הסקירה'),('3.2.4','תפקידים'),('3.2.5','סוגי סקירות'),('3.2.6','גורמים להצלחת התהליך')],
4:[('4.1','קטגוריות של טכניקות בדיקה'),('4.2','טכניקות קופסא שחורה'),('4.3','טכניקות קופסא לבנה'),('4.4','טכניקות מבוססות נסיון'),('4.5','גישות בדיקה מבוססות שיתוף פעולה')],
}
def norm(s): return re.sub(r'[^א-תa-zA-Z0-9 ]','',s).replace('  ',' ').strip()
res={}
for n,tops in TOPICS.items():
    z=zipfile.ZipFile(f'd{n}_final.pptx'); o=order(z)
    tt=[]
    for i,s in enumerate(o,1):
        t=etree.fromstring(z.read('ppt/'+s)); tt.append(' '.join(top_text(t)))
    print('== deck',n)
    for num,name in tops:
        cands=[]
        for i,x in enumerate(tt,1):
            if i<=3: continue
            r=difflib.SequenceMatcher(None,norm(name),norm(x)[:len(norm(name))+15]).ratio()
            if norm(name) in norm(x): r=max(r,0.95)
            cands.append((r,i,x[:60]))
        cands.sort(reverse=True)
        print(' ',num,name,'->',[(round(a,2),b,c) for a,b,c in cands[:3]])
