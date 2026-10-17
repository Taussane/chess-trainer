# Lists the Position evaluation master positions left out of Imbalance reading: those where the app's
# engine (Stockfish 19 lite, 1.2 s, in the page) and Stockfish 10's static evaluation (staticEval) are
# 2 squares of the bar apart or more (tactics take the evaluation away from them), or where Stockfish gives no breakdown.
# Writes the list into app/index.html (/*IMBALANCE_SKIP*/) and prints, for each imbalance, the
# thresholds that would split the remaining positions 40% = / 40% + or − / 20% ++ or −− (the levels
# in ASPECTS are set from them by hand).
# Needs playwright (pip install playwright) and the site built (python3 scripts/build-site.py).
# Usage: python3 scripts/imbalance-skip.py      (about 1.7 s per position)
import asyncio, json, pathlib, re, subprocess, sys, time
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app' / 'index.html'
CJ = (ROOT / 'vendor' / 'chess.js' / 'chess.js').read_text()
JS = r"""async ()=>{
  const wp = cp=>Math.max(1, Math.min(99, 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1)));
  const eng = fen=>new Promise(res=>{ sfQueue.push({ fen, multipv:1, movetime:1200, resolve:res }); pumpEngineQueue(); });
  const out = [];
  for(const p of POOLS.analysis){
    if(hiddenCastlingLoss(p.fen)) continue;
    const e = aspectsEntry(p.fen);
    for(let i=0; i<100 && e.status!=='done'; i++) await new Promise(r=>setTimeout(r, 50));
    const d = e.data; if(!d) continue;
    const r = await eng(p.fen), l = r.lines && r.lines[0];
    let cp = l ? (l.mate!=null ? (l.mate>0 ? 1e5 : -1e5) : l.cp) : 0; if(p.side==='b') cp = -cp;
    const st = staticEval(p.fen), sum = (st==null ? 0 : st) * 100;   // Stockfish's own static evaluation (what the criteria describe)
    out.push({ key: p.key, far: !!d.special || st==null || Math.abs(wp(sum) - wp(cp)) >= 25, off: d.off.slice(), vals: Object.fromEntries(ASPECTS.map(x=>[x.key, d[x.key]])) });
  }
  return out;
}"""
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
            await pg.goto('http://localhost:8799/index.html'); await pg.wait_for_timeout(1500)
            rows = await pg.evaluate(JS)
            await b.close()
    finally:
        server.terminate()
    skip = [r['key'] for r in rows if r['far']]
    s = APP.read_text(encoding='utf-8')
    s = re.sub(r'/\*IMBALANCE_SKIP\*/.*?/\*END IMBALANCE_SKIP\*/', lambda m: '/*IMBALANCE_SKIP*/' + json.dumps(skip, ensure_ascii=False) + '/*END IMBALANCE_SKIP*/', s, flags=re.S)
    APP.write_text(s, encoding='utf-8')
    kept = [r for r in rows if not r['far']]
    print(len(rows), 'positions,', len(skip), 'left out,', len(kept), 'in Imbalance reading')
    def q(xs, f):
        xs = sorted(xs); i = f * (len(xs) - 1); lo = int(i); return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo)
    for k in kept[0]['vals']:
        a = [abs(r['vals'][k]) for r in kept if k not in r['off']]
        print(f'  {k}: levels for 40/40/20 [{q(a, .4):.3f}, {q(a, .8):.3f}] ({len(a)} positions)')
asyncio.run(main())
