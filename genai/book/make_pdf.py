#!/usr/bin/env python3
import pathlib, asyncio
from playwright.async_api import async_playwright
R=pathlib.Path(__file__).resolve().parent
OUT=R.parents[1]/'site/courses/genai/pdf/NGQA-CT-GenAI-book.pdf'
FOOT='<div style="width:100%;font:9px Arial;color:#888;text-align:center;direction:rtl">NGQA · ספר מסכם CT-GenAI · עמוד <span class="pageNumber"></span> מתוך <span class="totalPages"></span></div>'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        pg=await b.new_page()
        await pg.goto((R/'build/book.html').as_uri(),wait_until='networkidle')
        await pg.evaluate('document.fonts.ready')
        await pg.pdf(path=str(OUT),format='A4',print_background=True,display_header_footer=True,
            header_template='<div></div>',footer_template=FOOT,margin={'top':'16mm','bottom':'18mm','left':'15mm','right':'15mm'})
        await b.close()
asyncio.run(main()); print(OUT, OUT.stat().st_size)
