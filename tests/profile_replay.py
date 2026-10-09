# Profile page (joined date, positions completed, this week, replay button, progress) and the
# replay loop: a position played below your average joins the list; replaying it at or above
# your average takes it off; replays count like any position; a position played today isn't
# offered again until tomorrow.
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        await pg.evaluate("fenEvalStore = {}; poolEvalStore = {}")   # forget searches the blocked real engine failed before the stand-in took over
        # A history: 8 Board analysis positions at 80%, two days ago and today.
        await pg.evaluate("""(()=>{ const now=Date.now(); results = Array.from({length:8},(_,i)=>({a:'analysis', acc:80, ts: now - (i<4 ? 2*864e5 : 0) - (8-i)*6e4, src:'masters'})); saveLocal(); progressReady(); render(); })()""")
        # Play a Board analysis position badly (guess far from the engine's value) -> joins the list.
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
        k = await pg.evaluate("pos().key"); await pg.wait_for_function("!!fenEval(pos().fen)")
        await pg.evaluate("(()=>{ const s=st('analysis'); const d=fenEval(pos().fen); s.guess = d && positionInfo(pos(), d).pct > 50 ? 2 : 98; render(); })()")
        await pg.click('#check'); await pg.wait_for_timeout(2500)
        lst = await pg.evaluate("missedList().map(x=>x.a+':'+x.key)")
        print('after a bad play:', lst)
        if f'analysis:{k}' not in lst: fails.append('a position below the average did not join the replay list')
        await pg.click('#homeBtn'); await pg.click('#accountBtn')
        txt = await pg.inner_text('.pf-id'); print(txt.replace('\n', ' '))
        if 'Training since' not in txt or '9 positions completed' not in txt: fails.append('profile header wrong')
        await pg.click('#progressBtn'); await pg.wait_for_timeout(200)
        txt = await pg.inner_text('.pf-scroll')
        if 'All played today' not in txt: fails.append('a position played today was offered for replay')
        rows = await pg.evaluate("[...document.querySelectorAll('.wk-table tbody tr')].map(r=>r.innerText.replace(/\\s+/g,' '))")
        print('week:', rows[:3])
        if not rows[0].startswith('Today 5') : fails.append(f'today row: {rows[0]}')
        await pg.screenshot(path=str(T.SHOTS/'profile.png'), full_page=True)
        # Next day: the position is offered again. Replay it well -> off the list, and it counts.
        await pg.evaluate("played = { day: todayKey(), keys: [] }; render()")
        txt = await pg.inner_text('.pf-scroll')
        if 'Replay 1' not in txt: fails.append('replay button missing the next day')
        n_before = await pg.evaluate("results.length")
        await pg.click('#replayBtn'); await pg.wait_for_timeout(300)
        title = await pg.inner_text('h1')
        if not title.startswith('Replay'): fails.append(f'replay title: {title}')
        if await pg.evaluate("pos().key") != k: fails.append('replay opened another position')
        await pg.evaluate("(()=>{ const s=st('analysis'); const d=fenEval(pos().fen); s.guess = positionInfo(pos(), d).pct; render(); })()")
        await pg.click('#check'); await pg.wait_for_timeout(2500)
        chip = await pg.inner_text('.layer:not(.ghost) .score')
        print('replay review:', chip.replace('\n',' '))
        if 'Average' not in chip: fails.append('replay review should show the average')
        if await pg.evaluate("missedList().length"): fails.append('position still on the list after a good replay')
        if await pg.evaluate("results.length") != n_before + 1: fails.append('a replay was not recorded in the results')
        nxt = await pg.inner_text('#nextPos')
        if nxt != "Finish": fails.append(f'next label: {nxt}')
        await pg.click('#nextPos'); await pg.wait_for_timeout(200)
        if await pg.evaluate("screen") != 'progress': fails.append('finishing the replay should return to the profile')
        await pg.click('#homeBtn'); txt = await pg.inner_text('.pf-id')
        if '10 positions completed' not in txt: fails.append('the replay is not in the positions completed')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
