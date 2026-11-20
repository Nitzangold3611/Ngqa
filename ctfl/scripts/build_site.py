from PIL import Image
import json,glob,os,re,zipfile,subprocess,sys
from lxml import etree
sys.path.insert(0,'/home/claude/work')
import fix_titles as FT
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}';R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
S='/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx'
CH={1:('מבוא לבדיקות תוכנה','Fundamentals of Testing'),2:('בדיקות לאורך מחזור חיי התוכנה','Testing Throughout the SDLC'),3:('בדיקות סטטיות','Static Testing'),4:('טכניקות בדיקה','Test Analysis and Design'),5:('ניהול בדיקות','Managing the Test Activities'),6:('כלי בדיקה','Test Tools')}
V=sys.argv[1] if len(sys.argv)>1 else '4'
os.chdir('/home/claude/work/site')
for f in glob.glob('sp/*'): os.remove(f)
decks=[];N=6
for n in range(1,7):
    pp=f'../d{n}_toc.pptx'; z=zipfile.ZipFile(pp)
    pres=z.read('ppt/presentation.xml').decode(); sz=re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"',pres); W,H=int(sz.group(1)),int(sz.group(2))
    rels=z.read('ppt/_rels/presentation.xml.rels').decode()
    m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
    order=[m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',pres)]
    out=subprocess.run(['python3',S+'/scripts/slide_text.py',pp],capture_output=True,text=True).stdout
    parts=re.split(r'<!-- Slide number: (\d+) -->',out)[1:]
    texts={int(a):b.split('### Notes:')[0] for a,b in zip(parts[0::2],parts[1::2])}
    fs=sorted(glob.glob(f'../hr{n}/s-*.jpg')); assert len(fs)==len(order),(n,len(fs),len(order))
    slides=[];ims=[]
    for i,(f,target) in enumerate(zip(fs,order),1):
        im=Image.open(f).convert('RGB'); w=1440; h=round(im.height*w/im.width); ims.append(im.resize((w,h),Image.LANCZOS))
        lines=[l.strip('# |').strip() for l in texts.get(i,'').splitlines() if l.strip() and not l.strip().startswith('![')]
        sp_path='ppt/'+target; rp=sp_path.replace('slides/','slides/_rels/')+'.rels'; srels={}
        if rp in z.namelist():
            for r in re.findall(r'<Relationship [^>]*>',z.read(rp).decode()):
                if 'TargetMode="External"' in r and 'hyperlink' in r:
                    srels[re.search(r'Id="([^"]+)"',r).group(1)]=re.search(r'Target="([^"]+)"',r).group(1).replace('&amp;','&')
        links=[]; seen=set()
        t=etree.fromstring(z.read(sp_path))
        for sp in t.iter(P+'sp',P+'pic'):
            urls=[srels[x.get(R+'id')] for x in sp.iter(A+'hlinkClick') if x.get(R+'id') in srels]
            # web addresses typed as plain text count as links too
            urls+=re.findall(r'https?://[^\s<>"]+', ''.join(sp.itertext()))
            for u in urls:
                u=u.rstrip('.,)')
                if u in seen: continue
                seen.add(u)
                b=FT.real_box(sp)
                L={'url':u}
                # a clickable area only where the link has a small box of its own
                if b and b[2]*b[3] < 0.2*W*H:
                    L.update({'x':round(b[0]/W*100,2),'y':round(b[1]/H*100,2),'w':round(b[2]/W*100,2),'h':round(b[3]/H*100,2)})
                links.append(L)
        TL=json.load(open(f'/home/claude/work/toc_links_{n}.json'))
        if i==TL['toc_slide']:
            links+= [dict(l) for l in TL['links']]
        master_shown = b'showMasterSp="0"' not in z.read(sp_path)
        if master_shown and i!=TL['toc_slide']:
            links.append(dict(TL['back'], slide=TL['toc_slide']))
        s={'title':(lines[0] if lines else '')[:120],'text':' '.join(lines)[:700]}
        if links: s['links']=links
        slides.append(s)
    for g in range(0,len(ims),N):
        c=Image.new('RGB',(w,h*N),'white')
        for k,im in enumerate(ims[g:g+N]): c.paste(im,(0,k*h))
        name=f'sp/ch{n}_{g//N:02d}.jpg'; c.save(name,quality=78,optimize=True,progressive=True)
        for k in range(len(ims[g:g+N])): slides[g+k]['img']=name+'?v='+V; slides[g+k]['k']=k
    decks.append({'id':f'ch{n}','num':n,'title':CH[n][0],'sub':CH[n][1],'cover':f'img/ch{n}.jpg','ratio':f'{w}/{h}','per':N,'slides':slides})
json.dump(decks,open('decks.json','w'),ensure_ascii=False)
print(len(glob.glob('sp/*')),'sprites', sum(len(d['slides']) for d in decks),'slides')
