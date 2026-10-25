# Lists the master positions offered first, to a player's first 10 positions of each exercise
# (FIRST_POSITIONS in the app): clear, representative ones, while the hints are on.
#  - Imbalance reading: 3 or more imbalances not "=" (the side they favour noted, and whether both sides
#    have some), from the app's own grading in the page.
#  - Position evaluation: not close to balanced: one side 1.50 or more ahead (finder's evaluation), its sign noted.
#  - Candidate moves: 3 or more good moves among the top 5 (decentMoves), so not a lone move among traps.
#  - Move selection: any position (the app takes care that the moves start out of order).
# Writes the lists into app/index.html (/*STARTERS*/ ... /*END STARTERS*/). Run after finder/inject.py and
# scripts/build-site.py (Imbalance reading reads the built site).
# Usage: python3 scripts/starters.py
import asyncio, json, pathlib, re, subprocess, sys, time
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app' / 'index.html'
CJ = (ROOT / 'vendor' / 'chess.js' / 'chess.js').read_text()
EVAL_MIN = 150     # centipawns: Position evaluation's starters
IMB_MIN = 3        # imbalances not "="
DECENT_MIN = 3     # good moves among the top 5

pools = json.loads((ROOT / 'data' / 'pools.json').read_text())['pools']
key = lambda e: f"{int(e['game'][1:])}:{e['ply']}"   # a position as game number:half-moves (the app's p.game, p.ply), far shorter than its FEN
analysis = {}
for e in pools['analysis']:
    m = e.get('metrics', {}); v = m.get('evalWhite')
    if m.get('mate') is None and v is not None and abs(v) >= EVAL_MIN: analysis[key(e)] = 1 if v > 0 else -1
candidates = [key(e) for e in pools['candidates'] if (e.get('metrics', {}).get('decentMoves') or 0) >= DECENT_MIN]

JS = r"""async (min)=>{
  const out = {};
  for(const p of POOLS.imbalances){
    const e = aspectsEntry(p.fen);
    for(let i=0; i<200 && e.status!=='done'; i++) await new Promise(r=>setTimeout(r, 20));
    const d = e.data; if(!d) continue;
    const ls = ASPECTS.filter(x=>!d.off.includes(x.key)).map(x=>aspectLevel(d[x.key], x.key)).filter(l=>l);
    if(ls.length < min) continue;
    const w = ls.filter(l=>l>0).length, b = ls.length - w;
    out[p.game.slice(1) + ':' + p.ply] = [w > b ? 1 : w < b ? -1 : 0, w && b ? 1 : 0];   // the side most grades favour; both sides have some
  }
  return out;
}"""
async def imbalances():
    server = subprocess.Popen([sys.executable, '-m', 'http.server', '8798'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            await pg.goto('http://localhost:8798/index.html'); await pg.wait_for_timeout(1500)
            out = await pg.evaluate(JS, IMB_MIN)
            await b.close()
            return out
    finally:
        server.terminate()
imb = asyncio.run(imbalances())
starters = { 'imbalances': imb, 'analysis': analysis, 'candidates': candidates }
s = APP.read_text(encoding='utf-8')
s = re.sub(r'/\*STARTERS\*/.*?/\*END STARTERS\*/', lambda m: '/*STARTERS*/' + json.dumps(starters, separators=(',', ':')) + '/*END STARTERS*/', s, flags=re.S)
APP.write_text(s, encoding='utf-8')
print('imbalances', len(imb), '(both sides:', sum(1 for v in imb.values() if v[1]), ') | analysis', len(analysis), '(White', sum(1 for v in analysis.values() if v > 0), ') | candidates', len(candidates))
