# The owner's games saved by an earlier version (no full-strength marker) load complete: nothing to re-check.
import asyncio, sys, json, re
sys.path.insert(0,'/home/claude/chess-trainer/tests')
import my_games as T, owner_seed as O
seed = re.search(r'/\*OWNER_SEED\*/(.*?)/\*END OWNER_SEED\*/', T.SRC, re.S).group(1)
games = json.loads(seed)
for g in games: g.pop('verified', None)
store = "localStorage.setItem('cst.mygames.v1', " + json.dumps(json.dumps(games)) + "); localStorage.setItem('cst.seed.v2','1'); localStorage.setItem('cst.source','mine');"
async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b, pg, errs = await O.run(p, owner=True, storage=store)
        await pg.evaluate("myBgRunning=true")   # look before any background work
        print('at load:', await pg.evaluate("({c:countsOf(myPositions), pending:myGames.flatMap(g=>g.positions).filter(p=>p.pending).length, queued:myGames.filter(g=>g.status==='queued').length, verified:myGames.filter(g=>g.verified).length})"))
        print([e for e in errs if 'importScripts' not in e]); await b.close()
asyncio.run(main())
