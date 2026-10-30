# Lists the Imbalance reading positions whose grades, added up, disagree with the engine: the
# engine (master-evals.json: the finder's search, the app's engine at 1.2 s) has one side 1.0 or more
# ahead, and the grades' sum (+ 1, ++ 2, from White's side; Development in place of Activity while a
# knight or bishop has never moved) is "=" or leans the other way. Writes the list into app/index.html
# (/*IMBALANCE_SKIP_BETA*/); the app leaves those positions out too (on top of IMBALANCE_SKIP).
# Needs playwright and the site built (python3 scripts/build-site.py). Usage: python3 scripts/imbalance-beta-skip.py
import asyncio, json, pathlib, re, subprocess, sys, time
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app' / 'index.html'
CJ = (ROOT / 'vendor' / 'chess.js' / 'chess.js').read_text()
EVALS = json.loads((ROOT / 'master-evals.json').read_text())
JS = r"""()=>POOLS.analysis.filter(p=>!IMBALANCE_SKIP.includes(p.key)).map(p=>{
  let d = null; try{ d = adaptAspects(parseAspects(sfTableLines(p.fen), p.fen), p.fen); }catch(e){}
  if(!d) return { key: p.key, sum: null };
  return { key: p.key, side: p.side, sum: ASPECTS.reduce((s, x)=>s + (d.off.includes(x.key) ? 0 : aspectLevel(d[x.key], x.key)), 0) };
})"""
async def main():
    server = subprocess.Popen([sys.executable, '-m', 'http.server', '8799'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(); pg.set_default_timeout(0)
            async def route(r):
                u = r.request.url
                if u.startswith('http://localhost'): await r.continue_()
                elif 'chess.js' in u: await r.fulfill(body=CJ, content_type='application/javascript')
                else: await r.abort()
            await pg.route('**/*', lambda r: asyncio.ensure_future(route(r)))
            await pg.goto('http://localhost:8799/beta/index.html'); await pg.wait_for_timeout(2000)
            assert await pg.evaluate('DEV_ON'), 'Development is off'
            rows = await pg.evaluate(JS)
            await b.close()
    finally:
        server.terminate()
    skip = []
    for r in rows:
        e = EVALS.get(r['key'])
        if r['sum'] is None or not e: continue
        cp = (1e5 if e[2] > 0 else -1e5) if e[2] is not None else e[1]
        if r['side'] == 'b': cp = -cp   # mover's point of view -> White's
        if abs(cp) >= 100 and (r['sum'] == 0 or (r['sum'] > 0) != (cp > 0)): skip.append(r['key'])
    s = APP.read_text(encoding='utf-8')
    s = re.sub(r'/\*IMBALANCE_SKIP_BETA\*/.*?/\*END IMBALANCE_SKIP_BETA\*/', lambda m: '/*IMBALANCE_SKIP_BETA*/' + json.dumps(skip, ensure_ascii=False) + '/*END IMBALANCE_SKIP_BETA*/', s, flags=re.S)
    APP.write_text(s, encoding='utf-8')
    print(len(rows), 'positions,', len(skip), 'left out on beta,', len(rows) - len(skip), 'kept')
asyncio.run(main())
