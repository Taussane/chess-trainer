# Log in with Google (for players without Lichess), against the real account server code and a
# stand-in Google that signs its ID tokens like Google:
#  1. Google login creates an account; Chess.com added; progress saved to it.
#  2. The same Google account on another device: same progress and Chess.com games.
#  3. Log out clears the browser; the account keeps everything. A Lichess login stays separate.
#  4. Linking: the Google account adds that Lichess login; the Lichess account (with its own progress)
#     is merged into it, and both logins open the same account. A Lichess account isn't offered Google.
import asyncio, sys, pathlib, subprocess, time, urllib.request
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
import accounts as A
ROOT = A.ROOT

async def google_login(pg):
    await pg.evaluate("screen='account'; render()")
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
            await P1.evaluate("screen='account'; render()")
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
            await P1.evaluate("screen='mygames'; render()")
            await P1.fill('#ccUser', 'ccplayer'); await P1.click('#ccConnect')
            await P1.wait_for_function("myGames.filter(g=>siteOf(g)==='chesscom').length===9", timeout=20000)
            await P1.wait_for_timeout(1200)
            await P1.evaluate("screen='account'; render()")
            acct = await P1.inner_text('.ac-logins'); print('   ', acct.replace('\n', ' '))
            if 'g-2001@example.com' not in acct: fails.append('logged-in line: ' + acct)
            await P1.evaluate("screen='mygames'; render()")
            if await P1.query_selector('#syncLine'): fails.append('a Lichess sync line shows without a Lichess login')
            await P1.screenshot(path=str(T.SHOTS/'google_2_logged_in.png'))
            # 2. Another device, same Google account.
            ctx2, P2, errs2 = await A.new_browser(p, SITE, who)
            await google_login(P2); await P2.wait_for_timeout(1500)
            n = await P2.evaluate("[results.length, chesscomName, myGames.filter(g=>siteOf(g)==='chesscom').length]"); print('2. other device:', n)
            if n != [1, 'CCPlayer', 9]: fails.append(f'second device: {n}')
            await P2.evaluate("screen='account'; render()")
            pf = await P2.inner_text('.ac-logins'); print('   profile:', pf.replace('\n', ' '))
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
            # 4. P2 (Lichess "Other") plays one; P1 (Google) adds that Lichess login: one account with both.
            # Two results on the Lichess account: one fine, one missed (for Replay), as the app saves them.
            await P2.evaluate("""(()=>{ const k = POOLS.analysis.map(p=>p.key), now = Date.now();
              [{ a:'analysis', acc:80, ts:now-2000, src:'masters', key:k[0], miss:false }, { a:'analysis', acc:5, ts:now-1000, src:'masters', key:k[1], miss:true }]
                .forEach(r=>{ results.push(r); resultsDb.add(r); }); })()"""); await P2.wait_for_timeout(1200)
            m = await P2.evaluate("missedList().length"); print("4. P2 missed before linking:", m, await P2.evaluate("results.map(r=>[r.a, r.acc, r.miss, (r.key||'').slice(0,20)])"))
            if m != 1: fails.append(f'test setup: P2 should have one missed position, has {m}')
            await P1.evaluate("screen='mygames'; render()")
            who[0] = 'tok-other'
            await P1.click('#mgLinkLichess'); await P1.wait_for_timeout(2500); await A.stand_in(P1); await P1.wait_for_timeout(2000)
            n = await P1.evaluate("[!!lichessAuth, !!googleAuth, results.length, (accountConnections||[]).map(c=>c.site).sort().join(','), myImportNote]"); print('4. P1 after adding Lichess:', n)
            if n[:4] != [True, True, 3, 'google,lichess']: fails.append(f'linking Lichess to the Google account: {n}')
            await P1.evaluate("screen='account'; render()")
            pf = await P1.inner_text('.ac-logins'); print('   profile:', pf.replace('\n', ' '))
            if 'Lichess' not in pf or 'Other' not in pf or 'g-2001@example.com' not in pf: fails.append('profile after linking: ' + pf)
            await P1.screenshot(path=str(T.SHOTS/'google_3_linked.png'))
            await P2.reload(); await P2.wait_for_timeout(600); await A.stand_in(P2); await P2.wait_for_timeout(1500)
            n = await P2.evaluate("[results.length, chesscomName]"); print('   P2 (Lichess) after reload:', n)
            if n != [3, 'CCPlayer']: fails.append(f'the Lichess login should now open the merged account: {n}')
            # 5. A new device logs in with Google only: the merged account in full, and its Lichess games
            #    (read without a Lichess login here); no "Connect your Lichess account".
            await P1.evaluate("screen='progress'; render()")
            ref = await P1.evaluate("({ results: results.map(r=>r.ts+r.a).sort().join(), missed: missedList().map(e=>e.a+e.key).sort().join(), week: [...document.querySelectorAll('.wk-table tbody tr')].map(r=>r.innerText).join('|') })")
            who[0] = 'g-2001'
            ctx4, P4, errs4 = await A.new_browser(p, SITE, who)
            # While the account loads (slow server here), My games says so: never the Chess.com box
            # this account doesn't need, nor the "Connect your Lichess account" button.
            A.API_DELAY[0] = 0.4
            await P4.evaluate("screen='account'; render()"); await P4.click('#googleLogin')
            seen = set()
            for _ in range(80):
                await P4.wait_for_timeout(100)
                try: await P4.evaluate("if(typeof screen!=='undefined' && screen!=='mygames' && typeof googleAuth!=='undefined' && googleAuth){ screen='mygames'; render(); }")
                except Exception: pass
                try: f = await P4.evaluate("[!!document.getElementById('ccUser'), !!document.getElementById('mgLinkLichess'), !!document.querySelector('.mg-loading'), typeof myGamesLoaded!=='undefined' && myGamesLoaded]")
                except Exception: continue
                seen.add(tuple(f))
                if f[3]: break
            A.API_DELAY[0] = 0
            print('   while loading:', sorted(seen))
            if any(f[0] or f[1] for f in seen): fails.append(f'My games showed the Chess.com box or the Lichess button before the account was read: {sorted(seen)}')
            if not any(f[2] for f in seen): fails.append('no "Retrieving your account" while loading')
            await A.stand_in(P4); await P4.wait_for_timeout(2500)
            await P4.evaluate("screen='progress'; render()")
            got = await P4.evaluate("({ results: results.map(r=>r.ts+r.a).sort().join(), missed: missedList().map(e=>e.a+e.key).sort().join(), week: [...document.querySelectorAll('.wk-table tbody tr')].map(r=>r.innerText).join('|') })")
            for k in ref:
                if got[k] != ref[k]: fails.append(f'merged account on a new device, {k}: {got[k]} vs {ref[k]}')
            n = await P4.evaluate("[!!lichessAuth, lichessName(), myGames.filter(g=>siteOf(g)==='lichess').length, myGames.filter(g=>siteOf(g)==='chesscom').length, results.filter(r=>r.key).every(r=>isPlayed(r.key))]")
            print('5. new device, Google only:', n, '| results', len(got['results'].split(',')), '| missed', len([x for x in got['missed'].split(',') if x]))
            if not got['missed']: fails.append('the missed position (Replay) did not come with the merge')
            if n[0] or n[1] != 'Other' or n[2] < 5 or n[3] != 9 or not n[4]: fails.append(f'new device: {n}')
            await P4.evaluate("screen='mygames'; render()")
            if await P4.query_selector('#mgLinkLichess'): fails.append('My games still offers to connect Lichess')
            line = await P4.inner_text('.mg-card'); print('   ', line.replace('\n', ' ')[:160])
            await P4.screenshot(path=str(T.SHOTS/'google_4_linked_mygames.png'))
            errs3 = errs4
            # A Lichess account isn't offered a Google login (Lichess is the main login).
            ctx3, P3, errs5 = await A.new_browser(p, SITE, who); errs3 += errs5
            who[0] = 'tok-taussane'; await A.login(P3)
            await P3.evaluate("screen='account'; render()"); await P3.wait_for_timeout(300)
            if await P3.query_selector('#googleLogin') or await P3.query_selector('#mgLinkLichess'): fails.append('a Lichess account should not be offered another login')
            for e in errs1 + errs2 + errs3:
                if 'importScripts' not in e: fails.append('page error: ' + e)
            await p['b'].close()
    finally:
        server.terminate()
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
