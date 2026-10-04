# Fixes from the October 2026 review, each checked with a stand-in engine and a stand-in account
# database:
#  1. more than 1000 results load in full, and none are added twice;
#  2. a review left before its evaluation arrived is still recorded when reopened;
#  3. a Final choice question only looked at doesn't hold back a position played elsewhere today;
#  4. Final choice: a game move outside the engine's top 5 is judged in one search with them;
#  5. games removed on another device don't come back;
#  6. missed positions follow the results (no separate list to fall out of step);
#  7. the routine skips an exercise with nothing left today;
#  8. an engine that stops answering shows the error instead of waiting forever.
import asyncio, sys, pathlib, json
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T

FAKEDB = """
(()=>{
  const S = window.__S = { results: %s, games: %s, meta: %s };
  window.__adds = 0;
  const query = (rows, f=[], lim=1000) => ({
    where(field, op, v){ return query(rows, f.concat([[field, op, v]]), lim); },
    orderBy(){ return query(rows, f, lim); },
    limit(n){ return query(rows, f, n); },
    get: async()=>{ let r = rows().slice().sort((a,b)=>(a.ts||0)-(b.ts||0));
      f.forEach(([k,op,v])=>{ r = r.filter(x=>op==='>' ? x[k] > v : true); });
      return { docs: r.slice(0, lim).map(d=>({ data:()=>d })) }; },
  });
  const col = path => {
    const name = path.split('/').pop();
    if(name==='results') return { ...query(()=>S.results), add: async r=>{ __adds++; S.results.push(r); } };
    if(name==='games') return { ...query(()=>S.games), doc: id=>({ set: async g=>{ S.games = S.games.filter(x=>x.id!==id).concat([g]); }, delete: async()=>{ S.games = S.games.filter(x=>x.id!==id); } }) };
    return { doc: id=>doc(path+'/'+id) };
  };
  const doc = p => ({ get: async()=>({ exists: p in S.meta, data: ()=>S.meta[p] }), set: async v=>{ S.meta[p] = v; } });
  window.claude = { use: async n => n==='db' ? { collection: col, doc } : n==='user' ? { id: async()=>'u1', isOwner: async()=>false } : null };
})();
"""

async def open_app(p, results=None, games=None, meta=None, local=None, fake_engine=True):
    b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width':390,'height':760})
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    async def route(r):
        if 'chess.js' in r.request.url: await r.fulfill(body=T.CHESS, content_type='application/javascript')
        elif r.request.url.startswith('https://app.test/'): await r.fulfill(body='<!doctype html><html><head><meta charset="utf-8"></head><body>'+T.SRC+'</body></html>', content_type='text/html')
        else: await r.abort()
    await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
    await pg.add_init_script(FAKEDB % (json.dumps(results or []), json.dumps(games or []), json.dumps(meta or {})))
    for k, v in (local or {}).items(): await pg.add_init_script(f"localStorage.setItem({k!r}, {v!r});")
    await pg.goto('https://app.test/'); await pg.wait_for_timeout(600)
    if fake_engine: await pg.evaluate("(()=>{"+T.FAKE+" fenEvalStore = {}; poolEvalStore = {}; render(); })()")
    return b, pg, errs

def rows(n, t0=1700000000000):
    return [{'a':'analysis', 'acc':70, 'ts':t0 + i*1000, 'src':'masters'} for i in range(n)]

async def main():
    fails = []; allerrs = []
    async with async_playwright() as p:
        # 1. 2500 results in the account, the same 2500 on this device.
        r = rows(2500)
        b, pg, errs = await open_app(p, results=r, local={'cst.results.v1': json.dumps(r)}); allerrs += errs
        n = await pg.evaluate("[results.length, __adds, __S.results.length]"); print('1. results, re-added, in account:', n)
        if n != [2500, 0, 2500]: fails.append(f'results paging: {n}')
        await b.close()
        b, pg, errs = await open_app(p, results=r); allerrs += errs   # a new device
        n = await pg.evaluate("[results.length, results[results.length-1].ts]"); print('   new device:', n)
        if n != [2500, r[-1]['ts']]: fails.append(f'new device paging: {n}')
        await b.close()

        # 2. Check, then home before the evaluation is in; reopen.
        b, pg, errs = await open_app(p); allerrs += errs
        await pg.evaluate("""(()=>{ const real = engineEval; engineEval = (f,s)=>new Promise(res=>setTimeout(()=>real(f,s).then(res), 1500)); fenEvalStore = {}; poolEvalStore = {}; })()""")
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(200)
        k = await pg.evaluate("pos().key")
        await pg.evaluate("(()=>{ st('analysis').guess = 70; render(); })()")
        await pg.click('#check'); await pg.click('#homeBtn'); await pg.wait_for_timeout(2000)
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(2500)
        n = await pg.evaluate(f"[pos().key, results.length, isPlayed({k!r})]"); print('2. reopened on', n[0]==k, 'results', n[1], 'played', n[2])
        if n != [k, 1, True]: fails.append(f'unrecorded review: {n}')
        await b.close()

        # 3. Final choice opened but not touched; its position is then played elsewhere today.
        b, pg, errs = await open_app(p); allerrs += errs
        await pg.click('.card[data-go="final"]'); await pg.wait_for_timeout(1500)
        k = await pg.evaluate("pos().key")
        await pg.click('#homeBtn'); await pg.evaluate(f"markPlayed({k!r})")
        await pg.click('.card[data-go="final"]'); await pg.wait_for_timeout(300)
        if await pg.evaluate("pos().key") == k: fails.append('an untouched Final choice kept a position played today')
        print('3. untouched Final choice gives way:', await pg.evaluate("pos().key") != k)

        # 4. Game move outside the top 5: picked from one search with the top 5 and the game move.
        await pg.evaluate("""(()=>{ window.__searches = []; const real = engineEval;
          engineEval = (f,s)=>{ __searches.push(s||'top5'); return real(f,s); }; fenEvalStore = {}; poolEvalStore = {}; })()""")
        info = await pg.evaluate("""(async()=>{
          const p = POOLS.final.find(p=>{ const sr = __fakeSearch(p.fen, null, 5); return !sr.lines.some(l=>l.uci===p.hist.uci); });
          if(!p) return null;
          for(let i=0;i<50 && !Array.isArray(finalMoves(p)); i++) await new Promise(r=>setTimeout(r,50));
          const ms = finalMoves(p);
          return { gm: p.hist.uci, shown: ms.map(m=>m.uci), searches: __searches.slice() };
        })()""")
        print('4.', info)
        if not info: fails.append('no test position with the game move outside the top 5')
        else:
            if info['gm'] not in info['shown']: fails.append('game move missing from the four')
            if not any(info['gm'] in x and len(x.split()) == 6 for x in info['searches']): fails.append('game move not judged with the top 5 before picking')
        await b.close()

        # 5. Games removed on another device (after they were added here) stay removed.
        g = {'id':'g1', 'white':'A', 'black':'B', 'me':'w', 'year':'2026', 'speed':'blitz', 'result':'1-0', 'sans':['e4','e5','Nf3','Nc6'], 'evals':None, 'status':'queued', 'positions':[], 'addedAt': 1000}
        b, pg, errs = await open_app(p, meta={'data/users/u1/trainer/meta/games-cleared': {'at': 2000}}, local={'cst.mygames.v1': json.dumps([g])}); allerrs += errs
        await pg.wait_for_timeout(300)
        n = await pg.evaluate("[myGames.length, __S.games.length]"); print('5. games after a removal elsewhere:', n)
        if n != [0, 0]: fails.append(f'removed games came back: {n}')
        await b.close()
        g2 = dict(g, addedAt=3000)   # added after the removal: kept and saved to the account
        b, pg, errs = await open_app(p, meta={'data/users/u1/trainer/meta/games-cleared': {'at': 2000}}, local={'cst.mygames.v1': json.dumps([g2])}); allerrs += errs
        await pg.wait_for_timeout(300)
        n = await pg.evaluate("[myGames.length, __S.games.length]"); print('   a game added later:', n)
        if n != [1, 1]: fails.append(f'a game added after the removal was dropped: {n}')
        await b.close()

        # 6. Missed positions come from the results: a miss on another device shows here, and a
        # list saved before (here X) gives way once X has a newer result.
        k0 = 'r2qkb1r/2pp1ppp/p1n1p1b1/1p6/1PPP4/P3P1P1/3N1P1P/R1BQKB1R w KQkq -'
        res = rows(6) + [{'a':'analysis', 'acc':40, 'ts':1700000100000, 'src':'masters', 'key':k0, 'miss':True}]
        b, pg, errs = await open_app(p, results=res, local={'cst.replay.v1': json.dumps([{'key':'X','a':'analysis','ts':1}, {'key':k0,'a':'analysis','ts':1}])}); allerrs += errs
        n = await pg.evaluate("missedList().map(x=>x.key)"); print('6. missed:', [x[:12] for x in n])
        if sorted(n) != sorted(['X', k0]): fails.append(f'missed list: {n}')
        await pg.evaluate(f"results.push({{a:'analysis', acc:90, ts:Date.now(), key:{k0!r}, miss:false}})")
        n = await pg.evaluate("missedList().map(x=>x.key)")
        if n != ['X']: fails.append(f'a position played well stayed missed: {n}')
        await b.close()

        # 7. Routine: Candidate moves has nothing left today -> the routine goes from Board
        # analysis straight to Final choice.
        b, pg, errs = await open_app(p); allerrs += errs
        await pg.evaluate("(()=>{ POOLS.candidates.forEach(p=>markPlayed(p.key)); render(); })()")
        await pg.click('#routineBtn'); await pg.wait_for_timeout(200)
        await pg.evaluate("(()=>{ st('analysis').guess = 70; render(); })()")
        await pg.click('#check'); await pg.wait_for_timeout(2500)
        lbl = await pg.inner_text('#nextPos'); print('7. routine next:', lbl)
        if lbl != 'Final choice ›': fails.append(f'routine did not skip Candidate moves: {lbl}')
        await b.close()

        # 8. The engine never answers: after the watchdog, the error shows.
        b, pg, errs = await open_app(p, fake_engine=False); allerrs += errs
        await pg.evaluate("""(()=>{ sfState='ready'; sfBusy=false; sfQueue=[]; bgQueue=[]; sfWorker = { postMessage(){} }; fenEvalStore = {}; render(); })()""")
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(200)
        await pg.wait_for_timeout(11800)
        txt = await pg.inner_text('#app'); print('8.', 'stopped working' in txt)
        if 'stopped working' not in txt: fails.append('no error after the engine stopped answering')
        await b.close()
    allerrs = [e for e in allerrs if 'importScripts' not in e]
    if allerrs: fails.append(f'page errors: {allerrs[:3]}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
