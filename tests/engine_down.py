# The engine can't be loaded (here: its download is blocked): Check can't be pressed, and the
# message sits below the exercise's card, as on the home page.
import asyncio, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
async def main():
    fails = []
    SITE = (ROOT/'index.html').read_text()
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width':390,'height':760})
        async def route(r):
            u = r.request.url
            if 'chess.js' in u: return await r.fulfill(body=T.CHESS, content_type='application/javascript')
            if u.startswith('https://site.test/'): return await r.fulfill(body=SITE, content_type='text/html')
            await r.abort()
        await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
        await pg.goto('https://site.test/')
        await pg.wait_for_function("sfState==='error'", timeout=60000)
        for a in ['analysis', 'candidates']:
            await pg.evaluate(f"screen='{a}'; render()"); await pg.wait_for_timeout(300)
            st = await pg.evaluate("[document.getElementById('check').disabled, !!document.querySelector('.panel .engine-error'), !!document.querySelector('.panel + .engine-error')]")
            print(a, st)
            if st != [True, False, True]: fails.append(f'{a}: Check enabled or message misplaced: {st}')
        await pg.screenshot(path=str(T.SHOTS/'engine_down.png'))
        await b.close()
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
asyncio.run(main())
