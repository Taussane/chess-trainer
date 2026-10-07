# Which positions come next (your games, and masters by the same rule):
#  - the core list: never-played positions, newest game first, then positions got right, the
#    longest-ago success first; missed positions are not in it;
#  - Replay: missed positions not tried in the past week (one tried 2 days ago waits);
#  - picks: Replay gets about 10%; in the core list, the front comes far more often than the end,
#    and the position just got right almost never;
#  - rotation: past 100 games, the oldest leave the core list; one with a missed position stays
#    (for Replay only), the others are removed; at most 100 games are kept for Replay, the oldest go.
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        await pg.evaluate("bgEval = ()=>new Promise(()=>{}); myName = 'TestPlayer'")
        await pg.evaluate("pgn => importPgnText(pgn)", pathlib.Path(T.SAMPLE).read_text())
        # Every game a known date (newest = index 0), all mistakes already checked (so positions exist).
        await pg.evaluate("""(()=>{ const day = 864e5, now = Date.now();
          myGames.forEach((g, i)=>{ g.playedAt = now - (i+1)*day; g.verified = true; if(!g.evals) g.evals = g.sans.map(()=>({cp:0})); extractOwnPositions(g); });
          onOwnPositionsChanged(); })()""")
        info = await pg.evaluate("""(()=>{ const a = 'analysis', day = 864e5, now = Date.now();
          const ps = mineCandidates(a).core; if(ps.length < 8) return { n: ps.length };
          // results: two got right (older and recent success), one missed 8 days ago, one missed 2 days ago
          const [ok1, ok2, miss8, miss2] = [ps[0], ps[1], ps[2], ps[3]];
          results.push({ a, acc:90, ts: now - 5*day, key: ok1.key, miss:false }, { a, acc:90, ts: now - 1*day, key: ok2.key, miss:false },
                       { a, acc:20, ts: now - 8*day, key: miss8.key, miss:true }, { a, acc:20, ts: now - 2*day, key: miss2.key, miss:true });
          results.sort((x,y)=>x.ts-y.ts);
          const c = mineCandidates(a), keys = c.core.map(p=>p.key), played = p=>gamePlayedAt(myGames.find(g=>g.id===p.gameId));
          const unseen = c.core.filter(p=>p.key!==ok1.key && p.key!==ok2.key);
          return { n: c.core.length, tail: keys.slice(-2), ok: [ok1.key, ok2.key], inCore: [miss8.key, miss2.key].filter(k=>keys.includes(k)).length,
                   replay: c.replay.map(p=>p.key), miss8: miss8.key,
                   newestFirst: unseen.every((p,i)=>!i || played(unseen[i-1]) >= played(p)) };
        })()""")
        print('core', info.get('n'), '| replay', len(info.get('replay', [])), '| newest first', info.get('newestFirst'))
        if info.get('n', 0) < 6: fails.append(f'too few positions to test: {info}')
        else:
            if info['tail'] != info['ok']: fails.append('got-right positions should end the line, longest-ago success first')
            if info['inCore']: fails.append('a missed position is in the core list')
            if info['replay'] != [info['miss8']]: fails.append(f'replay should hold only the position missed 8 days ago: {info["replay"]}')
            if not info['newestFirst']: fails.append('never-played positions are not newest game first')
        # First picks over many draws.
        st = await pg.evaluate("""(()=>{ const a = 'analysis', c = mineCandidates(a), n = 20000, first = {};
          for(let i=0; i<n; i++){ const k = drawMine(a)[0].key; first[k] = (first[k]||0) + 1; }
          const f = p=>(first[p.key]||0)/n;
          return { replay: c.replay.reduce((t,p)=>t+f(p),0), front: f(c.core[0]), last: f(c.core[c.core.length-1]), size: c.core.length }; })()""")
        print('first pick: replay %.3f | front %.3f | just got right %.4f (core %d)' % (st['replay'], st['front'], st['last'], st['size']))
        if not 0.08 <= st['replay'] <= 0.12: fails.append(f'replay share {st["replay"]:.3f}, expected about 0.10')
        if not st['front'] > 10 * max(st['last'], 1e-4): fails.append('the front of the line is not picked far more often than its end')
        # Rotation past 100 games.
        rot = await pg.evaluate("""(()=>{ progressLoaded = true;
          const oldest = myGames.slice().sort((x,y)=>gamePlayedAt(x)-gamePlayedAt(y));
          const keepMissed = oldest[0], plain = oldest[1];
          const pos = keepMissed.positions.find(p=>p.acts.includes('analysis'));
          results.push({ a:'analysis', acc:10, ts: Date.now() - 9*864e5, key: pos.key, miss:true }); results.sort((x,y)=>x.ts-y.ts);
          const base = myGames[0];
          for(let i=0; i<100; i++){ const g = JSON.parse(JSON.stringify(base)); g.id = 'new' + i; g.playedAt = Date.now() - i*1000; extractOwnPositions(g); myGames.push(g); }
          rotateMyGames();
          const k = myGames.find(g=>g.id===keepMissed.id);
          return { core: myGames.filter(g=>!g.retired).length, kept: !!k && k.retired, dropped: !myGames.some(g=>g.id===plain.id),
                   replayHasIt: mineCandidates('analysis').replay.some(p=>p.key===pos.key), coreHasOld: mineCandidates('analysis').core.some(p=>p.gameId===keepMissed.id) }; })()""")
        print('rotation:', rot)
        if rot != {'core': 100, 'kept': True, 'dropped': True, 'replayHasIt': True, 'coreHasOld': False}: fails.append(f'rotation: {rot}')
        # Masters use the same line: positions added to the library later come first; one got right goes last.
        ms = await pg.evaluate("""(()=>{ const a = 'final', P = POOLS[a], now = Date.now();
          const newer = P.slice(0, 5); newer.forEach(p=>p.added = (p.added||0) + 30*864e5);   // as if added a month later
          results.push({ a, acc:95, ts: now, key: P[10].key, miss:false }); results.sort((x,y)=>x.ts-y.ts); lineCache = {};
          const c = candidatesFor(a, 'masters'), keys = c.core.map(p=>p.key);
          const first = {}; for(let i=0; i<5000; i++){ const k = drawWeighted(a, 'masters')[0].key; first[k] = (first[k]||0)+1; }
          return { newerFirst: newer.every(p=>keys.indexOf(p.key) < 5), gotRightLast: keys[keys.length-1]===P[10].key,
                   newerShare: newer.reduce((t,p)=>t+(first[p.key]||0),0)/5000, size: keys.length }; })()""")
        print('masters line:', ms)
        if not ms['newerFirst'] or not ms['gotRightLast']: fails.append(f'masters line order: {ms}')
        if ms['newerShare'] < 5/ms['size']*1.5: fails.append(f'newer master positions not favoured: {ms}')
        # Games kept for Replay: at most 100, the oldest go first.
        cap = await pg.evaluate("""(()=>{ const base = myGames[0], now = Date.now(), day = 864e5;
          myGames = []; results = [];
          for(let i=0; i<230; i++){ const g = JSON.parse(JSON.stringify(base)); g.id = 'g' + i; g.playedAt = now - i*day; g.retired = false; extractOwnPositions(g); myGames.push(g); }
          // a missed position in each of the 130 oldest games
          for(let i=100; i<230; i++){ const p = myGames[i].positions.find(p=>p.acts.includes('analysis')); results.push({ a:'analysis', acc:10, ts: now - 30*day + i, key: p.key, miss:true }); }
          results.sort((x,y)=>x.ts-y.ts); onOwnPositionsChanged(); rotateMyGames();
          const kept = myGames.filter(g=>g.retired);
          return { core: myGames.filter(g=>!g.retired).length, replayGames: kept.length,
                   oldestKept: Math.max(...kept.map(g=>+g.id.slice(1))), replayPositions: mineCandidates('analysis').replay.length }; })()""")
        print('replay cap:', cap)
        if cap != {'core': 100, 'replayGames': 100, 'oldestKept': 199, 'replayPositions': 100}: fails.append(f'replay cap: {cap}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
