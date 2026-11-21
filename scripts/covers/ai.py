from base import *
T,O,N='#14DACD','#F38911','#121133'
nodes=[(300,180),(300,280),(300,380),(420,230),(420,330),(540,280)]
g=''.join(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="{T}" stroke-width="3" opacity=".6"/>' for a in nodes[:3] for b in nodes[3:5])
g+=''.join(f'<path d="M{a[0]} {a[1]}L540 280" stroke="{T}" stroke-width="3" opacity=".6"/>' for a in nodes[3:5])
g+=''.join(f'<circle cx="{x}" cy="{y}" r="17" fill="{N}" stroke="{T if i<5 else O}" stroke-width="6"/>' for i,(x,y) in enumerate(nodes))
ai=f'''<g filter="url(#sh)">{g}</g>
<g filter="url(#sh)" transform="translate(600 160)">
 <rect width="210" height="240" rx="22" fill="#fff"/>
 <rect x="24" y="26" width="110" height="13" rx="6.5" fill="#d9dcea"/>
 {''.join(f'<rect x="24" y="{66+i*44}" width="26" height="26" rx="7" fill="none" stroke="{T}" stroke-width="5"/><path d="M30 {79+i*44}l6 7 12-14" fill="none" stroke="{T}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><rect x="62" y="{71+i*44}" width="{120-(i%2)*30}" height="11" rx="5.5" fill="#eceef6"/>' for i in range(3))}
 <rect x="24" y="198" width="26" height="26" rx="7" fill="none" stroke="{O}" stroke-width="5"/><rect x="62" y="205" width="100" height="11" rx="5.5" fill="#d9dcea"/>
</g>
<text x="300" y="470" font-family="Arial" font-weight="700" font-size="44" fill="{T}" opacity=".9">AI</text>'''
open('ai.svg','w').write(page(ai))
