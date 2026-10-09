# Smoke test: opens the app in headless Chromium with a fake engine, plays 3 positions of each
# activity, and fails on any page error or missing pool data.
# Needs: pip install playwright (with a Chromium browser).
import asyncio, pathlib, sys
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT/'app'/'index.html').read_text()
CHESS = (ROOT/'vendor'/'chess.js'/'chess.js').read_text()
FAKE = """engineEval = (fen, sm)=>new Promise(res=>{ setTimeout(()=>{ const g=new Chess(fen);
  const ms=sm?sm.split(' '):g.moves({verbose:true}).slice(0,5).map(m=>m.from+m.to+(m.promotion||''));
  res({lines:ms.map((u,i)=>({uci:u,cp:50-i*40,mate:null})), bestUci:ms[0]}); }, 50); });
  fenEvalStore={}; poolEvalStore={}; engineErrorBanner=()=>''; failEngine=()=>{}; sfState='ready'; render();"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width':390,'height':760})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        async def route(r):
            if 'chess.js' in r.request.url: await r.fulfill(body=CHESS, content_type='application/javascript')
            else: await r.abort()
        await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
        await pg.set_content('<!doctype html><html><head><meta charset="utf-8"></head><body>'+SRC+'</body></html>')
        await pg.wait_for_timeout(300)
        await pg.evaluate("(()=>{"+FAKE+"})()")
        sizes = await pg.evaluate("Object.fromEntries(Object.entries(POOLS).map(([k,v])=>[k,v.length]))")
        print('pools', sizes)
        assert all(sizes.get(k,0) > 0 for k in ('analysis','candidates','final')), 'empty pool'
        for act in ['analysis','candidates','final']:
            await pg.click(f'.card[data-go="{act}"]'); await pg.wait_for_timeout(1500)
            for i in range(3):
                title = await pg.evaluate("document.querySelector('.pos-title').innerText.replace(/\\n/g,' · ')")
                if act == 'candidates':
                    await pg.evaluate("(()=>{ const ch=new Chess(pos().fen); const m=ch.moves({verbose:true})[0]; st('candidates').picks=[{id:'c',san:m.san,from:m.from,to:m.to,uci:m.from+m.to,slot:0}]; render(); })()")
                await pg.click('#check'); await pg.wait_for_timeout(4200)
                score = await pg.evaluate("document.querySelector('.layer:not(.ghost) .score').innerText.replace(/\\s+/g,' ')")
                print(act, i, title, '|', score)
                await pg.click('#nextPos'); await pg.wait_for_timeout(600)
            await pg.click('#homeBtn')
        errs = [e for e in errs if 'importScripts' not in e]
        await b.close()
        if errs: print('page errors:', errs); sys.exit(1)
        print('ok')
asyncio.run(main())
