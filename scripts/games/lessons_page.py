#!/usr/bin/env python3
"""Writes /courses/<c>/lessons/index.html (recorded lessons page, v3.13) for every course.
The lessons themselves come from the backoffice (Netlify Blobs) through /lessons.js."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
NAMES = {'ctfl': 'CTFL 4.0', 'genai': 'CT-GenAI', 'sql': 'SQL', 'ste': 'CT-STE', 'ai': 'CT-AI', 'mat': 'CT-MAT', 'jobs': 'סדנת מחפשי עבודה'}
T = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<script src="/auth.js"></script>
<script>document.documentElement.style.visibility='hidden';
NGQAAuth.guard('__C__').then(async ok=>{if(!ok)return;const A=NGQAAuth,i=A.info(await A.session());await A.config();
  if(!A.canRec(i,'__C__')){location.replace('/courses/__C__/?norec=1');return}
  document.documentElement.style.visibility=''}).catch(()=>{document.documentElement.style.visibility=''});</script>
<script>try{const t=localStorage.getItem('ngqa-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>שיעורים מוקלטים · __N__ | NGQA</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
:root{color-scheme:light dark;--navy:#121133;--teal:#14DACD;--teal-d:#0E9F97;--orange:#F38911;
--bg:light-dark(#f4f6fb,#0b0a24);--card:light-dark(#fff,#18173f);--ink:light-dark(#121133,#eef0ff);--mute:light-dark(#5d5c7c,#a9a8cf);--line:light-dark(#e1e3ef,#2a2960)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 Heebo,Arial,sans-serif}
a{color:inherit}
.bar{background:var(--navy);color:#fff;display:flex;gap:10px;align-items:center;padding:10px max(3vw,14px)}
.bar img{height:34px}.bar b{flex:1;font-size:18px}.bar a{color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:6px 14px;text-decoration:none;font-size:15px;white-space:nowrap}
.wrap{max-width:1240px;margin:auto;padding:22px max(3vw,14px)}
footer{text-align:center;color:var(--mute);font-size:14px;padding:22px}
</style>
</head>
<body>
<div class="bar"><img src="/logo.png" alt="NGQA"><b>שיעורים מוקלטים · __N__</b><a href="../">חזרה לקורס</a></div>
<main class="wrap" id="ls"></main>
<footer>כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה</footer>
<script src="/lessons.js"></script>
<script>(async()=>{let decks=[];try{decks=await (await fetch('../decks.json')).json()}catch(e){}
  NGQALessons.render(document.getElementById('ls'),{c:'__C__',decks,only:'',base:'../',hash:true})})();</script>
</body>
</html>
'''
def write(c):
    d = ROOT / 'site/courses' / c / 'lessons'; d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(T.replace('__C__', c).replace('__N__', NAMES[c]), encoding='utf-8')
if __name__ == '__main__':
    for c in (sys.argv[1:] or list(NAMES)): write(c); print(c)
