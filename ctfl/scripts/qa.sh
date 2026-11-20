#!/bin/bash
# qa.sh deck.pptx outdir
S=/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx
rm -rf $2 && mkdir -p $2 && cp "$1" $2/deck.pptx && cd $2 && timeout 600 python3 $S/scripts/office/soffice.py --headless --convert-to pdf deck.pptx >/dev/null 2>&1; pdftoppm -jpeg -r ${3:-80} deck.pdf s; python3 -c "
from PIL import Image
import glob
fs=sorted(glob.glob('s-*.jpg'))
for k in range(0,len(fs),9):
  ims=[Image.open(f) for f in fs[k:k+9]];w,h=ims[0].size
  c=Image.new('RGB',(w*3,h*3),'white')
  for i,im in enumerate(ims):c.paste(im,((i%3)*w,(i//3)*h))
  c.save(f'g{k//9}.jpg')
print(len(fs))"
