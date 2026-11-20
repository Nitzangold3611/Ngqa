import math
W,H=960,540
def traces():
    s='';col=lambda i:'#F38911' if i%4==2 else '#14DACD'
    for i in range(7):
        y=520-i*26;a=40+((i*97)%160);b=18+((i*53)%40);c=30+((i*71)%110)
        s+=f'<path d="M0 {y}H{a}l{b} -{b}H{a+b+c}" stroke="{col(i)}" stroke-width="2" fill="none" opacity=".35"/><circle cx="{a+b+c}" cy="{y-b}" r="4.5" fill="{col(i)}" opacity=".5"/>'
        y2=20+i*26;a2=40+((i*131)%170);b2=18+((i*41)%36);c2=30+((i*83)%100)
        s+=f'<path d="M{W} {y2}H{W-a2}l-{b2} {b2}H{W-a2-b2-c2}" stroke="{col(i+1)}" stroke-width="2" fill="none" opacity=".3"/><circle cx="{W-a2-b2-c2}" cy="{y2+b2}" r="4.5" fill="none" stroke="{col(i+1)}" stroke-width="2" opacity=".5"/>'
    return s
def page(inner):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><radialGradient id="g" cx="50%" cy="48%" r="60%"><stop offset="0" stop-color="#232161"/><stop offset="1" stop-color="#121133"/></radialGradient>
<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#000" flood-opacity=".35"/></filter></defs>
<rect width="{W}" height="{H}" fill="url(#g)"/>{traces()}{inner}</svg>'''
