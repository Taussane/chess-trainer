# The website (index.html at the top of the repository, built by scripts/build-site.py):
# up to date with the app, a proper phone page, and "My games" downloading games straight from
# Lichess (a stand-in Lichess answers here: the sample games for TestPlayer, "not found" otherwise). Only a logged-in player can download games: their own.
import asyncio, sys, pathlib, subprocess
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
ROOT = pathlib.Path(__file__).resolve().parent.parent
async def main():
    fails = []
    if subprocess.run([sys.executable, str(ROOT/'scripts'/'build-site.py'), '--check']).returncode: fails.append('index.html out of date')
    SITE = (ROOT/'index.html').read_text()
    asked = []
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width':390,'height':760}, is_mobile=True, has_touch=True)
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        async def route(r):
            u = r.request.url
            if 'chess.js' in u: await r.fulfill(body=T.CHESS, content_type='application/javascript')
            elif u.startswith('https://site.test/'): await r.fulfill(body=SITE, content_type='text/html')
            elif u.startswith('https://lichess.org/api/games/user/'):
                asked.append((u, r.request.headers.get('accept')))
                if '/TestPlayer?' in u: await r.fulfill(body=pathlib.Path(T.SAMPLE).read_text(), content_type='application/x-chess-pgn', headers={'access-control-allow-origin':'*'})
                else: await r.fulfill(status=404, body='', headers={'access-control-allow-origin':'*'})
            else: await r.abort()
        await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
        await pg.goto('https://site.test/'); await pg.wait_for_timeout(400)
        st = await pg.evaluate("[document.compatMode, !!document.querySelector('meta[name=viewport]'), document.title, typeof window.claude, document.documentElement.scrollWidth <= innerWidth]")
        print('page:', st)
        if st != ['CSS1Compat', True, 'Chess Strategy Trainer', 'undefined', True]: fails.append(f'page setup: {st}')
        await pg.evaluate("(()=>{"+T.FAKE+" render(); })()")
        await pg.click('#myGamesBtn')
        if await pg.query_selector('#exportLink'): fails.append('the website still shows the download steps')
        # Logged out: only the Lichess login, no way to download someone's games by name.
        found = await pg.evaluate("['#lichessUser','#fetchGames','#bulletBox'].filter(s=>document.querySelector(s))")
        if found or not await pg.query_selector('#lichessLogin'): fails.append(f'logged out, the card still offers: {found}')
        # Logged in (as after Lichess's sign-in): your own games, downloaded with your login.
        await pg.evaluate("setLichessAuth({ token:'tok', username:'TestPlayer' }); render()")
        # No button: games come in by themselves (here: called as on a visit).
        if await pg.query_selector('#fetchGames'): fails.append('a manual download button is still shown')
        await pg.evaluate("syncLichessGames()"); await pg.wait_for_timeout(700)
        line = await pg.inner_text('#syncLine'); print('first visit:', line)
        if '10 new games added' not in line: fails.append('first sync: ' + line)
        u, acc = asked[-1]; print('asked:', u, '|', acc)
        if 'max=100' not in u or 'evals=true' not in u or 'bullet' not in u or 'since=' in u or 'pgn' not in (acc or ''): fails.append('first request to Lichess: ' + u)
        # Next visit: only games played since the newest one here.
        await pg.evaluate("syncLichessGames()"); await pg.wait_for_timeout(700)
        u = asked[-1][0]; newest = await pg.evaluate("myGames.reduce((m,g)=>Math.max(m,g.playedAt||0),0)")
        line = await pg.inner_text('#syncLine'); print('next visit:', line, '| since', u.split('since=')[-1])
        if f'since={newest+1000}' not in u: fails.append('next request does not ask only for newer games: ' + u)
        if line != 'Up to date with Lichess.': fails.append('second sync line: ' + line)
        await pg.screenshot(path=str(T.SHOTS/'site_mygames.png'))
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
