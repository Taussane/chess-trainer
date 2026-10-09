# Reading games: a pawn capture on the b-file ("bxc6") must not cut a game short (chess.js's
# lenient reading takes it for a bishop move), and a game saved cut short earlier is completed when
# the same games are added again, keeping its engine checks.
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
PGN = '''[Event "Rated classical game"]
[Site "https://lichess.org/abcdEFGH"]
[White "TestPlayer"]
[Black "Other"]
[Result "1-0"]
[UTCDate "2026.09.01"]

1. e4 d6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Bf5 5. f3 Bxe4 6. fxe4 Nc6 7. Nf3 e6 8. Bb5 Qd7 9. Ne5 Qd6 10. Bxc6+ bxc6 11. O-O f6 12. Qh5+ g6 13. Nxg6 hxg6 14. Qxh8 Qxd4+ 15. Kh1 Qxe4 16. Qxg8 O-O-O 17. Bf4 g5 18. Bxg5 fxg5 19. Rxf8 Rxf8 20. Qxf8+ Kb7 1-0
'''
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        await pg.evaluate("bgEval = ()=>new Promise(()=>{}); myName = 'TestPlayer'")
        await pg.evaluate("pgn => importPgnText(pgn)", PGN)
        n = await pg.evaluate("myGames[0].sans.length"); print('moves read:', n)
        if n != 40: fails.append(f'game cut short at {n} half-moves')
        # A copy saved cut short (as before the fix), with one engine check: completed on re-adding.
        await pg.evaluate("(()=>{ const g = myGames[0]; g.sans = g.sans.slice(0, 19); g.checks = { 4: 12 }; extractOwnPositions(g); })()")
        await pg.evaluate("pgn => importPgnText(pgn)", PGN)
        st = await pg.evaluate("[myGames.length, myGames[0].sans.length, JSON.stringify(myGames[0].checks), myImportNote]"); print('re-added:', st)
        if st[:3] != [1, 40, '{"4":12}'] or 'Finished 1 game' not in st[3]: fails.append(f'repair: {st}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
