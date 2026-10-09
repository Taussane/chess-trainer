# 190 games saved in the browser, then the page loads: it must never freeze for long (positions are
# found a few games at a time), and the next load reuses the positions already found.
import asyncio, sys, json, pathlib
sys.path.insert(0, '/home/claude/chess-trainer/tests')
import my_games as T
from playwright.async_api import async_playwright
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        await pg.click('#accountBtn'); await pg.set_input_files('#pgnFile', T.SAMPLE); await pg.wait_for_timeout(300)
        await pg.evaluate("importPgnText(%s, false, 'TestPlayer')" % json.dumps(pathlib.Path('/home/claude/chess-trainer/tests/chesscom-sample.pgn').read_text()))
        await pg.wait_for_timeout(2000)
        saved = await pg.evaluate("""(()=>{ myGames.forEach(g=>{ if(!g.evals){ g.evals = g.sans.map((s,i)=>({cp: Math.round(80*Math.sin(i*1.7))})); g.evalBy='scan'; g.status='evaluated'; } });
           const out=[]; for(let k=0;k<11;k++) myGames.forEach(g=>out.push({...g, id:g.id+'x'+k})); return JSON.stringify(out.slice(0,200)); })()""")
        await b.close()
        for label in ('first load (nothing found yet)', 'next load (positions kept)'):
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width':390,'height':760}); pg = await ctx.new_page()
            async def route(r):
                if 'chess.js' in r.request.url: await r.fulfill(body=T.CHESS, content_type='application/javascript')
                elif r.request.url.startswith('https://app.test/'): await r.fulfill(body='<!doctype html><html><head><meta charset="utf-8"></head><body>'+T.SRC+'</body></html>', content_type='text/html')
                else: await r.abort()
            await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
            await pg.add_init_script("window.claude = { use: async()=>null }; window.__longest=0; new PerformanceObserver(l=>l.getEntries().forEach(e=>{ window.__longest=Math.max(window.__longest, Math.round(e.duration)); })).observe({type:'longtask', buffered:true});")
            await pg.add_init_script(f"localStorage.setItem('cst.mygames.v1', {saved!r});")
            await pg.goto('https://app.test/'); await pg.wait_for_timeout(5000)
            r = await pg.evaluate("[myGames.length, myPositions.length, (window.__longest||0)]")
            print(label, '| games, positions, longest freeze (ms):', r)
            if r[0] != 190 or r[1] < 1000 or r[2] > 400: fails.append(f'{label}: {r}')
            saved = await pg.evaluate("localStorage.getItem('cst.mygames.v1')")
            await b.close()
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
asyncio.run(main())
