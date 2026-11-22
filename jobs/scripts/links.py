"""Build the 7 link documents of the job-search workshop as PDFs (headless Chrome)."""
import base64, html, os, subprocess
OUT = '/home/claude/jobs/links'
LOGO = base64.b64encode(open('/home/claude/ngqa/site/courses/sql/logo.png', 'rb').read()).decode()
D = [
 ('01-interview-questions-drive', 'תיקיית שאלות מראיונות עבודה', 'Interview Questions — Shared Folder',
  'תיקייה משותפת עם דוגמאות לשאלות מראיונות עבודה בבדיקות תוכנה.',
  [('תיקיית הדוגמאות', [('Google Drive — שאלות מראיונות', 'https://drive.google.com/drive/folders/16QJpZbwY8Mh1OqjDnqUXG8vMf9i-iYuH')])]),
 ('02-interview-question-sites', 'אתרים עם שאלות מראיונות עבודה', 'Interview Questions & Tips — Websites',
  'אתרים עם שאלות מראיונות, טיפים להצלחה בירידי תעסוקה ובראיונות, ושאלות היגיון.',
  [('שאלות מראיונות עבודה', [('JobHunt — פורום שאלות מראיונות', 'http://www.jobhunt.co.il/f/viewforum.php?f=1'),
                            ('GeekInterview — Testing Interview Questions', 'http://www.geekinterview.com/Interview-Questions/Testing')]),
   ('טיפים להצלחה בירידי תעסוקה ובראיונות עבודה', [('Career Tips 4 Geeks', 'http://careertips4geeks.blogspot.com/2011/05/blog-post_08.html'),
      ('NewJob365 — Interview Tips', 'http://www.newjob365.com/interview-tips/'), ('JobIQ', 'http://www.jobiq.co.il/'),
      ('AllJobs — שפת גוף בראיון', 'http://www.alljobs.co.il/ArticlePage.aspx?LinkWord=Body_language'),
      ('Ortal HR', 'http://www.ortal-hr.co.il/?actions=show&id=37&instance_id=5'),
      ('Meditech — ראיון עבודה', 'http://www.meditechr.co.il/19675/%D7%A8%D7%90%D7%99%D7%95%D7%9F-%D7%A2%D7%91%D7%95%D7%93%D7%94'),
      ('ארגון העובדים', 'http://www.ovdim.org.il/Page18673.asp')]),
   ('שאלות היגיון', [('RapidJob — חידות ושאלות', 'http://www.rapidjob.info/info/questions_riddles.htm'),
      ('JobHunt — מאגר ראיונות', 'http://www.jobhunt.co.il/interviews_db.php'),
      ('eMath — פורום חידות והיגיון', 'http://www.emath.co.il/forums/%D7%97%D7%99%D7%93%D7%95%D7%AA-%D7%95%D7%94%D7%99%D7%92%D7%99%D7%95%D7%9F-%D7%91%D7%A8%D7%99%D7%90/340.htm'),
      ('פורום BGU', 'http://forum.bgu.co.il/index.php?showtopic=55149')])]),
 ('03-freelance-remote', 'עבודה כעצמאיים ומרחוק', 'Freelance & Remote Work',
  'אתרים שבהם אפשר למצוא עבודה כעצמאיים ומרחוק, כל אחד בתחומו.',
  [('פלטפורמות לעצמאיים ולעבודה מרחוק', [(n, 'https://' + u) for n, u in [('Upwork', 'www.upwork.com'), ('Fiverr', 'www.fiverr.com'),
     ('Remote.co', 'www.remote.co'), ('We Work Remotely', 'www.weworkremotely.com'), ('FlexJobs', 'www.flexjobs.com'),
     ('Remote OK', 'www.remoteok.io'), ('AngelList', 'www.angel.co/jobs'), ('SimplyHired', 'www.simplyhired.com'),
     ('Working Nomads', 'www.workingnomads.co'), ('Jobspresso', 'www.jobspresso.co'), ('Freelancer', 'www.freelancer.com'),
     ('Guru', 'www.guru.com'), ('Toptal', 'www.toptal.com'), ('PeoplePerHour', 'www.peopleperhour.com'), ('99designs', 'www.99designs.com')]])]),
 ('04-job-search-management', 'כלים לניהול תהליך חיפוש העבודה', 'Job Search Management Tools',
  'כלים שיעזרו לכם לעקוב אחרי משרות, הגשות, ראיונות ומשימות.',
  [('ניהול ומעקב', [(n, u if u.startswith('http') else 'https://' + u) for n, u in [('Trello', 'www.trello.com'), ('JobScan', 'www.jobscan.co'),
     ('JibberJobber', 'www.jibberjobber.com'), ('Huntr', 'www.huntr.co'), ('Teal', 'www.tealhq.com'),
     ('Microsoft To Do', 'https://lnkd.in/gSGSedDr'), ('Evernote', 'www.evernote.com'), ('RescueTime', 'www.rescuetime.com'),
     ('Google Keep', 'keep.google.com'), ('Notion', 'www.notion.so')]])]),
 ('05-technical-assignments', 'הכנה למטלות בית טכניות', 'Technical Home Assignments — Practice',
  'אתרי תרגול למי שצריך להתכונן למטלות בית ולמבחנים טכניים.',
  [('אתרי תרגול', [('LeetCode', 'https://leetcode.com/'), ('HackerRank', 'https://lnkd.in/d322VBBq'), ('HackerEarth', 'https://lnkd.in/dXy7SAcf'),
     ('Codewars', 'https://www.codewars.com'), ('CodeChef', 'https://www.codechef.com/'), ('CodingNinjas', 'https://lnkd.in/dAQiqPYk'),
     ('TopCoder', 'https://www.topcoder.com/'), ('Coderbyte', 'https://coderbyte.com/'), ('Geektastic', 'https://geektastic.com'),
     ('FreeCodeCamp', 'https://lnkd.in/dGGmah9M'), ('GeeksForGeeks', 'https://lnkd.in/dveifGFn')])]),
 ('06-contract-salary-tools', 'כלים לשלב החוזה והשכר', 'Contract & Salary Tools',
  'כלים להשוואת שכר ותנאים — שימושיים לפני משא ומתן על הצעת עבודה.',
  [('השוואת שכר ותנאים', [('Comparably', 'https://lnkd.in/ggZ4xhE7'), ('Levels.fyi', 'http://www.levels.fyi/'), ('Salary.com', 'https://www.salary.com/'),
     ('Glassdoor', 'http://www.glassdoor.com/'), ('Payscale', 'http://www.payscale.com/'), ('PaycheckCity', 'https://lnkd.in/de6hBaxP'),
     ('טבלת השכר של עמותת הבודקים ITCB', 'https://bit.ly/ITCB-Salary-Chart')])]),
 ('07-job-search-groups', 'קבוצות למחפשי עבודה', 'Job Search Groups — WhatsApp, Facebook & LinkedIn',
  'קבוצות וואטסאפ, פייסבוק ולינקדאין עם משרות בבדיקות תוכנה.',
  [('קבוצות וואטסאפ', [('QA Juniors', 'https://chat.whatsapp.com/HZd0IkdGxAY5K40DmZlm9B'), ('J4J Learning', 'https://chat.whatsapp.com/D8BaGT3aOuREOEX8ruAOk8')]),
   ('קבוצות בפייסבוק', [('משרות בדיקות תוכנה – בודקי תוכנה – QA', 'https://www.facebook.com/groups/2368415563415290/'),
      ('משרות QA | הצעות עבודה בתחום ה-QA | דרושים QA', 'https://www.facebook.com/groups/1831968293740695/'),
      ('דרושים – משרות בדיקות תוכנה – QA', 'https://www.facebook.com/groups/749706461749096/'),
      ('דרושים – משרות בדיקות תוכנה – QA (2)', 'https://www.facebook.com/groups/381230202062988/')]),
   ('קבוצות בלינקדאין', [('Search & find a QA Job in Israel', 'https://www.linkedin.com/groups/3055472/'),
      ('QA Jobs & Networking in Israel', 'https://www.linkedin.com/groups/5087484/'), ('QA Jobs in Israel', 'https://www.linkedin.com/groups/8275529/')])]),
]
CSS = '''@page{size:A4;margin:14mm 14mm 16mm}
body{font-family:"Open Sans","DejaVu Sans",Arial,sans-serif;direction:rtl;color:#121133;margin:0;font-size:11pt}
.hd{display:flex;align-items:center;gap:14px;background:#121133;color:#fff;border-radius:14px;padding:14px 18px;margin-bottom:14px}
.hd img{height:58px}.hd h1{margin:0;font-size:21pt;line-height:1.2}.hd .en{color:#14DACD;font-size:10pt;direction:ltr;text-align:right}
.bar{height:4px;width:80px;background:linear-gradient(90deg,#14DACD 70%,#F38911 70%);margin:4px 0 0}
.lead{color:#444;margin:0 4px 12px}.tag{font-size:9pt;color:#F38911;font-weight:700}
h2{font-size:13pt;margin:16px 0 8px;padding-right:10px;border-right:4px solid #F38911}
ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:7px}
li{border:1px solid #dfe3ef;border-radius:10px;padding:8px 11px;break-inside:avoid;background:#fbfcff}
li b{display:block;font-size:10.5pt}li a{color:#0f8f88;font-size:8.6pt;direction:ltr;unicode-bidi:embed;word-break:break-all;text-decoration:none}
.one ul{grid-template-columns:1fr}
.ft{margin-top:18px;border-top:1px solid #dfe3ef;padding-top:6px;font-size:8pt;color:#888;text-align:center}'''
os.makedirs(OUT, exist_ok=True)
for slug, t, en, lead, secs in D:
    body = ''
    for h, items in secs:
        lis = ''.join(f'<li><b>{html.escape(n)}</b><a href="{html.escape(u)}">{html.escape(u)}</a></li>' for n, u in items)
        body += f'<section class="{"one" if len(items) < 3 else ""}"><h2>{html.escape(h)}</h2><ul>{lis}</ul></section>'
    doc = f'''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>{html.escape(t)}</title><style>{CSS}</style></head><body>
<div class="hd"><img src="data:image/png;base64,{LOGO}" alt="NGQA"><div><div class="tag">סדנת מחפשי עבודה · קישורים חשובים</div><h1>{html.escape(t)}</h1><div class="bar"></div><div class="en">{html.escape(en)}</div></div></div>
<p class="lead">{html.escape(lead)} כל הקישורים לחיצים.</p>{body}
<div class="ft">כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה</div></body></html>'''
    hp = f'{OUT}/{slug}.html'; open(hp, 'w').write(doc)
    subprocess.run(['google-chrome', '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={OUT}/{slug}.pdf', 'file://' + hp], capture_output=True, timeout=60)
    print(slug, os.path.getsize(f'{OUT}/{slug}.pdf'))
