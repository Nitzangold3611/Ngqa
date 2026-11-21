from base import *
T,O,N='#14DACD','#F38911','#121133'
ste=f'''
<g filter="url(#sh)">
 <path d="M480 95l170 62v120c0 110-74 180-170 215c-96-35-170-105-170-215V157z" fill="{T}"/>
 <path d="M480 128l138 50v100c0 90-60 148-138 178c-78-30-138-88-138-178V178z" fill="{N}" opacity=".9"/>
 <rect x="428" y="262" width="104" height="86" rx="14" fill="#fff"/>
 <path d="M448 262v-26a32 32 0 0 1 64 0v26" fill="none" stroke="#fff" stroke-width="14"/>
 <circle cx="480" cy="298" r="12" fill="{N}"/><rect x="474" y="304" width="12" height="24" rx="5" fill="{N}"/>
</g>
<g filter="url(#sh)" transform="translate(660 300)">
 <circle r="70" fill="rgba(243,137,17,.14)" stroke="{O}" stroke-width="16"/>
 <path d="M50 50l62 62" stroke="{O}" stroke-width="24" stroke-linecap="round"/>
 <g><ellipse rx="20" ry="25" fill="#fff"/><circle cy="-28" r="11" fill="#fff"/>
 <path d="M-20 -6h-14M20 -6h14M-20 10h-15M20 10h15M-17 -19l-11 -9M17 -19l11 -9" stroke="#fff" stroke-width="5" stroke-linecap="round"/></g>
</g>
<g filter="url(#sh)" transform="translate(200 210)">
 <rect width="150" height="120" rx="16" fill="#fff"/>
 <rect x="18" y="22" width="80" height="11" rx="5.5" fill="#d9dcea"/><rect x="18" y="46" width="114" height="11" rx="5.5" fill="#eceef6"/>
 <rect x="18" y="70" width="96" height="11" rx="5.5" fill="#d9dcea"/>
 <circle cx="120" cy="96" r="18" fill="{T}"/><path d="M111 96l7 8 12-14" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</g>'''
open('ste.svg','w').write(page(ste))
