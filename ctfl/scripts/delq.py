import sys,os,re,zipfile,tempfile,shutil,subprocess
S='/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx'
src,dst,idx=sys.argv[1],sys.argv[2],[int(x) for x in sys.argv[3].split(',') if x]
w=tempfile.mkdtemp()
zipfile.ZipFile(src).extractall(w)
p=os.path.join(w,'ppt/presentation.xml'); x=open(p,encoding='utf-8').read()
ids=re.findall(r'<p:sldId [^>]*/>',x)
for i in sorted(idx,reverse=True): x=x.replace(ids[i-1],'',1)
open(p,'w',encoding='utf-8').write(x)
subprocess.run(['python3',S+'/scripts/clean.py',w],check=True,capture_output=True)
out=os.path.abspath(dst)
if os.path.exists(out): os.remove(out)
subprocess.run(['zip','-qXrDy',out,'.'],cwd=w,check=True); shutil.rmtree(w)
print(os.path.basename(dst),'removed',len(idx),'left',len(ids)-len(idx))
