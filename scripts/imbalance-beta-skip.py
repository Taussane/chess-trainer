# Lists the Imbalance reading positions whose grades, added up, disagree with the engine: the
# engine (master-evals.json: the finder's search, the app's engine at 1.2 s) has one side 1.0 or more
# ahead, and the grades' sum (+ 1, ++ 2, from White's side; Development in place of Activity while a
# knight or bishop has never moved) is "=" or leans the other way. Writes the list into app/index.html
# (/*IMBALANCE_SKIP_BETA*/), with the positions where every criterion is "="; the app leaves those positions out too (on top of IMBALANCE_SKIP).
# And, for the beta only (/*IMBALANCE_SKIP_PICK*/), the positions where Stockfish 10's own terms read the
# decisive criteria otherwise (pickDisagrees, below).
# Needs playwright and the site built (python3 scripts/build-site.py). Usage: python3 scripts/imbalance-beta-skip.py
import asyncio, json, pathlib, re, subprocess, sys, time
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app' / 'index.html'
CJ = (ROOT / 'vendor' / 'chess.js' / 'chess.js').read_text()
EVALS = json.loads((ROOT / 'master-evals.json').read_text())
JS = r"""()=>{
// The beta's check (choose the decisive criteria): Stockfish 10's own term for each criterion (parseAspects,
// in pawns; Material left out, a plain count, and Activity while it's Development, King safety in an
// endgame, King activity) against our grade: one of its three biggest (half a pawn or more) on the other
// side, or one of our ++ that it reads the other way or next to nothing (under 0.1).
const pickDisagrees = (fen, d)=>{
  const raw = parseAspects(sfTableLines(fen), fen); if(!raw) return false;
  const xs = ASPECTS.filter(x=>x.key!=='material' && !d.off.includes(x.key) && !(x.key==='activity' && devActive(fen)) && !(x.key==='king' && isEndgame(fen)));
  const lv = x=>aspectLevel(d[x.key], x.key), top = xs.slice().sort((a, b)=>Math.abs(raw[b.key]) - Math.abs(raw[a.key])).slice(0, 3).filter(x=>Math.abs(raw[x.key]) >= 0.5);
  return top.some(x=>lv(x) && Math.sign(lv(x))!==Math.sign(raw[x.key]))
      || xs.some(x=>Math.abs(lv(x))===2 && (Math.abs(raw[x.key]) < 0.1 || Math.sign(raw[x.key])!==Math.sign(lv(x))));
};
return POOLS.analysis.filter(p=>!IMBALANCE_SKIP.includes(p.key)).map(p=>{
  let d = null; try{ d = adaptAspects(parseAspects(sfTableLines(p.fen), p.fen), p.fen); }catch(e){}
  if(!d) return { key: p.key, sum: null };
  return { key: p.key, side: p.side, sum: ASPECTS.reduce((s, x)=>s + (d.off.includes(x.key) ? 0 : aspectLevel(d[x.key], x.key)), 0),
           graded: ASPECTS.some(x=>!d.off.includes(x.key) && aspectLevel(d[x.key], x.key)), pick: pickDisagrees(p.fen, d) };
});}"""
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
    skip, pick = [], []
    for r in rows:
        e = EVALS.get(r['key'])
        if r['sum'] is None or not e: continue
        cp = (1e5 if e[2] > 0 else -1e5) if e[2] is not None else e[1]
        if r['side'] == 'b': cp = -cp   # mover's point of view -> White's
        if abs(cp) >= 100 and (r['sum'] == 0 or (r['sum'] > 0) != (cp > 0)): skip.append(r['key'])
        elif not r['graded']: skip.append(r['key'])   # every criterion "=": nothing to choose (the beta grades 1 to 3, never "=")
        elif r.get('pick'): pick.append(r['key'])   # the beta only: Stockfish 10 reads the decisive criteria otherwise
    s = APP.read_text(encoding='utf-8')
    s = re.sub(r'/\*IMBALANCE_SKIP_BETA\*/.*?/\*END IMBALANCE_SKIP_BETA\*/', lambda m: '/*IMBALANCE_SKIP_BETA*/' + json.dumps(skip, ensure_ascii=False) + '/*END IMBALANCE_SKIP_BETA*/', s, flags=re.S)
    s = re.sub(r'/\*IMBALANCE_SKIP_PICK\*/.*?/\*END IMBALANCE_SKIP_PICK\*/', lambda m: '/*IMBALANCE_SKIP_PICK*/' + json.dumps(pick, ensure_ascii=False) + '/*END IMBALANCE_SKIP_PICK*/', s, flags=re.S)
    APP.write_text(s, encoding='utf-8')
    print(len(rows), 'positions,', len(skip), 'left out on both sites,', len(pick), 'more on beta,', len(rows) - len(skip) - len(pick), 'kept on beta')
asyncio.run(main())
