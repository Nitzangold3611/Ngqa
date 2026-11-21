from base import *
T,O,N,WT='#14DACD','#F38911','#121133','#FFFFFF'
# --- CTFL: checklist + magnifier + bug ---
ctfl=f'''
<g filter="url(#sh)">
 <rect x="300" y="110" width="270" height="330" rx="26" fill="#fff"/>
 <rect x="390" y="92" width="90" height="38" rx="12" fill="{O}"/>
 {''.join(f'<rect x="335" y="{170+i*62}" width="34" height="34" rx="8" fill="none" stroke="{T}" stroke-width="5"/><path d="M342 {187+i*62}l8 9 16-19" fill="none" stroke="{T}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><rect x="388" y="{176+i*62}" width="{140-(i%2)*40}" height="11" rx="5.5" fill="#d9dcea"/><rect x="388" y="{193+i*62}" width="{90-(i%3)*15}" height="9" rx="4.5" fill="#eceef6"/>' if i<3 else f'<rect x="335" y="{170+i*62}" width="34" height="34" rx="8" fill="none" stroke="{O}" stroke-width="5"/><rect x="388" y="{176+i*62}" width="120" height="11" rx="5.5" fill="#d9dcea"/>' for i in range(4))}
</g>
<g filter="url(#sh)">
 <circle cx="610" cy="300" r="92" fill="rgba(20,218,205,.12)" stroke="{T}" stroke-width="18"/>
 <path d="M676 366l78 78" stroke="{T}" stroke-width="26" stroke-linecap="round"/>
 <circle cx="610" cy="300" r="60" fill="#fff" opacity=".1"/>
 <g transform="translate(610 302)">
  <ellipse rx="26" ry="32" fill="{O}"/><circle cy="-36" r="15" fill="{O}"/>
  <path d="M-26 -8h-18M26 -8h18M-26 12h-20M26 12h20M-22 -24l-14 -12M22 -24l14 -12" stroke="{O}" stroke-width="6" stroke-linecap="round"/>
  <path d="M0 -26v56" stroke="{N}" stroke-width="4"/>
 </g>
</g>'''
# --- GenAI: chat bubble with sparkles + neural nodes + check ---
nodes=[(250,170),(250,270),(250,370),(360,220),(360,320)]
gen='<g opacity=".9">'+''.join(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="{T}" stroke-width="3" opacity=".55"/>' for a in nodes[:3] for b in nodes[3:])+''.join(f'<path d="M{a[0]} {a[1]}L470 {270}" stroke="{T}" stroke-width="3" opacity=".55"/>' for a in nodes[3:])+''.join(f'<circle cx="{x}" cy="{y}" r="15" fill="{N}" stroke="{T}" stroke-width="5"/>' for x,y in nodes)+'</g>'
def star(cx,cy,r,c): return f'<path d="M{cx} {cy-r}C{cx+r*.18} {cy-r*.18} {cx+r*.18} {cy-r*.18} {cx+r} {cy}C{cx+r*.18} {cy+r*.18} {cx+r*.18} {cy+r*.18} {cx} {cy+r}C{cx-r*.18} {cy+r*.18} {cx-r*.18} {cy+r*.18} {cx-r} {cy}C{cx-r*.18} {cy-r*.18} {cx-r*.18} {cy-r*.18} {cx} {cy-r}Z" fill="{c}"/>'
gen+=f'''
<g filter="url(#sh)">
 <path d="M470 150h250a34 34 0 0 1 34 34v150a34 34 0 0 1-34 34H585l-58 48v-48h-57a34 34 0 0 1-34-34V184a34 34 0 0 1 34-34z" fill="#fff"/>
 <rect x="478" y="196" width="190" height="14" rx="7" fill="#d9dcea"/><rect x="478" y="224" width="230" height="14" rx="7" fill="#d9dcea"/><rect x="478" y="252" width="150" height="14" rx="7" fill="#eceef6"/>
 <circle cx="700" cy="318" r="34" fill="{T}"/><path d="M684 318l11 12 22-25" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
</g>
{star(760,130,40,O)}{star(820,205,20,T)}{star(705,95,14,'#fff')}'''
# --- SQL (ready for the next course): database + table ---
sql=f'''
<g filter="url(#sh)">
 <g transform="translate(330 120)">
  <path d="M0 40v220c0 26 60 46 130 46s130-20 130-46V40" fill="{T}"/>
  <ellipse cx="130" cy="40" rx="130" ry="40" fill="#5ff0e6"/>
  <path d="M0 120c0 26 60 46 130 46s130-20 130-46M0 195c0 26 60 46 130 46s130-20 130-46" fill="none" stroke="{N}" stroke-width="7" opacity=".35"/>
 </g>
 <g transform="translate(560 200)">
  <rect width="250" height="190" rx="18" fill="#fff"/>
  <rect width="250" height="46" rx="18" fill="{O}"/><rect y="28" width="250" height="18" fill="{O}"/>
  {''.join(f'<rect x="{18+c*80}" y="{66+r*38}" width="{60}" height="14" rx="7" fill="{"#d9dcea" if (r+c)%2 else "#eceef6"}"/>' for r in range(3) for c in range(3))}
  <path d="M0 98h250M0 136h250M83 46v144M166 46v144" stroke="#e1e3ef" stroke-width="2"/>
 </g>
</g>'''
for n,s in (('ctfl',ctfl),('genai',gen),('sql',sql)):
    open(f'{n}.svg','w').write(page(s))
print('ok')
