#!/bin/bash
cd /home/claude/ai && python3 mkbuild.py
for N in "$@"; do
python3 aibuild.py $N spec/ch$N.jsonl out/ch$N.pptx 2>&1 | tail -2
(cd out && timeout 300 soffice --headless --convert-to pdf ch$N.pptx >/dev/null 2>&1; rm -rf q$N; mkdir q$N; pdftoppm -r 50 -jpeg ch$N.pdf q$N/s 2>/dev/null)
python3 - $N <<'PY'
import sys,glob
from PIL import Image
N=sys.argv[1]
fs=sorted(glob.glob(f'/home/claude/ai/out/q{N}/*.jpg'))
if not fs: sys.exit()
ims=[Image.open(f) for f in fs]; w,h=ims[0].size
for k in range(0,len(ims),12):
  g=Image.new('RGB',(w*3,h*4),'white')
  for j,im in enumerate(ims[k:k+12]): g.paste(im,((j%3)*w,(j//3)*h))
  g.save(f'/home/claude/ai/out/g{N}_{k//12}.jpg')
print(len(ims),'renders')
PY
done
