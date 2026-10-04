# The owner's built-in games: added for the owner only, once; never for another viewer.
import asyncio, sys
from playwright.async_api import async_playwright
import my_games as T
FAKE_CLAUDE = "window.claude = { use: async n => n==='user' ? { isOwner: async()=>%s, id: async()=>'u1' } : null };"
async def run(p, owner, storage=None):
    b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width':390,'height':760}); pg = await ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    async def route(r):
        if 'chess.js' in r.request.url: await r.fulfill(body=T.CHESS, content_type='application/javascript')
        elif r.request.url.startswith('https://app.test/'): await r.fulfill(body='<!doctype html><html><head><meta charset="utf-8"></head><body>'+T.SRC+'</body></html>', content_type='text/html')
        else: await r.abort()
    await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
    await pg.add_init_script(FAKE_CLAUDE % ('true' if owner else 'false'))
    if storage: await pg.add_init_script(storage)
    await pg.goto('https://app.test/'); await pg.wait_for_timeout(300)
    await pg.evaluate("(()=>{"+T.FAKE+" render(); myBackground(); })()")
    await pg.wait_for_timeout(600)
    return b, pg, errs
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await run(p, owner=False)
        n = await pg.evaluate("myGames.length")
        if n: fails.append(f'non-owner got {n} games')
        await b.close()
        b, pg, errs = await run(p, owner=True)
        for _ in range(120):
            st = await pg.evaluate("({games:myGames.length, pending:myGames.flatMap(g=>g.positions).filter(p=>p.act==='pending').length, queued:myGames.filter(g=>g.status==='queued').length})")
            if st['games'] and not st['pending'] and not st['queued']: break
            await pg.wait_for_timeout(500)
        c = await pg.evaluate("countsOf(myPositions)"); print('owner:', st, c, await pg.evaluate("myName"))
        if st['games'] != 50 or st['pending'] or st['queued']: fails.append(f'owner: {st}')
        await pg.click('#myGamesBtn'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(T.SHOTS/'owner_mygames.png'))
        # remove: must not come back on the next load
        await pg.click('#clearBtn'); await pg.click('#clearYes'); await pg.wait_for_timeout(200)
        ls = await pg.evaluate("JSON.stringify(Object.fromEntries(Object.entries(localStorage)))")
        await b.close()
        b, pg, errs2 = await run(p, owner=True, storage=f"Object.entries({ls}).forEach(([k,v])=>localStorage.setItem(k,v));")
        n = await pg.evaluate("myGames.length")
        if n: fails.append(f'removed games came back: {n}')
        await b.close()
    errs = [e for e in errs + errs2 if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
asyncio.run(main())
