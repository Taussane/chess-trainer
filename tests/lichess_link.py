# "Open in Lichess": a position from a game opens the WHOLE game at that position (#ply), from the
# side to play. Master games (and Chess.com's): Lichess's analysis board with the moves; replaying
# them up to that ply must give the position shown. Your Lichess games: the game's own page.
import asyncio, sys, pathlib, urllib.parse
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
CHECK = """(p=>{ const u = lichessUrl(p), m = u.match(/analysis\\/pgn\\/([^?]+)\\?color=(\\w+)#(\\d+)$/);
  if(!m) return 'no whole game: ' + u;
  const sans = m[1].split('_').map(decodeURIComponent), c = new Chess();
  for(const s of sans.slice(0, +m[3])) if(!c.move(s)) return 'bad move ' + s;
  if(c.fen().split(' ').slice(0,4).join(' ') !== p.fen.split(' ').slice(0,4).join(' ')) return 'wrong position at #' + m[3];
  if(m[2] !== (p.side==='b' ? 'black' : 'white')) return 'wrong side';
  return 'ok'; })"""
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        r = await pg.evaluate(f"(()=>{{ const f = {CHECK}; const out = {{}}; ['analysis','candidates','final'].forEach(a=>POOLS[a].forEach(x=>{{ const v = f(x); out[v] = (out[v]||0)+1; }})); return out; }})()")
        print('masters:', r)
        if list(r) != ['ok']: fails.append(f'masters: {r}')
        await pg.click('#accountBtn'); await pg.fill('#lichessUser', 'TestPlayer')
        await pg.set_input_files('#pgnFile', T.SAMPLE); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""(()=>{ const out = {}; myPositions.forEach(x=>{ const u = lichessUrl(x), m = u.match(/^https:\/\/lichess\.org\/([A-Za-z0-9]{8})(\/black)?#(\d+)$/);
          const v = !m ? 'not the game page: ' + u : m[1]!==x.gameId ? 'wrong game' : +m[3]!==x.ply ? 'wrong move' : (!!m[2])!==(x.side==='b') ? 'wrong side' : 'ok';
          out[v] = (out[v]||0)+1; }); return out; })()""")
        print('my games:', r)
        if list(r) != ['ok']: fails.append(f'my games: {r}')
        t = await pg.evaluate("lichessUrl(TEST_POSITIONS[0])")
        if 'analysis/standard/' not in t: fails.append('a test position should open on its own: ' + t)
        await pg.click('#homeBtn'); await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
        await pg.evaluate("fenEvalStore = {}; render()"); await pg.click('#check'); await pg.wait_for_timeout(2500)
        href = await pg.get_attribute('a.btn.secondary', 'href'); print('review link:', href[:70] + '…' + href[-14:])
        if '/analysis/pgn/' not in href: fails.append('the review link is not the whole game')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
