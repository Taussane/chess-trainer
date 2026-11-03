# The Plan finder's onboarding positions (a new player's first 10 come from these): master positions of its pool
# that are clear-cut: nothing urgent (quiet), Stockfish away from the balanced line's edge (within ±0.25, or 1.0
# or more), and both plan rows decided (Trades and Dynamic or positional, not Either). Written into app/index.html
# (PLANQ_STARTERS). Usage: python3 scripts/planq-starters.py, then python3 scripts/build-site.py
import asyncio, sys, json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
import my_games as T
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        await pg.route('**/master-evals.json', lambda r: asyncio.ensure_future(r.fulfill(body=(ROOT / 'master-evals.json').read_text(), content_type='application/json')))
        await pg.evaluate("masterEvals=null; loadMasterEvals();"); await pg.wait_for_timeout(3000)
        keys = await pg.evaluate("""(()=>{ const out = []; for(const p of POOLS.planq){ const info = planqInfo(p), vals = explorerVals(p.fen, true); if(!info || !vals || vals.special) continue;
          const c = planqMake(p, info, vals, new Set()); if(c.urgent.ambiguous || c.urgent.kind || !planqFits(p, c)) continue;
          const cp = info.mate!=null ? 1e4 : Math.abs(info.cp);
          if((cp <= 25 || cp >= 100) && c.rows.every(r=>r.answer)) out.push(p.key); } return out.sort(); })()""")
        await b.close()
    app = ROOT / 'app' / 'index.html'
    s = app.read_text()
    s = re.sub(r'/\*PLANQ_STARTERS\*/.*?/\*END PLANQ_STARTERS\*/', lambda m: '/*PLANQ_STARTERS*/' + json.dumps(keys) + '/*END PLANQ_STARTERS*/', s, flags=re.S)
    app.write_text(s)
    print('Plan finder starters:', len(keys))
asyncio.run(main())
