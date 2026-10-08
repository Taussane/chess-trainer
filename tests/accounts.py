# Accounts end to end: the website against the real account server code (worker/, run here on
# Node's built-in SQLite, see worker/test/local.mjs) and a stand-in Lichess.
#  1. Play without logging in, then log in: what was played here joins the new account; your games
#     download and are saved to it.
#  2. Another device logs in: same progress and games.
#  3. What it plays reaches the account; logging out clears that browser (it's safe in the account).
#  4. Another person logging in on a browser holding someone else's copy never gets it.
#  5. Delete my account removes everything on the server.
import asyncio, sys, pathlib, json, subprocess, time, urllib.request, urllib.error
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = 8791
API = f'http://127.0.0.1:{PORT}'
PLAYERS = {'tok-taussane': {'id':'taussane','username':'Taussane'}, 'tok-other': {'id':'other','username':'Other'}}
CORS = {'access-control-allow-origin':'*', 'access-control-allow-headers':'authorization, content-type, accept', 'access-control-allow-methods':'GET, POST, DELETE, OPTIONS'}

def api(method, path, token='tok-taussane'):
    req = urllib.request.Request(API + path, method=method, headers={'Authorization':'Bearer ' + token})
    with urllib.request.urlopen(req) as r: return json.loads(r.read())

async def new_browser(p, SITE, login_as):
    """A browser (own storage) on the website; Lichess approves sign-ins as login_as[0]."""
    ctx = await p['b'].new_context(viewport={'width':390,'height':760})
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.add_init_script(f"localStorage.setItem('cst.api', 'https://api.test');")
    async def route(r):
        u, m = r.request.url, r.request.method
        if 'chess.js' in u: return await r.fulfill(body=T.CHESS, content_type='application/javascript')
        if u.startswith('https://site.test/'): return await r.fulfill(body=SITE, content_type='text/html')
        if u.startswith('https://api.test/'):   # to the account server, as the browser sent it
            req = urllib.request.Request(API + u[len('https://api.test'):], method=m, data=r.request.post_data_buffer,
                                         headers={k: v for k, v in r.request.headers.items() if k.lower() in ('authorization','content-type','origin','x-auth-site','access-control-request-method','access-control-request-headers')})
            try:
                with urllib.request.urlopen(req) as resp: status, body, hdrs = resp.status, resp.read(), dict(resp.headers)
            except urllib.error.HTTPError as e: status, body, hdrs = e.code, e.read(), dict(e.headers)
            return await r.fulfill(status=status, body=body, headers=hdrs)
        if m == 'OPTIONS': return await r.fulfill(status=204, headers=CORS)
        if u.startswith('https://lichess.org/oauth?'):
            from urllib.parse import urlparse, parse_qsl
            q = dict(parse_qsl(urlparse(u).query))
            return await r.fulfill(body=f'<script>location.replace({json.dumps(q["redirect_uri"] + "?code=" + login_as[0] + "&state=" + q["state"])})</script>', content_type='text/html')
        if u == 'https://lichess.org/api/token' and m == 'POST':
            from urllib.parse import parse_qsl
            code = dict(parse_qsl(r.request.post_data or ''))['code']
            return await r.fulfill(body=json.dumps({'access_token': code, 'token_type':'Bearer'}), content_type='application/json', headers=CORS)
        if u == 'https://lichess.org/api/token': return await r.fulfill(status=204, headers=CORS)
        if u == 'https://lichess.org/api/account':
            tok = (r.request.headers.get('authorization') or '').replace('Bearer ', '')
            return await r.fulfill(body=json.dumps(PLAYERS.get(tok, {'error':'no'})), status=200 if tok in PLAYERS else 401, content_type='application/json', headers=CORS)
        if u.startswith('https://lichess.org/api/games/user/'):
            return await r.fulfill(body=pathlib.Path(T.SAMPLE).read_text().replace('TestPlayer', 'Taussane'), content_type='application/x-chess-pgn', headers=CORS)
        await r.abort()
    await ctx.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
    await pg.goto('https://site.test/'); await pg.wait_for_timeout(400)
    await stand_in(pg)
    return ctx, pg, errs

async def stand_in(pg):
    await pg.evaluate("(()=>{" + T.FAKE + " fenEvalStore = {}; poolEvalStore = {}; render(); })()")

async def play_one(pg):
    await pg.evaluate("screen='home'; render()")
    await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
    await pg.evaluate("(()=>{ st('analysis').guess = 60; render(); })()")
    await pg.click('#check'); await pg.wait_for_timeout(2500)

async def login(pg):
    await pg.evaluate("screen='mygames'; render()")
    await pg.click('#lichessLogin'); await pg.wait_for_timeout(2500)
    await stand_in(pg); await pg.wait_for_timeout(1500)

async def main():
    fails = []
    SITE = (ROOT/'index.html').read_text()
    server = subprocess.Popen(['node', str(ROOT/'worker'/'test'/'local.mjs'), str(PORT)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try: urllib.request.urlopen(API + '/api/health'); break
            except Exception: time.sleep(0.1)
        async with async_playwright() as pw:
            p = {'b': await pw.chromium.launch()}
            who = ['tok-taussane']
            # 1. Device A: two positions before logging in, then log in.
            ctxA, A, errsA = await new_browser(p, SITE, who)
            await play_one(A); await play_one(A)
            await login(A)
            await A.wait_for_timeout(1500)
            srv = api('GET', '/api/results?after=-1&limit=1000')['rows']; games = api('GET', '/api/games')['games']
            print('1. account after first login: results', len(srv), '| games', len(games))
            if len(srv) != 2: fails.append(f'results played before logging in did not join the account: {len(srv)}')
            if len(games) < 5: fails.append(f'games not saved to the account: {len(games)}')
            if any('positions' in g for g in games): fails.append('games saved with their positions')
            # 2. Device B logs in: same progress and games.
            ctxB, B, errsB = await new_browser(p, SITE, who)
            await login(B); await B.wait_for_timeout(1000)
            n = await B.evaluate("[results.length, myGames.length, localStorage.getItem('cst.owner')!=null]"); print('2. device B:', n)
            if n[0] != 2 or n[1] != len(games) or not n[2]: fails.append(f'device B: {n}')
            await B.evaluate("screen='progress'; render()"); await B.screenshot(path=str(T.SHOTS/'accounts_profile.png'))
            # 2b. Chess.com: A adds a username; its live games come in (cc- ids), B sees them after a reload.
            await A.evaluate("screen='mygames'; render()")
            await A.fill('#ccUser', 'nobody'); await A.click('#ccConnect'); await A.wait_for_timeout(600)
            note = await A.inner_text('.mg-note'); print('2b. unknown Chess.com player:', note)
            if 'No Chess.com player named nobody' not in note: fails.append('unknown Chess.com player: ' + note)
            await A.fill('#ccUser', 'ccplayer'); await A.click('#ccConnect'); await A.wait_for_timeout(2500)
            await A.wait_for_function("myPositions.some(p=>p.gameId && p.gameId.startsWith('cc-'))", timeout=20000)   # once a Chess.com game is scanned
            cc = await A.evaluate("[chesscomName, myGames.filter(g=>siteOf(g)==='chesscom').map(g=>g.id), (myPositions.find(p=>p.gameId && p.gameId.startsWith('cc-'))||{}).year]")
            line = await A.inner_text('#ccLine'); print('    A:', cc[0], len(cc[1]), 'games,', cc[2], '|', line)
            if cc[0] != 'CCPlayer' or len(cc[1]) != 9 or not all(i.startswith('cc-') for i in cc[1]) or 'Chess.com' not in (cc[2] or ''): fails.append(f'Chess.com games: {cc}')
            if '9 new games added' not in line: fails.append('Chess.com line: ' + line)
            await A.wait_for_timeout(800)
            await B.reload(); await B.wait_for_timeout(600); await stand_in(B); await B.wait_for_timeout(1500)
            n = await B.evaluate("[chesscomName, myGames.filter(g=>siteOf(g)==='chesscom').length]"); print('    B after reload:', n)
            if n != ['CCPlayer', 9]: fails.append(f'Chess.com on device B: {n}')
            await A.evaluate("screen='mygames'; render()"); await A.screenshot(path=str(T.SHOTS/'accounts_chesscom.png'))
            rows = await A.evaluate("[...document.querySelectorAll('.mg-table tbody tr')].map(r=>[...r.children].map(c=>c.innerText.trim()))")
            print('    table:', rows)
            if [r[0] for r in rows] != ['Masters', 'Lichess', 'Chess.com'] or rows[2][1] != '9' or rows[1][1] != str(len(games)): fails.append(f'games table: {rows}')
            if await A.query_selector('#pgnFile'): fails.append('the website still offers adding a PGN file')
            await A.click('#ccDisconnect'); await A.wait_for_timeout(800)
            n = await A.evaluate("[chesscomName, myGames.filter(g=>siteOf(g)==='chesscom').length, !!document.querySelector('#ccUser')]"); print('    A after disconnect:', n)
            if n != ['', 0, True]: fails.append(f'Chess.com disconnect: {n}')
            if any(g['id'].startswith('cc-') for g in api('GET', '/api/games')['games']): fails.append('Chess.com games left in the account after disconnect')
            # 3. B plays one: in the account. B logs out: B's copy cleared, the account keeps it.
            await play_one(B); await B.wait_for_timeout(1200)
            if len(api('GET', '/api/results?after=-1')['rows']) != 3: fails.append('a result played on B did not reach the account')
            await B.evaluate("screen='progress'; render()"); await B.click('#pfLogout'); await B.wait_for_timeout(1500)
            n = await B.evaluate("[results.length, myGames.length, lichessAuth, localStorage.getItem('cst.owner')]"); print('3. B after logout:', n)
            if n != [0, 0, None, None]: fails.append(f'B not cleared after logout: {n}')
            if len(api('GET', '/api/results?after=-1')['rows']) != 3: fails.append('logout lost results')
            # 4. Someone else logs in on A while A holds Taussane's copy: it must not reach their account.
            await A.evaluate("lichessAuth = null; localStorage.removeItem('cst.lichessAuth')")   # as if the token were simply lost
            who[0] = 'tok-other'
            await login(A); await A.wait_for_timeout(1000)
            other = api('GET', '/api/results?after=-1', 'tok-other')['rows']
            n = await A.evaluate("[results.length, myGames.length]"); print('4. other person on A: their account', len(other), '| A now', n)
            if other or n[0]: fails.append('a previous player\'s results reached another account')
            # 5. Delete Other's account from A, then check Taussane's is intact; delete it too.
            await A.evaluate("screen='progress'; render()"); await A.click('#pfDelete'); await A.click('#pfDeleteYes'); await A.wait_for_timeout(1200)
            me = api('GET', '/api/me', 'tok-other')   # signing in again makes a fresh, empty account
            print('5. other deleted; taussane still has', len(api('GET', '/api/results?after=-1')['rows']), 'results')
            if len(api('GET', '/api/results?after=-1')['rows']) != 3: fails.append('deleting one account touched another')
            await A.screenshot(path=str(T.SHOTS/'accounts_after_delete.png'))
            for e in errsA + errsB:
                if 'importScripts' not in e: fails.append('page error: ' + e)
            await p['b'].close()
    finally:
        server.terminate()
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
