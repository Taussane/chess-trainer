# Log in with Google (for players without Lichess), against the real account server code and a
# stand-in Google that signs its ID tokens like Google:
#  1. Google login creates an account; Chess.com added; progress saved to it.
#  2. The same Google account on another device: same progress and Chess.com games.
#  3. Log out clears the browser; the account keeps everything. A Lichess login stays separate.
import asyncio, sys, pathlib, subprocess, time, urllib.request
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
import accounts as A
ROOT = A.ROOT

async def google_login(pg):
    await pg.evaluate("screen='mygames'; render()")
    await pg.click('#googleLogin'); await pg.wait_for_timeout(2500)
    await A.stand_in(pg); await pg.wait_for_timeout(1500)

async def main():
    fails = []
    SITE = (ROOT/'index.html').read_text().replace('156223514087-0v17r4o6c77ru9hq3kafmpan91l2lunh.apps.googleusercontent.com', 'test-client.apps.googleusercontent.com')
    server = subprocess.Popen(['node', str(ROOT/'worker'/'test'/'local.mjs'), str(A.PORT)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try: urllib.request.urlopen(A.API + '/api/health'); break
            except Exception: time.sleep(0.1)
        async with async_playwright() as pw:
            p = {'b': await pw.chromium.launch()}
            who = ['g-2001']
            ctx1, P1, errs1 = await A.new_browser(p, SITE, who)
            await P1.evaluate("screen='mygames'; render()")
            btns = await P1.evaluate("[!!document.getElementById('lichessLogin'), !!document.getElementById('googleLogin')]")
            if btns != [True, True]: fails.append(f'both login buttons should show: {btns}')
            await P1.screenshot(path=str(T.SHOTS/'google_1_logged_out.png'))
            await A.play_one(P1)
            await google_login(P1)
            st = await P1.evaluate("[googleAuth && googleAuth.email, !!localStorage.getItem('cst.googleAuth'), location.hash, results.length, localStorage.getItem('cst.owner')!=null]")
            print('1. after Google login:', st)
            if st[0] != 'g-2001@example.com' or not st[1] or st[2] or st[3] != 1 or not st[4]: fails.append(f'Google login: {st}')
            tok = await P1.evaluate("googleAuth.token")
            req = lambda path: __import__('json').loads(urllib.request.urlopen(urllib.request.Request(A.API + path, headers={'Authorization': 'Bearer ' + tok, 'X-Auth-Site': 'app'})).read())
            me = req('/api/me'); print('   account:', me['connections'])
            if me['connections'] != [{'site': 'google', 'username': 'g-2001@example.com', 'verified': True}]: fails.append(f"connections: {me['connections']}")
            if len(req('/api/results?after=-1')['rows']) != 1: fails.append('the position played before logging in did not join the Google account')
            await P1.fill('#ccUser', 'ccplayer'); await P1.click('#ccConnect')
            await P1.wait_for_function("myGames.filter(g=>siteOf(g)==='chesscom').length===9", timeout=20000)
            await P1.wait_for_timeout(1200)
            acct = await P1.inner_text('.mg-account'); print('   ', acct.replace('\n', ' '))
            if 'g-2001@example.com' not in acct: fails.append('logged-in line: ' + acct)
            if await P1.query_selector('#syncLine'): fails.append('a Lichess sync line shows without a Lichess login')
            await P1.screenshot(path=str(T.SHOTS/'google_2_logged_in.png'))
            # 2. Another device, same Google account.
            ctx2, P2, errs2 = await A.new_browser(p, SITE, who)
            await google_login(P2); await P2.wait_for_timeout(1500)
            n = await P2.evaluate("[results.length, chesscomName, myGames.filter(g=>siteOf(g)==='chesscom').length]"); print('2. other device:', n)
            if n != [1, 'CCPlayer', 9]: fails.append(f'second device: {n}')
            await P2.evaluate("screen='progress'; render()")
            pf = await P2.inner_text('.pf-lichess'); print('   profile:', pf.replace('\n', ' '))
            if 'Google' not in pf: fails.append('profile: ' + pf)
            # 3. Log out on device 2: cleared there, the account keeps everything, device 1 still logged in.
            await P2.click('#pfLogout'); await P2.wait_for_timeout(1500)
            n = await P2.evaluate("[results.length, myGames.length, googleAuth, localStorage.getItem('cst.owner')]"); print('3. device 2 after logout:', n)
            if n != [0, 0, None, None]: fails.append(f'not cleared after logout: {n}')
            if len(req('/api/results?after=-1')['rows']) != 1: fails.append('device 1 lost its login, or the account its results')
            # A Lichess login is a different account.
            who[0] = 'tok-other'
            await A.login(P2)
            n = await P2.evaluate("[!!lichessAuth, results.length, chesscomName]"); print('   Lichess login on device 2:', n)
            if n != [True, 0, '']: fails.append(f'Lichess account mixed with the Google one: {n}')
            for e in errs1 + errs2:
                if 'importScripts' not in e: fails.append('page error: ' + e)
            await p['b'].close()
    finally:
        server.terminate()
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
