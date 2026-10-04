# Positions played today are skipped by every exercise (and remembered across a reload).
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        # Play the next Candidate moves position.
        await pg.click('.card[data-go="candidates"]'); await pg.wait_for_timeout(300)
        k = await pg.evaluate("pos().key")
        await pg.evaluate("(()=>{ const ch=new Chess(pos().fen); const m=ch.moves({verbose:true})[0]; st('candidates').picks=[{id:'c',san:m.san,from:m.from,to:m.to,uci:m.from+m.to+(m.promotion||''),slot:0}]; render(); })()")
        await pg.click('#check'); await pg.wait_for_timeout(3000)
        if await pg.evaluate("pos().key") != k: fails.append('the reviewed position changed under the review')
        await pg.click('#homeBtn')
        # Put that same position next in Final choice: it must be skipped.
        await pg.evaluate(f"(()=>{{ const t=ctx('final'); ensureTrack(t); const p=orders['candidates'][seqBy['candidates']]; orders[t].splice(seqBy[t], 0, p); }})()")
        await pg.click('.card[data-go="final"]'); await pg.wait_for_timeout(300)
        k2 = await pg.evaluate("pos().key")
        if k2 == k: fails.append('Final choice showed a position already played today')
        saved = await pg.evaluate("localStorage.getItem('cst.played.v1')")
        print('played:', saved[:80], '| final opened on another position:', k2 != k)
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
