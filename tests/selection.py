# Which of your positions comes next ("My games"): the core list (your last 100 games) in one line,
# never-played positions newest game first, then those got right, longest-ago success first;
# picks weighted down the line; Replay (missed, not tried for a week, any game) gets 10%.
# Also the rotation: a 101st game retires the oldest; a retired game stays only while it has a
# missed position.
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
SETUP = """(()=>{
  bgEval = ()=>new Promise(()=>{});
  const day = 864e5, now = Date.now(), fen = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1';
  // 101 games, game i played i days ago, one Candidate moves position each.
  myGames = Array.from({length:101}, (_, i)=>({ id:'g'+i, sans:['e4'], me:'b', playedAt: now - i*day, status:'evaluated',
    positions:[{ key:'own:g'+i+':1', fen, side:'b', moveNo:1, title:'t', year:'', last:null, hist:{uci:'e7e5', san:'e5', from:'e7', to:'e5'}, acts:['candidates'], gameId:'g'+i, ply:1 }] }));
  myGamesLoaded = true; progressReady();
  results = [
    { a:'candidates', acc:90, ts: now - 1*day,  key:'own:g3:1',  miss:false },   // got right yesterday
    { a:'candidates', acc:90, ts: now - 20*day, key:'own:g4:1',  miss:false },   // got right long ago
    { a:'candidates', acc:20, ts: now - 2*day,  key:'own:g5:1',  miss:true  },   // missed this week: resting
    { a:'candidates', acc:20, ts: now - 9*day,  key:'own:g6:1',  miss:true  },   // missed 9 days ago: Replay
    { a:'candidates', acc:20, ts: now - 30*day, key:'own:g100:1', miss:true },   // missed, oldest game: Replay
    { a:'candidates', acc:90, ts: now - 30*day, key:'own:g99:1', miss:false },   // got right, game 99
  ];
  onOwnPositionsChanged();
})()"""
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        await pg.evaluate(SETUP)
        await pg.evaluate("rotateMyGames()")
        st = await pg.evaluate("[myGames.length, myGames.filter(g=>g.retired).map(g=>g.id)]"); print('rotation:', st)
        if st != [101, ['g100']]: fails.append(f'the 101st game should leave the core list but stay (it has a missed position): {st}')
        c = await pg.evaluate("(()=>{ const v = mineCandidates('candidates'); return { core: v.core.map(p=>p.gameId), replay: v.replay.map(p=>p.gameId) }; })()")
        print('core line starts', c['core'][:4], '… ends', c['core'][-3:], '| replay', sorted(c['replay']))
        if c['core'][:3] != ['g0', 'g1', 'g2'] or c['core'][-3:] != ['g99', 'g4', 'g3']: fails.append(f'core order: {c["core"][:4]} … {c["core"][-3:]}')
        if sorted(c['replay']) != ['g100', 'g6']: fails.append(f'replay: {c["replay"]}')
        if 'g5' in c['core'] + c['replay']: fails.append('a position missed this week is offered')
        # First picks over many draws: front > back, Replay ≈ 10%, the latest success almost never.
        d = await pg.evaluate("""(()=>{ const n = 20000, f = {}; for(let i=0;i<n;i++){ const g = drawMine('candidates')[0].gameId; f[g] = (f[g]||0)+1; }
          const pct = g=>100*(f[g]||0)/n; return { front: pct('g0'), mid: pct('g50'), last: pct('g3'), replay: pct('g6') + pct('g100') }; })()""")
        print('first pick %:', {k: round(v, 2) for k, v in d.items()})
        if not (d['front'] > d['mid'] > d['last']): fails.append(f'weights do not slide down the line: {d}')
        if not (8 <= d['replay'] <= 12): fails.append(f'Replay share {d["replay"]:.1f}% (expected about 10%)')
        if d['last'] > 0.1: fails.append(f'the position just got right comes too often: {d["last"]:.2f}%')
        # Getting the retired game's missed position right removes the game for good.
        await pg.evaluate("results.push({ a:'candidates', acc:95, ts:Date.now(), key:'own:g100:1', miss:false }); rotateMyGames()")
        st = await pg.evaluate("[myGames.some(g=>g.id==='g100'), mineCandidates('candidates').replay.map(p=>p.gameId), mineCandidates('candidates').core.includes(undefined)]")
        print('after getting it right:', st)
        if st[0] or 'g100' in st[1]: fails.append(f'the retired game should be gone: {st}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
