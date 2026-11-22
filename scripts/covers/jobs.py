from base import *
T,O,N='#14DACD','#F38911','#121133'
jobs=f'''<g filter="url(#sh)" transform="translate(300 120)">
 <rect width="230" height="300" rx="18" fill="#fff"/>
 <circle cx="56" cy="62" r="30" fill="{T}"/><circle cx="56" cy="54" r="11" fill="#fff"/><path d="M36 82a20 16 0 0 1 40 0" fill="#fff"/>
 <rect x="102" y="44" width="100" height="14" rx="7" fill="{N}"/><rect x="102" y="68" width="70" height="10" rx="5" fill="#d9dcea"/>
 {''.join(f'<rect x="30" y="{122+i*34}" width="{170-(i%3)*30}" height="11" rx="5.5" fill="{["#eceef6","#eceef6",O][i%3] if i!=0 else T}"/>' for i in range(5))}
</g>
<g filter="url(#sh)" transform="translate(570 150)">
 <rect width="180" height="130" rx="18" fill="{N}"/>
 <path d="M30 130l-6 34 40-34z" fill="{N}"/>
 <circle cx="55" cy="66" r="10" fill="{T}"/><circle cx="90" cy="66" r="10" fill="{T}"/><circle cx="125" cy="66" r="10" fill="{O}"/>
</g>
<g filter="url(#sh)" transform="translate(600 330)">
 <rect width="140" height="100" rx="14" fill="{O}"/><rect x="45" y="-22" width="50" height="30" rx="8" fill="none" stroke="{O}" stroke-width="10"/>
 <rect y="40" width="140" height="10" fill="rgba(0,0,0,.15)"/>
</g>'''
open('jobs.svg','w').write(page(jobs))
