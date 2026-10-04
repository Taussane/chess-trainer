# How "My games" fills up after an upload, and what happens while it does:
#  1. right after the upload (engine busy elsewhere): every game already has its Board analysis
#     positions; Lichess-analysed games have their likely mistakes flagged; Candidate moves and
#     Final choice can't be opened yet and say why;
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
        await pg.click('#myGamesBtn'); await pg.fill('#lichessUser', 'TestPlayer')
        await pg.set_input_files('#pgnFile', T.SAMPLE); await pg.wait_for_timeout(300)
        st = await pg.evaluate("({games:myGames.length, gamesWithBA:myGames.filter(g=>g.positions.some(p=>p.acts.includes('analysis'))).length, flagged:myGames.flatMap(g=>g.positions).filter(p=>p.pending).length, c:countsOf(myPositions)})")
        print('right after upload:', st)
        if st['gamesWithBA'] < 7: fails.append(f"Board analysis not ready at once: {st}")
        if not st['flagged']: fails.append('no likely mistakes flagged from Lichess evaluations')
        if st['c']['candidates']: fails.append('mistakes used before being checked')
        await pg.click('#homeBtn'); await pg.click('[data-src="mine"]'); await pg.wait_for_timeout(100)
        cards = await pg.evaluate("[...document.querySelectorAll('.card')].map(c=>c.dataset.go+':'+(c.disabled?'off':'on')+':'+c.querySelector('.card-desc').innerText)")
        print('home:', cards)
        if not cards[0].startswith('analysis:on'): fails.append('Board analysis should open at once')
        if not all(':off:Waiting for new positions' in c for c in cards[1:]): fails.append(f'Candidate moves / Final choice should wait: {cards}')
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
        if not c['candidates']: fails.append('no mistakes after the checks')
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
