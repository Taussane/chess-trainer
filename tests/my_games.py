# "My games": uploads a Lichess-style PGN (tests/lichess-sample.pgn), checks what is skipped,
# that Lichess-analysed games give positions at once, that the background scan analyses the rest,
# that every mistake goes into both Candidate moves and Final choice, that "My games" positions open in
# the exercises, and that everything survives a reload. Uses a stand-in engine (scores from
# material, so a lost piece reads as a mistake).
# Needs: pip install playwright (with a Chromium browser).
import asyncio, pathlib, sys
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT/'app'/'index.html').read_text()
CHESS = (ROOT/'vendor'/'chess.js'/'chess.js').read_text()
SAMPLE = str(ROOT/'tests'/'lichess-sample.pgn')
SHOTS = ROOT/'tests'/'shots'; SHOTS.mkdir(exist_ok=True)
FAKE = """
window.__fakeScore = fen=>{ const g=new Chess(fen); let s=0; const v={p:100,n:300,b:300,r:500,q:900,k:0};
  g.board().forEach(r=>r.forEach(c=>{ if(c) s += (c.color===g.turn()?1:-1)*v[c.type]; })); return s; };
window.__fakeSearch = (fen, sm, mpv)=>{ const g=new Chess(fen);
  const ms = sm ? sm.split(' ') : g.moves({verbose:true}).map(m=>m.from+m.to+(m.promotion||''));
  const lines = ms.map(u=>{ const h=new Chess(fen); h.move({from:u.slice(0,2),to:u.slice(2,4),promotion:u[4]}); return {uci:u, cp:-__fakeScore(h.fen()), mate:null}; })
    .sort((a,b)=>b.cp-a.cp).slice(0, sm ? ms.length : (mpv||5));
  lines.forEach((l,i)=>{ l.cp += 30 - i*45; });   // spread the grades
  return {lines, bestUci: lines[0] && lines[0].uci}; };
engineEval = (fen, sm)=>new Promise(res=>setTimeout(()=>res(__fakeSearch(fen, sm, 5)), 20));
bgEval = (fen, o)=>new Promise(res=>setTimeout(()=>res(__fakeSearch(fen, o&&o.searchmoves, o&&o.multipv)), 2));
failEngine = ()=>{}; sfState = 'ready'; engineErrorBanner = ()=>'';
"""
async def page_with_app(p, storage=None, in_claude=True):
    # in_claude: the page as published inside Claude (window.claude present, nothing granted);
    # False: the website, where games are fetched from Lichess directly.
    b = await p.chromium.launch(); ctx = await b.new_context(viewport={'width':390,'height':760})
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    async def route(r):
        if 'chess.js' in r.request.url: await r.fulfill(body=CHESS, content_type='application/javascript')
        elif r.request.url.startswith('https://app.test/'): await r.fulfill(body='<!doctype html><html><head><meta charset="utf-8"></head><body>'+SRC+'</body></html>', content_type='text/html')
        else: await r.abort()
    await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
    if in_claude: await pg.add_init_script("window.claude = { use: async()=>null };")
    if storage: await pg.add_init_script(f"localStorage.setItem('cst.mygames.v1', {storage!r});")
    await pg.goto('https://app.test/'); await pg.wait_for_timeout(300)
    await pg.evaluate("(()=>{"+FAKE+" render(); myBackground(); })()")
    return b, pg, errs
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await page_with_app(p)
        dis = await pg.evaluate("[...document.querySelectorAll('[data-src]')].map(x=>x.dataset.src+':'+x.disabled).join(' ')")
        if 'mine:true' not in dis: fails.append('source buttons not disabled before any games: '+dis)
        await pg.click('#accountBtn'); await pg.wait_for_timeout(200)
        await pg.fill('#lichessUser', 'TestPlayer')
        href = await pg.get_attribute('#exportLink', 'href')
        if 'games/user/TestPlayer' not in href or 'evals=true' not in href or 'bullet,blitz' not in href: fails.append('export link: '+href)
        async with pg.expect_file_chooser(timeout=3000) as fc:   # a real tap must open the browser's file chooser
            await pg.click('.file-btn')
        await (await fc.value).set_files(SAMPLE); await pg.wait_for_timeout(400)
        note = await pg.inner_text('.mg-note'); print('note:', note)
        if 'Added 10 games' not in note or '5 already analysed' not in note or '1 variant' not in note: fails.append('import note: '+note)
        await pg.screenshot(path=str(SHOTS/'mg_1_after_upload.png'))
        seen = []; counts_seen = []; ba_keys = []
        for _ in range(60):
            seen.append(await pg.evaluate("(document.querySelector('.mg-status')||{}).innerText || ''"))
            counts_seen.append(await pg.evaluate("countsOf(myPositions)"))
            ba_keys.append(set(await pg.evaluate("myPositions.filter(p=>p.acts.includes('analysis')).map(p=>p.key)")))
            st = await pg.evaluate("({queued:myGames.filter(g=>g.status==='queued').length, pending:0, running:myBgRunning})")
            if not st['queued'] and not st['pending'] and not st['running']: break
            await pg.wait_for_timeout(500)
        import re as _re
        await pg.wait_for_timeout(300); seen.append(await pg.inner_text('.mg-status'))
        nums = [int(m.group(1)) for t in seen for m in [_re.match(r'Analysing your games: (\d+) of 10 done', t)] if m]
        print('status lines:', sorted(set(seen))[:4], '…', seen[-1])
        if any(t and not (_re.match(r'Analysing your games: \d+ of 10 done', t) or t == 'All games analysed.') for t in seen): fails.append(f'unexpected status line: {set(seen)}')
        if nums != sorted(nums): fails.append(f'the counter went backwards: {nums}')
        if seen[-1] != 'All games analysed.': fails.append('final status: ' + seen[-1])
        if any(not (ba_keys[i] <= ba_keys[i+1]) for i in range(len(ba_keys)-1)): fails.append('a Board analysis position was removed during analysis')
        for a in ('analysis','candidates','final'):
            xs = [c[a] for c in counts_seen]
            if xs != sorted(xs): fails.append(f'{a} positions went down during analysis: {xs}')
        counts = await pg.evaluate("countsOf(myPositions)"); print('my positions:', counts)
        if st['queued'] or st['pending']: fails.append(f'background not finished: {st}')
        if counts['analysis'] < 5: fails.append(f'too few Board analysis positions: {counts}')
        if counts['candidates'] + counts['final'] < 3: fails.append(f'too few mistake positions: {counts}')
        mine_only = await pg.evaluate("myPositions.every(p=>!p.acts.includes('analysis') ? p.side===myGames.find(g=>g.id===p.gameId).me : true) && myPositions.filter(p=>p.acts.includes('candidates')).every(p=>p.acts.includes('final') || new Chess(p.fen).moves().length<4)")
        if not mine_only: fails.append('a mistake position is not the player to move, or not in both exercises')
        excl = await pg.evaluate("new Set(myPositions.map(p=>p.key)).size===myPositions.length")
        if not excl: fails.append('a position is used twice')
        await pg.screenshot(path=str(SHOTS/'mg_2_done.png'))
        print('status:', await pg.inner_text('.mg-status'), '| table:', (await pg.inner_text('.mg-table')).replace('\n',' | ').replace('\t',' '))
        # Exercises on "My games"
        await pg.click('#homeBtn'); await pg.wait_for_timeout(200)
        await pg.click('[data-src="mine"]'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(SHOTS/'mg_3_home.png'))
        for act in ['analysis','candidates','final']:
            if counts[act] == 0: continue
            await pg.click(f'.card[data-go="{act}"]'); await pg.wait_for_timeout(1500)
            t = await pg.evaluate("pos().key+' | '+pos().title+' | '+pos().year")
            print(act, '→', t)
            if not t.startswith('own:'): fails.append(f'{act} did not open one of your positions: {t}')
            if act=='final':
                n = await pg.evaluate("(finalMoves(pos())||[]).length")
                if n != 4: fails.append(f'final shows {n} moves')
                await pg.screenshot(path=str(SHOTS/'mg_4_final.png'))
            await pg.click('#homeBtn'); await pg.wait_for_timeout(200)
        saved = await pg.evaluate("localStorage.getItem('cst.mygames.v1')")
        await b.close()
        # Reload: everything comes back from the saved copy, nothing is re-analysed
        b, pg, errs2 = await page_with_app(p, saved)
        n = await pg.evaluate("[myGames.length, myPositions.length, myGames.filter(g=>g.status!=='evaluated').length]"); print('after reload:', n)
        if n[0] != 10 or n[1] == 0 or n[2] != 0: fails.append(f'after reload: {n}')
        # Upload again: everything already there
        await pg.click('#accountBtn'); await pg.set_input_files('#pgnFile', SAMPLE); await pg.wait_for_timeout(300)
        note = await pg.inner_text('.mg-note')
        if 'Added 0 games' not in note or '10 already added' not in note: fails.append('re-upload note: '+note)
        # Paste route: remove, then paste the same file's text
        await pg.click('#clearBtn'); await pg.click('#clearYes'); await pg.wait_for_timeout(200)
        await pg.click('#pasteToggle'); await pg.fill('#pgnPaste', pathlib.Path(SAMPLE).read_text()); await pg.click('#pasteAdd'); await pg.wait_for_timeout(300)
        note = await pg.inner_text('.mg-note'); print('paste note:', note)
        if 'Added 10 games' not in note: fails.append('paste: '+note)
        # Remove
        await pg.click('#clearBtn'); await pg.click('#clearYes'); await pg.wait_for_timeout(200)
        n = await pg.evaluate("[myGames.length, myPositions.length, source]")
        if n != [0, 0, 'masters']: fails.append(f'after removing: {n}')
        await b.close()
        errs = [e for e in errs + errs2 if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok')
    sys.exit(1 if fails else 0)
if __name__=="__main__": asyncio.run(main())
