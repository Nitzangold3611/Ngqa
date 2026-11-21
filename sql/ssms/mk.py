"""SSMS 22 interface illustrations (HTML/CSS -> PNG) for the SQL deck, chapter 1."""
import asyncio, os
from playwright.async_api import async_playwright
OUT = os.path.dirname(os.path.abspath(__file__))
CSS = '''
*{box-sizing:border-box}body{margin:0;background:transparent;font:13px "Segoe UI",Arial,sans-serif;color:#1e1e1e}
.win{width:1200px;height:700px;background:#f3f3f3;border:1px solid #c8c8c8;border-radius:8px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 8px 30px rgba(0,0,0,.18)}
.tb{height:34px;background:#eeeef2;display:flex;align-items:center;padding:0 12px;gap:10px;border-bottom:1px solid #dcdce4}
.tb .logo{width:18px;height:18px;border-radius:4px;background:#68217a;color:#fff;font-size:10px;font-weight:700;display:grid;place-items:center}
.tb .t{font-size:12.5px;color:#333}.tb .sp{flex:1}.tb .wc{display:flex;gap:18px;color:#555;font-size:14px}
.menu{height:28px;display:flex;align-items:center;gap:16px;padding:0 12px;background:#eeeef2;font-size:13px;color:#222}
.tool{height:40px;display:flex;align-items:center;gap:8px;padding:0 10px;background:#f5f5f8;border-bottom:1px solid #dcdce4}
.btn{display:flex;align-items:center;gap:6px;padding:4px 9px;border-radius:4px;font-size:13px;color:#222;border:1px solid transparent}
.btn .i{width:16px;height:16px;border-radius:3px;background:#c9d6ef;display:inline-block}
.btn.nq .i{background:#ffd76a;border:1px solid #d1a52a}
.btn.ex .i{width:0;height:0;border-left:12px solid #2e9e44;border-top:7px solid transparent;border-bottom:7px solid transparent;border-radius:0;background:none}
.dd{border:1px solid #c5c5d0;background:#fff;border-radius:3px;padding:3px 26px 3px 8px;font-size:13px;position:relative;min-width:150px}
.dd:after{content:"▾";position:absolute;right:8px;top:2px;color:#555}
.sep{width:1px;height:22px;background:#d0d0da}
.hl{border:2px solid #F38911!important;background:#fff4e5!important;box-shadow:0 0 0 4px rgba(243,137,17,.25)}
.body{flex:1;display:flex;min-height:0}
.oe{width:330px;background:#fff;border-right:1px solid #d6d6de;display:flex;flex-direction:column}
.ph{height:30px;display:flex;align-items:center;padding:0 10px;font-size:12.5px;background:#e8e8ee;color:#333;border-bottom:1px solid #d6d6de;gap:8px}
.ph .x{margin-left:auto;color:#777}
.oetool{height:28px;display:flex;align-items:center;gap:10px;padding:0 10px;font-size:12px;color:#444;border-bottom:1px solid #eee}
.tree{padding:6px 0;font-size:13px;line-height:24px}
.tree div{white-space:nowrap;padding-left:calc(10px + var(--l,0)*18px);display:flex;align-items:center;gap:6px}
.tree .tg{width:12px;color:#666;font-size:10px;text-align:center}
.fd{width:15px;height:12px;background:#e8c35a;border-radius:2px;display:inline-block}
.db{width:13px;height:14px;background:#7a8fb3;border-radius:6px/3px;display:inline-block}
.sv{width:15px;height:14px;background:#4b6fae;border-radius:2px;display:inline-block}
.tbl{width:14px;height:12px;border:1.5px solid #6a7a9a;background:linear-gradient(#6a7a9a 0 3px,#fff 3px);display:inline-block}
.sel{background:#cce4f7;outline:1px solid #8fc3eb}
.main{flex:1;display:flex;flex-direction:column;min-width:0;background:#fff}
.tabs{height:30px;display:flex;align-items:flex-end;background:#eeeef2;border-bottom:1px solid #d6d6de;padding-left:6px}
.tab{background:#fff;border:1px solid #d6d6de;border-bottom:0;padding:5px 12px;font-size:12.5px;border-radius:4px 4px 0 0;display:flex;gap:10px}
.tab b{font-weight:400;color:#68217a}
.ed{flex:1;font:14px Consolas,monospace;padding:10px 0;position:relative;min-height:0;display:flex}
.ln{width:44px;color:#2b91af;text-align:right;padding-right:10px}
.code{flex:1;white-space:pre}
.k{color:#0000ff}.s{color:#a31515}
.cur{display:inline-block;width:2px;height:16px;background:#000;vertical-align:-3px}
.empty{flex:1;display:grid;place-items:center;color:#9a9aa8;font-size:14px;background:#f7f7fa}
.res{height:250px;border-top:1px solid #d6d6de;display:flex;flex-direction:column}
.rtabs{height:28px;display:flex;align-items:center;gap:16px;padding:0 10px;font-size:12.5px;background:#f3f3f6;border-bottom:1px solid #e0e0e6}
.rtabs .on{border-bottom:2px solid #68217a;padding-bottom:3px}
table{border-collapse:collapse;font-size:12.5px;margin:4px 6px}
th{background:#f0f0f0;border:1px solid #d6d6d6;font-weight:400;text-align:left;padding:3px 8px;color:#333}
td{border:1px solid #e3e3e3;padding:3px 8px;white-space:nowrap}
td.n{background:#f0f0f0;color:#666;text-align:right}
.status{height:26px;background:#fff3c4;border-top:1px solid #e6d58a;display:flex;align-items:center;gap:22px;padding:0 10px;font-size:12px;color:#333}
.status .ok{color:#2e7d32}
.sb{height:24px;background:#68217a;color:#fff;font-size:12px;display:flex;align-items:center;padding:0 10px;gap:20px}
/* connect dialog */
.dlg{width:560px;background:#fff;border:1px solid #bdbdc8;border-radius:8px;box-shadow:0 12px 34px rgba(0,0,0,.22);font-size:13.5px;overflow:hidden}
.dlg .h{padding:14px 18px 6px;font-size:18px;font-weight:600}
.dlg .s{padding:0 18px 10px;color:#666;font-size:12.5px}
.row{display:flex;align-items:center;padding:7px 18px;gap:12px}
.row label{width:150px;color:#333}.row .f{flex:1;border:1px solid #c5c5d0;border-radius:4px;padding:6px 8px;background:#fff;position:relative}
.row .f.d:after{content:"▾";position:absolute;right:10px;color:#555}
.chk{display:flex;align-items:center;gap:8px;padding:7px 18px 7px 180px}
.chk i{width:15px;height:15px;border:1.5px solid #555;border-radius:3px;display:inline-grid;place-items:center;font-style:normal;font-size:11px;background:#fff}
.dlg .ft{display:flex;justify-content:flex-end;gap:10px;padding:14px 18px;background:#f7f7f9;border-top:1px solid #e6e6ec;margin-top:8px}
.b2{padding:6px 18px;border-radius:4px;border:1px solid #c5c5d0;background:#fff}.b2.p{background:#68217a;color:#fff;border-color:#68217a}
'''


def shell(title_db, tree_sel, main, toolbar_hl=None, status=''):
    nq = 'btn nq hl' if toolbar_hl == 'nq' else 'btn nq'
    ex = 'btn ex hl' if toolbar_hl == 'ex' else 'btn ex'
    dd = 'dd hl' if toolbar_hl == 'dd' else 'dd'
    nw_sel = ' sel' if tree_sel == 'nw' else ''
    db_sel = ' sel' if tree_sel == 'dbs' else ''
    open_nw = tree_sel in ('nw', 'tables')
    tree = f'''<div><span class="tg">▾</span><span class="sv"></span>localhost\\SQLEXPRESS (SQL Server 17.0)</div>
<div style="--l:1" class="{db_sel.strip()}"><span class="tg">▾</span><span class="fd"></span>Databases</div>
<div style="--l:2"><span class="tg">▸</span><span class="fd"></span>System Databases</div>
<div style="--l:2"><span class="tg">▸</span><span class="fd"></span>Database Snapshots</div>
<div style="--l:2" class="{nw_sel.strip()}"><span class="tg">{'▾' if open_nw else '▸'}</span><span class="db"></span>Northwind</div>'''
    if open_nw:
        tree += '''<div style="--l:3"><span class="tg">▸</span><span class="fd"></span>Database Diagrams</div>
<div style="--l:3"><span class="tg">▾</span><span class="fd"></span>Tables</div>
<div style="--l:4"><span class="tg">▸</span><span class="fd"></span>System Tables</div>''' + ''.join(
            f'<div style="--l:4"><span class="tg">▸</span><span class="tbl"></span>dbo.{t}</div>'
            for t in ('Categories', 'Customers', 'Employees', 'Order Details', 'Orders', 'Products', 'Shippers', 'Suppliers'))
    tree += '''<div style="--l:1"><span class="tg">▸</span><span class="fd"></span>Security</div>
<div style="--l:1"><span class="tg">▸</span><span class="fd"></span>Server Objects</div>
<div style="--l:1"><span class="tg">▸</span><span class="fd"></span>Management</div>'''
    return f'''<div class="win">
<div class="tb"><span class="logo">SQL</span><span class="t">SQL Server Management Studio 22</span><span class="sp"></span><span class="wc">—&nbsp;&nbsp;☐&nbsp;&nbsp;✕</span></div>
<div class="menu"><span>File</span><span>Edit</span><span>View</span><span>Query</span><span>Git</span><span>Project</span><span>Tools</span><span>Extensions</span><span>Window</span><span>Help</span></div>
<div class="tool"><span class="{nq}"><span class="i"></span>New Query</span><span class="sep"></span><span class="{dd}">{title_db}</span><span class="{ex}"><span class="i"></span>Execute</span><span class="btn">■</span><span class="btn">✓</span><span class="sep"></span><span class="btn"><span class="i"></span></span><span class="btn"><span class="i"></span></span></div>
<div class="body"><div class="oe"><div class="ph">Object Explorer<span class="x">✕</span></div><div class="oetool">Connect ▾ &nbsp; ⟲ &nbsp; ▽</div><div class="tree">{tree}</div></div>
<div class="main">{main}</div></div>
<div class="sb"><span>Ready</span></div></div>'''


EDITOR = lambda code, res=None: (
    '<div class="tabs"><span class="tab">SQLQuery1.sql - localhost\\SQLEXPRESS.Northwind <b>✕</b></span></div>'
    f'<div class="ed"><div class="ln">{"<br>".join(str(i) for i in range(1, 9))}</div><div class="code">{code}</div></div>'
    + (res or ''))
RES = '''<div class="res"><div class="rtabs"><span class="on">Results</span><span>Messages</span></div><div style="overflow:hidden">
<table><tr><th></th><th>CustomerID</th><th>CompanyName</th><th>ContactName</th><th>City</th><th>Country</th></tr>''' + ''.join(
    f'<tr><td class="n">{i}</td><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td></tr>' for i, (a, b, c, d, e) in enumerate([
        ('ALFKI', 'Alfreds Futterkiste', 'Maria Anders', 'Berlin', 'Germany'),
        ('ANATR', 'Ana Trujillo Emparedados y helados', 'Ana Trujillo', 'México D.F.', 'Mexico'),
        ('ANTON', 'Antonio Moreno Taquería', 'Antonio Moreno', 'México D.F.', 'Mexico'),
        ('AROUT', 'Around the Horn', 'Thomas Hardy', 'London', 'UK'),
        ('BERGS', 'Berglunds snabbköp', 'Christina Berglund', 'Luleå', 'Sweden'),
        ('BLAUS', 'Blauer See Delikatessen', 'Hanna Moos', 'Mannheim', 'Germany')], 1)) + '''</table></div>
<div class="status" style="margin-top:auto"><span class="ok">✔ Query executed successfully.</span><span>localhost\\SQLEXPRESS</span><span>Northwind</span><span>91 rows</span></div></div>'''
EMPTY = '<div class="empty">לחיצה על New Query פותחת חלון שאילתה חדש</div>'
SCENES = {
    'oe_nw': shell('Northwind', 'nw', EMPTY),
    'oe_dbs': shell('master', 'dbs', EMPTY),
    'newq': shell('Northwind', 'nw', EMPTY, 'nq'),
    'editor': shell('Northwind', 'nw', EDITOR('<span class="cur"></span>')),
    'exec': shell('Northwind', 'nw', EDITOR('<span class="k">SELECT</span> * <span class="k">FROM</span> Customers;', RES), 'ex'),
    'connect': '''<div class="dlg"><div class="h">Connect to Server</div><div class="s">Database Engine</div>
<div class="row"><label>Server type</label><div class="f d">Database Engine</div></div>
<div class="row"><label>Server name</label><div class="f d hl">localhost\\SQLEXPRESS</div></div>
<div class="row"><label>Authentication</label><div class="f d">Windows Authentication</div></div>
<div class="row"><label>Database name</label><div class="f d">&lt;default&gt;</div></div>
<div class="row"><label>Encrypt</label><div class="f d">Mandatory</div></div>
<div class="chk hl" style="margin:4px 18px 4px 180px;padding:5px 8px;border-radius:4px"><i>✓</i>Trust server certificate</div>
<div class="ft"><span class="b2">Cancel</span><span class="b2 p">Connect</span></div></div>''',
}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg = await b.new_page(viewport={'width': 1260, 'height': 760}, device_scale_factor=2)
        for k, h in SCENES.items():
            await pg.set_content(f'<style>{CSS}</style><div id="w" style="display:inline-block;padding:14px">{h}</div>')
            await pg.wait_for_timeout(100)
            el = await pg.query_selector('#w')
            await el.screenshot(path=f'{OUT}/{k}.png', omit_background=True)
        await b.close()
asyncio.run(main())
print('ok')
