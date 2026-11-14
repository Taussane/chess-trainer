# How "My games" fills up after an upload, and what happens while it does:
#  1. right after the upload (engine busy elsewhere): only the game being worked on has positions, each
#     as it's validated; the others wait for their turn, game by game;
#  2. the background goes game by game, Lichess's analysed games first, one search per position (the pass): a game's
#     likely mistakes first, no position searched twice;
#  3. when every position was played today, the review's Next waits, and comes back by itself
#     when a new position arrives.
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
# The questions' Check waits for a first move of the answer (the bar touched, a swap, a grade): tests that
# answer straight away open it as a player would have.
UNGATE = "(()=>{ const s = st(screen); s.barMoved = true; s.swapped = true; const c = document.getElementById('check'); if(c && sfState!=='error' && (screen!=='candidates' || s.picks.length)) c.disabled = false; })()"
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        # Engine work is held back until we release it, and every background call is logged.
        await pg.evaluate("""(()=>{ window.__log=[]; window.__hold=true; const real=bgEval;
          bgEval = (fen,o)=>new Promise(res=>{ const go=()=>{ __log.push([o && (o.movetime===400 || o.movetime===500) ? 'plan' : 'check', fen]); real(fen,o).then(res); };
            const wait=()=>{ if(__hold) setTimeout(wait,20); else go(); }; wait(); }); })()""")
        await pg.click('#accountBtn'); await pg.evaluate("(t=>{ importPgnText(t, false, 'TestPlayer'); render(); })", pathlib.Path(T.SAMPLE).read_text()); await pg.wait_for_timeout(300)
        st = await pg.evaluate("({games:myGames.length, analysed:myGames.filter(g=>g.evals).length, gamesWithBA:myGames.filter(g=>g.positions.some(p=>p.acts.includes('imbalances') || p.acts.includes('planq'))).length, unanalysedWithPositions:myGames.filter(g=>!g.evals && g.positions.length).length, flagged:myGames.flatMap(g=>g.positions).filter(p=>p.pending).length, c:countsOf(myPositions)})")
        print('right after upload:', st)
        if not st['gamesWithBA'] or st['gamesWithBA'] > st['analysed'] or st['unanalysedWithPositions']: fails.append(f"positions should come only from analysed games: {st}")
        if not st['flagged']: fails.append('no likely mistakes flagged from Lichess evaluations')
        early = await pg.evaluate("[...new Set(myPositions.map(p=>p.gameId))].filter(id=>!myReached.has(id)).length")
        if early: fails.append(f"positions from {early} games not reached yet: games are done one at a time")
        pending_by_game = await pg.evaluate("Object.fromEntries(myGames.map(g=>[g.id, (g.positions||[]).filter(p=>p.pending).map(p=>p.fen)]))")
        fens_by_game = await pg.evaluate("Object.fromEntries(myGames.map(g=>{ const c = new Chess(), f = [c.fen()]; g.sans.forEach(s=>{ c.move(s); f.push(c.fen()); }); return [g.id, f]; }))")
        # Release the engine: the pass begins with the likely mistakes.
        await pg.evaluate("__hold=false")
        # the first finished game: its positions in, the exercises open
        for _ in range(80):
            if await pg.evaluate("myDone.size > 0 && myPositions.length > 0"): break
            await pg.wait_for_timeout(100)
        await pg.click('#homeBtn'); await pg.click('[data-src="mine"]'); await pg.wait_for_timeout(100)
        cards = await pg.evaluate("[...document.querySelectorAll('.card')].map(c=>c.dataset.go+':'+(c.disabled?'off':'on')+':'+c.querySelector('.card-desc').innerText)")
        print('home after the first game:', cards, await pg.evaluate("countsOf(myPositions)"))
        await pg.screenshot(path=str(T.SHOTS/'fast_1_home_waiting.png'))
        for _ in range(120):
            done = await pg.evaluate("!myWorkPending() && !myBgRunning")
            if done: break
            await pg.wait_for_timeout(250)
        log = await pg.evaluate("__log")
        print('work order:', ''.join('C' if x[0]=='check' else 'p' for x in log)[:80], '…', len(log), 'searches')
        # each game's pass begins with its likely mistakes (Lichess's), when it has some
        for gid, pend in pending_by_game.items():
            mine = [x[1] for x in log if x[0]=='check' and x[1] in fens_by_game[gid]]
            if pend and mine and mine[0] not in pend: fails.append(f'game {gid}: its pass did not start with a likely mistake')
        c = await pg.evaluate("countsOf(myPositions)"); print('finally:', c)
        fens = [x[1] for x in log if x[0]=='check']
        print('pass searches:', len(fens), '| distinct positions:', len(set(fens)))
        # (the same position can come up in two games: searched once per game)
        occ = await pg.evaluate("(()=>{ const n = {}; myGames.forEach(g=>{ const c = new Chess(), f = [c.fen()]; g.sans.forEach(s=>{ c.move(s); f.push(c.fen()); }); new Set(f).forEach(x=>n[x] = (n[x] || 0) + 1); }); return n; })()")
        over = [f for f in set(fens) if fens.count(f) > occ.get(f, 1)]
        if over: fails.append(f'a position was searched more than once in a game: {over[:2]}')
        if not c['final']: fails.append('no Final choice positions after the searches')
        # Waiting at the review: everything but one Imbalance reading position already played today.
        await pg.evaluate("(()=>{ const t=ctx('imbalances',false); ensureTrack(t); const pool=poolOf(t); const cur=posAt(t, firstAvailable(t, seqBy[t])); pool.forEach(p=>{ if(p.key!==cur.key) markPlayed(p.key); }); })()")
        await pg.evaluate("openActivity('imbalances')"); await pg.wait_for_timeout(300)
        await pg.evaluate("(()=>{ const s=st('imbalances'); s.asp={material:1,pawns:-1,space:1}; s.aspTouched=true; render(); })()")
        await pg.evaluate(UNGATE); await pg.click('#check')
        await pg.wait_for_function("(document.getElementById('nextPos')||{}).innerText", timeout=15000); await pg.wait_for_timeout(500)
        n = await pg.evaluate("[document.getElementById('nextPos').disabled, document.getElementById('nextPos').innerText]")
        print('next after the last one:', n)
        if n != [True, 'All played today']: fails.append(f'Next should wait: {n}')
        await pg.screenshot(path=str(T.SHOTS/'fast_2_next_waiting.png'))
        # A new game arrives: Next comes back by itself.
        await pg.evaluate("""(()=>{ const g = JSON.parse(JSON.stringify(myGames[0])); g.id='newgame1'; g.checks={}; g.status='evaluated'; extractOwnPositions(g); myGames.push(g); onOwnPositionsChanged(); myBackground(); })()""")
        for _ in range(100):   # (its turn: its checks, then its positions)
            if not await pg.evaluate("document.getElementById('nextPos').disabled"): break
            await pg.wait_for_timeout(100)
        n = await pg.evaluate("[document.getElementById('nextPos').disabled, document.getElementById('nextPos').innerText]")
        print('after a new game:', n)
        if n[0]: fails.append(f'Next did not come back: {n}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
