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
        await pg.wait_for_timeout(1500)
        st = await pg.evaluate("({c:countsOf(myPositions), pending:myGames.flatMap(g=>g.positions).filter(p=>p.pending).length, queued:myGames.filter(g=>g.status==='queued').length, verified:myGames.filter(g=>g.verified).length, running:myBgRunning, tried:myTried.size})")
        print('after load:', st)
        fails = []
        if st['c'] != {'analysis':126, 'candidates':131, 'final':127} or st['pending'] or st['tried'] or st['running']: fails.append(f'owner games not complete at once: {st}')
        errs = [e for e in errs if 'importScripts' not in e]
        if errs: fails.append(f'page errors: {errs}')
        await b.close()
        print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
