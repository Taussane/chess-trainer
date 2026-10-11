# How "My games" fills up after an upload, and what happens while it does:
#  1. right after the upload (engine busy elsewhere): games Lichess analysed already have their
#     Board analysis and Candidate moves positions (Lichess's analysis is trusted), Final choice
#     waits for each mistake's top-5 search; games not analysed have no position yet (none appears
#     and later goes); Final choice can't be opened yet and says why;
#  2. the background checks the flagged mistakes before it quick-scans any other game;
#  3. when every position was played today, the review's Next waits, and comes back by itself
#     when a new position arrives.
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        # Engine work is held back until we release it, and every background call is logged.
        await pg.evaluate("""(()=>{ window.__log=[]; window.__hold=true; const real=bgEval;
          bgEval = (fen,o)=>new Promise(res=>{ const go=()=>{ __log.push(o && o.multipv===1 ? 'scan' : 'check'); real(fen,o).then(res); };
            const wait=()=>{ if(__hold) setTimeout(wait,20); else go(); }; wait(); }); })()""")
        await pg.click('#accountBtn'); await pg.fill('#lichessUser', 'TestPlayer')
        await pg.set_input_files('#pgnFile', T.SAMPLE); await pg.wait_for_timeout(300)
        st = await pg.evaluate("({games:myGames.length, analysed:myGames.filter(g=>g.evals).length, gamesWithBA:myGames.filter(g=>g.positions.some(p=>p.acts.includes('analysis'))).length, unanalysedWithPositions:myGames.filter(g=>!g.evals && g.positions.length).length, flagged:myGames.flatMap(g=>g.positions).filter(p=>p.pending).length, c:countsOf(myPositions)})")
        print('right after upload:', st)
        if not st['gamesWithBA'] or st['gamesWithBA'] > st['analysed'] or st['unanalysedWithPositions']: fails.append(f"positions should come only from analysed games: {st}")
        if not st['flagged']: fails.append('no likely mistakes flagged from Lichess evaluations')
        if not st['c']['candidates']: fails.append("Lichess's mistakes should be in Candidate moves at once")
        if st['c']['final']: fails.append('Final choice used before its search')
        await pg.click('#homeBtn'); await pg.click('[data-src="mine"]'); await pg.wait_for_timeout(100)
        cards = await pg.evaluate("[...document.querySelectorAll('.card')].map(c=>c.dataset.go+':'+(c.disabled?'off':'on')+':'+c.querySelector('.card-desc').innerText)")
        print('home:', cards)
        if not cards[0].startswith('imbalances:on') or not cards[1].startswith('analysis:on') or not cards[2].startswith('candidates:on'): fails.append(f'Board analysis and Candidate moves should open at once: {cards}')
        if ':off:Finding positions' not in cards[3]: fails.append(f'Move selection should wait: {cards}')
        await pg.screenshot(path=str(T.SHOTS/'fast_1_home_waiting.png'))
        # Release the engine: all checks must come before the first quick scan.
        await pg.evaluate("__hold=false")
        for _ in range(120):
            done = await pg.evaluate("!myWorkPending() && !myBgRunning")
            if done: break
            await pg.wait_for_timeout(250)
        log = await pg.evaluate("__log")
        first_scan = log.index('scan') if 'scan' in log else len(log)
        print('work order:', ''.join('C' if x=='check' else 's' for x in log)[:80], '…', len(log), 'searches')
        if 'scan' in log and log[:first_scan].count('check') < st['flagged']: fails.append('a game was scanned before the flagged mistakes were checked')
        c = await pg.evaluate("countsOf(myPositions)"); print('finally:', c)
        tried = await pg.evaluate("[...myTried].filter(k=>!k.startsWith('scan:')).length")
        checks = log.count('check')
        print('distinct mistakes checked:', tried, '| check searches:', checks)
        if checks > 2*tried: fails.append(f'a likely mistake was checked more than once ({checks} searches for {tried})')
        if not c['final']: fails.append('no Final choice positions after the searches')
        # Waiting at the review: everything but one Board analysis position already played today.
        await pg.evaluate("(()=>{ const t=ctx('analysis',false); ensureTrack(t); const pool=poolOf(t); const cur=posAt(t, firstAvailable(t, seqBy[t])); pool.forEach(p=>{ if(p.key!==cur.key) markPlayed(p.key); }); })()")
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
        await pg.click('#check'); await pg.wait_for_timeout(2500)
        n = await pg.evaluate("[document.getElementById('nextPos').disabled, document.getElementById('nextPos').innerText]")
        print('next after the last one:', n)
        if n != [True, 'All played today']: fails.append(f'Next should wait: {n}')
        await pg.screenshot(path=str(T.SHOTS/'fast_2_next_waiting.png'))
        # A new game arrives: Next comes back by itself.
        await pg.evaluate("""(()=>{ const g = JSON.parse(JSON.stringify(myGames[0])); g.id='newgame1'; g.checks={}; g.status='evaluated'; extractOwnPositions(g); myGames.push(g); onOwnPositionsChanged(); })()""")
        await pg.wait_for_timeout(300)
        n = await pg.evaluate("[document.getElementById('nextPos').disabled, document.getElementById('nextPos').innerText]")
        print('after a new game:', n)
        if n[0]: fails.append(f'Next did not come back: {n}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
