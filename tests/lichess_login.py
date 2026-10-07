# "Log in with Lichess" on the website, against a stand-in Lichess that checks the sign-in the way
# Lichess does (PKCE: the code verifier must match the challenge sent first, same redirect address,
# single-use code). Then: your username fills in, your games download with the token, the profile
# shows the account, a reload keeps you logged in, "Log out" revokes the token, and a cancelled
# login says so.
import asyncio, sys, pathlib, hashlib, base64, json, urllib.parse
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
ROOT = pathlib.Path(__file__).resolve().parent.parent
CORS = {'access-control-allow-origin':'*', 'access-control-allow-headers':'authorization, content-type, accept', 'access-control-allow-methods':'GET, POST, DELETE, OPTIONS'}
async def main():
    fails = []
    SITE = (ROOT/'index.html').read_text()
    L = {'auth':None, 'codes':{}, 'revoked':[], 'games_auth':[], 'deny':False}
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width':390,'height':760})
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        async def route(r):
            u, m = r.request.url, r.request.method
            if m == 'OPTIONS': return await r.fulfill(status=204, headers=CORS)
            if 'chess.js' in u: return await r.fulfill(body=T.CHESS, content_type='application/javascript')
            if u.startswith('https://site.test/'): return await r.fulfill(body=SITE, content_type='text/html')
            if u.startswith('https://lichess.org/oauth?'):
                q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(u).query)); L['auth'] = q
                # Lichess's approval page, already approved (or cancelled): back to the site.
                back = q['redirect_uri'] + ('?error=access_denied&state=' if L['deny'] else '?code=c1&state=') + q['state']
                if not L['deny']: L['codes']['c1'] = q
                return await r.fulfill(body=f'<script>location.replace({json.dumps(back)})</script>', content_type='text/html')
            if u == 'https://lichess.org/api/token' and m == 'POST':
                f = dict(urllib.parse.parse_qsl(r.request.post_data or '')); q = L['codes'].pop(f.get('code'), None)
                ch = base64.urlsafe_b64encode(hashlib.sha256(f.get('code_verifier','').encode()).digest()).decode().rstrip('=')
                ok = q and q['code_challenge'] == ch and f.get('redirect_uri') == q['redirect_uri'] and f.get('client_id') == q['client_id'] and f.get('grant_type') == 'authorization_code'
                return await r.fulfill(status=200 if ok else 400, body=json.dumps({'access_token':'tok123','token_type':'Bearer','expires_in':31536000} if ok else {'error':'invalid_grant'}), content_type='application/json', headers=CORS)
            if u == 'https://lichess.org/api/token' and m == 'DELETE':
                L['revoked'].append(r.request.headers.get('authorization')); return await r.fulfill(status=204, headers=CORS)
            if u == 'https://lichess.org/api/account':
                ok = r.request.headers.get('authorization') == 'Bearer tok123'
                return await r.fulfill(status=200 if ok else 401, body=json.dumps({'id':'testplayer','username':'TestPlayer'} if ok else {'error':'No such token'}), content_type='application/json', headers=CORS)
            if u.startswith('https://lichess.org/api/games/user/TestPlayer?'):
                L['games_auth'].append(r.request.headers.get('authorization'))
                return await r.fulfill(body=pathlib.Path(T.SAMPLE).read_text(), content_type='application/x-chess-pgn', headers=CORS)
            await r.abort()
        await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
        await pg.goto('https://site.test/'); await pg.wait_for_timeout(300)
        await pg.evaluate("(()=>{"+T.FAKE+" render(); })()")
        await pg.click('#myGamesBtn'); await pg.screenshot(path=str(T.SHOTS/'login_1_before.png'))
        await pg.click('#lichessLogin'); await pg.wait_for_timeout(2500); print('url:', pg.url)
        print('asked Lichess for:', {k: L['auth'][k] for k in ('client_id','redirect_uri','code_challenge_method','response_type')})
        st = await pg.evaluate("[location.search, lichessAuth && lichessAuth.username, myName, screen, myGames.length]"); print('after login:', st)
        if st[:4] != ['', 'TestPlayer', 'TestPlayer', 'mygames']: fails.append(f'login: {st}')
        await pg.evaluate("(()=>{"+T.FAKE+" })()")
        await pg.wait_for_timeout(500)
        n = await pg.evaluate("myGames.length"); print('games after first login:', n, '| sent with', L['games_auth'])
        if n != 10 or L['games_auth'][-1:] != ['Bearer tok123']: fails.append(f'games after login: {n} {L["games_auth"]}')
        txt = await pg.inner_text('.mg-card'); print('card:', txt.split('\n')[1])
        if 'Logged in as TestPlayer' not in txt or await pg.query_selector('#lichessUser'): fails.append('card after login')
        await pg.screenshot(path=str(T.SHOTS/'login_2_after.png'))
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('#progressBtn'); txt = await pg.inner_text('.pf-lichess'); print('profile:', txt.replace('\n',' '))
        if 'TestPlayer' not in txt: fails.append('profile after reload: ' + txt)
        await pg.click('#pfLogout'); await pg.wait_for_timeout(300)
        st = await pg.evaluate("[lichessAuth, localStorage.getItem('cst.lichessAuth')]"); print('after logout:', st, L['revoked'])
        if st != [None, None] or L['revoked'] != ['Bearer tok123']: fails.append('logout')
        # Cancelled on Lichess.
        L['deny'] = True
        await pg.click('#pfLogin'); await pg.wait_for_timeout(2000)
        note = await pg.inner_text('.mg-note'); print('cancelled:', note)
        if 'cancelled' not in note: fails.append('cancel note: ' + note)
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
