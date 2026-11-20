import zipfile,re,json,subprocess
from lxml import etree
from extract import *
def items_of(el):
    items=[]
    for p in el.iter(A+'p'):
        s=''.join(x.text or '' for x in p.iter(A+'t')).strip()
        if not s: continue
        m=re.match(r'^(\d+(?:\.\d+)*)\s*(.*)$',s)
        items.append((m.group(1),m.group(2).strip()) if m else ('',s))
    return items
res={}
for n in range(1,7):
    rep=[a for a,b,c in json.load(open(f'v2_report_{n}.json')) if b=='agenda']
    if not rep: continue
    z=zipfile.ZipFile(f'd{n}_toc_v1.pptx');o=order(z)
    for i in rep:
        t=etree.fromstring(z.read('ppt/'+o[i-1]));cls,te,ne,rest=classify(t)
        tp=[e for k,e in rest if k=='textplain'][0]; mk=[e for k,e in rest if k=='shape'][0]
        mb=box(mk); my=(mb[1]+mb[3]/2)*72
        x=subprocess.run(['pdftotext','-bbox-layout','-f',str(i),'-l',str(i),f'v1pdf/{n}/deck.pdf','-'],capture_output=True,text=True).stdout
        lines=[]
        for ln in re.findall(r'<line xMin="[\d.]+" yMin="([\d.]+)" xMax="[\d.]+" yMax="([\d.]+)">(.*?)</line>',x,re.S):
            words=re.findall(r'>([^<]*)</word>',ln[2]); lines.append(((float(ln[0])+float(ln[1]))/2,' '.join(words)))
        its=items_of(tp)
        b0=box(tp); y0,y1=b0[1]*72-5,(b0[1]+b0[3])*72+5
        cand=[(abs(y-my),s) for y,s in lines if y0<=y<=y1 and s.strip()]
        best=None
        cand=sorted((abs(y-my),y,s0) for y,s0 in lines if y0<=y<=y1 and s0.strip())
        if cand:
            yb=cand[0][1]
            s0=' '.join(c[2] for c in cand if abs(c[1]-yb)<3).replace('&amp;','&')
            ws=set(s0.split())|{w[::-1] for w in s0.split()}
            sc=[(len(ws & set((num+' '+txt).split()))/max(1,len(set((num+' '+txt).split()))),k) for k,(num,txt) in enumerate(its)]
            m=max(sc)
            best=(cand[0][0],m[1],m[0],s0)
        res[f'{n}-{i}']=best[1] if best else None
        print(n,i,its[best[1]][1][:30] if best else None, round(best[0],1) if best else '', round(best[2],2) if best else '', '|', best[3][:40] if best else '')
json.dump(res,open('agenda_cur.json','w'))
