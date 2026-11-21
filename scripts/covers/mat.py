from base import *
T,O,N='#14DACD','#F38911','#121133'
mat=f'''<g filter="url(#sh)">
 <rect x="360" y="80" width="200" height="390" rx="34" fill="#fff"/>
 <rect x="378" y="118" width="164" height="300" rx="10" fill="{N}"/>
 <rect x="440" y="96" width="40" height="8" rx="4" fill="#d9dcea"/><circle cx="460" cy="442" r="14" fill="none" stroke="#d9dcea" stroke-width="4"/>
 {''.join(f'<rect x="{396+(i%3)*50}" y="{140+(i//3)*58}" width="36" height="36" rx="9" fill="{[T,O,"#3b3a7a"][i%3]}"/>' for i in range(9))}
 <rect x="396" y="320" width="128" height="12" rx="6" fill="#3b3a7a"/><rect x="396" y="344" width="96" height="12" rx="6" fill="#3b3a7a"/>
 <circle cx="500" cy="388" r="20" fill="{T}"/><path d="M490 388l7 8 14-16" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</g>
<g filter="url(#sh)" transform="translate(640 270)">
 <circle r="70" fill="rgba(243,137,17,.14)" stroke="{O}" stroke-width="16"/>
 <path d="M50 50l62 62" stroke="{O}" stroke-width="24" stroke-linecap="round"/>
 <g><ellipse rx="20" ry="25" fill="#fff"/><circle cy="-28" r="11" fill="#fff"/>
 <path d="M-20 -6h-14M20 -6h14M-20 10h-15M20 10h15M-17 -19l-11 -9M17 -19l11 -9" stroke="#fff" stroke-width="5" stroke-linecap="round"/></g>
</g>
<g filter="url(#sh)" transform="translate(200 200)" fill="none" stroke="{T}" stroke-width="12" stroke-linecap="round">
 <path d="M0 60a90 90 0 0 1 120 0"/><path d="M25 90a52 52 0 0 1 70 0"/><circle cx="60" cy="122" r="8" fill="{T}" stroke="none"/>
</g>'''
open('mat.svg','w').write(page(mat))
