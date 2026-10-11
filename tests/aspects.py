# Imbalance reading, and the imbalances in Position evaluation's review: Stockfish 10's `eval` table,
# grouped into six imbalances, gauged as signs (−−− to +++), revealed one by one, drawn on the board.
import asyncio, sys, pathlib, json
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import my_games as T
FEN = 'r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8'
TABLE = "     Term    |    White    |    Black    |    Total   \n             |   MG    EG  |   MG    EG  |   MG    EG \n ------------+-------------+-------------+------------\n    Material |  ----  ---- |  ----  ---- |  0.02  1.21\n   Imbalance |  ----  ---- |  ----  ---- |  0.28  0.28\n  Initiative |  ----  ---- |  ----  ---- |  0.00  0.12\n       Pawns |  0.73  0.04 |  0.48 -0.02 |  0.25  0.06\n     Knights | -0.04 -0.13 | -0.17 -0.20 |  0.13  0.07\n     Bishops | -0.33 -0.99 | -0.40 -1.01 |  0.07  0.02\n       Rooks | -0.26 -0.02 |  0.00  0.00 | -0.26 -0.02\n      Queens |  0.00  0.00 |  0.00  0.00 |  0.00  0.00\n    Mobility |  0.32  0.79 |  0.25  0.83 |  0.07 -0.03\n King safety |  0.42 -0.08 |  0.52 -0.08 | -0.10  0.00\n     Threats |  0.13  0.12 |  0.07  0.06 |  0.07  0.06\n      Passed |  0.00  0.00 |  0.00  0.00 |  0.00  0.00\n       Space |  0.92  0.00 |  0.67  0.00 |  0.25  0.00\n     Variant |  0.00  0.00 |  0.00  0.00 |  0.00  0.00\n ------------+-------------+-------------+------------\n       Total |  ----  ---- |  ----  ---- |  0.79  1.77\n\nTotal evaluation: 0.88 (white side)"   # recorded from Stockfish.js 10 ("Total evaluation: 0.88")
async def main():
    fails = []
    async with async_playwright() as p:
        b, pg, errs = await T.page_with_app(p)
        # 1. Parsing: the aspects add up to Stockfish's own total (it adds a small bonus for the move).
        r = await pg.evaluate("([t, f])=>{ const a = parseAspects(t.split('\\n').concat(['Total evaluation: 0.88 (white side)']), f); return a && {a, sum: Object.values(a).reduce((x,y)=>x+y,0)}; }", [TABLE, FEN])
        print('parsed:', r and {k: round(v, 2) for k, v in r['a'].items()}, 'sum', r and round(r['sum'], 2))
        if not r or abs(r['sum'] - 0.88) > 0.2: fails.append(f'aspects do not add up to the total: {r}')
        if r and not 0.6 < r['a']['material'] < 1.2: fails.append('White is a pawn up: material should be about +0.9')
        n = await pg.evaluate("parseAspects(['Total evaluation: none (in check)'], 'k7/8/8/8/8/8/8/K7 w - - 0 1')")
        if n is not None: fails.append('in check should give no aspects')
        # 2. The engine path: an `eval` request answered in one message, and one never answered.
        r = await pg.evaluate("""async ([t, fen])=>{
          const sent = []; sfWorker = { postMessage: m=>sent.push(m) }; sfBusy = false; sfState = 'ready';
          const pr = engineAspects(fen);
          onEngineMessage({ data: t + '\\n\\nTotal evaluation: 0.88 (white side)' });
          const lines = await pr;
          const pr2 = engineAspects(fen); const t0 = Date.now(); const none = await pr2;
          return { sent, n: lines && lines.length, none, waited: Date.now()-t0, state: sfState, busy: sfBusy }; }""", [TABLE, FEN])
        print('engine path:', {k: v for k, v in r.items() if k != 'sent'}, r['sent'][:2])
        if 'eval' not in r['sent'] or 'position fen '+FEN not in r['sent'] or not r['n'] or r['n'] < 15: fails.append(f'eval request: {r}')
        if r['none'] is not None or r['state'] != 'ready' or r['busy']: fails.append(f'an unanswered eval should give nothing and leave the engine working: {r}')
        await pg.evaluate("sfWorker = null")
        # 3. Imbalance reading: no bar; the prompt; every imbalance "=" at first.
        await pg.click('.card[data-go="imbalances"]'); await pg.wait_for_timeout(300)
        await pg.evaluate("""t=>{ engineAspects = fen=>Promise.resolve(t.split('\\n')); aspectsStore = {}; render(); }""", TABLE)
        prompt = await pg.text_content('#imbPrompt')
        if prompt != 'Gauge each imbalance: who has the edge, and how big?': fails.append(f'prompt: {prompt}')
        if await pg.query_selector('#evalBar'): fails.append('Imbalance reading has no evaluation bar')
        start = await pg.evaluate("[...document.querySelectorAll('#aspInput .asp-pick')].map(b=>b.textContent).join(' ')")
        if start != '= = = = = =': fails.append(f'imbalances should start at =: {start}')
        h1 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        # 4. Gauging: tap a badge, then a level (the scale opens above it); slide; arrow keys; a tap elsewhere closes it.
        await pg.click('.asp-pick[data-asp="material"]'); await pg.wait_for_timeout(100)
        above = await pg.evaluate("document.querySelector('.asp-picker').getBoundingClientRect().bottom <= document.querySelector('.asp-pick[data-asp=\"material\"]').getBoundingClientRect().top")
        if not above: fails.append('the scale should open above the badge')
        await pg.click('.asp-picker [data-l="2"]'); await pg.wait_for_timeout(100)
        await pg.click('.asp-pick[data-asp="king"]'); await pg.wait_for_timeout(100)
        xy = await pg.evaluate("[0,-3].map(l=>{ const r = document.querySelector('.asp-picker [data-l=\"'+l+'\"]').getBoundingClientRect(); return [r.x+r.width/2, r.y+r.height/2]; })")
        await pg.mouse.move(*xy[0]); await pg.mouse.down(); await pg.mouse.move(xy[1][0], xy[1][1], steps=8); await pg.mouse.up(); await pg.wait_for_timeout(100)
        await pg.focus('.asp-pick[data-asp="space"]'); await pg.keyboard.press('ArrowUp'); await pg.keyboard.press('ArrowUp'); await pg.keyboard.press('ArrowDown')
        await pg.click('.asp-pick[data-asp="threats"]'); await pg.wait_for_timeout(100)
        await pg.mouse.click(5, 5); await pg.wait_for_timeout(100)
        r = await pg.evaluate("({ asp: st('imbalances').asp, badges: [...document.querySelectorAll('#aspInput .asp-pick')].map(b=>b.textContent).join(' '), open: !!document.querySelector('.asp-picker') })")
        print('gauged:', r)
        if r['asp'] != {'material': 2, 'king': -3, 'space': 1} or r['badges'] != '++ = + = −−− =' or r['open']: fails.append(f'gauging: {r}')
        # 5. The review: your levels first; then one by one the engine's, the score climbing; the buttons last.
        await pg.click('#check'); await pg.wait_for_selector('#aspects', timeout=5000); await pg.wait_for_timeout(150)
        first = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item .asp-badge')].map(b=>b.textContent).join(' | ')"); acc0 = await pg.text_content('#revealAcc')
        print('at first:', first, acc0)
        if first != '++ | = | + | = | −−− | =' or acc0 not in ('—', '0%'): fails.append(f'the review should open on your levels: {first} {acc0}')
        seen = set(); scores = []
        for _ in range(120):
            seen.add(await pg.evaluate("st('imbalances').aspShown || 0"))
            sc = await pg.text_content('#revealAcc')
            if not scores or scores[-1] != sc: scores.append(sc)
            if await pg.evaluate("!!st('imbalances').aspDone"): break
            await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(500)
        print('revealed in steps:', sorted(seen), 'score:', scores)
        if len(seen) < 4: fails.append(f'the imbalances should turn one by one: {sorted(seen)}')
        rows = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item')].map(r=>r.querySelector('.asp-name').textContent+': '+[...r.querySelector('.asp-badge').classList].filter(c=>['w','b','eq'].includes(c))[0]+' '+r.querySelector('.asp-badge').textContent)")
        heads = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-head')].map(h=>h.textContent)")
        print('rows:', rows, heads)
        if [x.split(':')[0] for x in rows] != ['Material', 'Pawns', 'Space', 'Activity', 'King safety', 'Threats']: fails.append(f'rows: {rows}')
        if heads != ['Static', 'Dynamic']: fails.append(f'column titles: {heads}')
        vals = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data; return ASPECTS.map(x=>a[x.key]); })()")
        def badge(v):
            n = sum(abs(v) >= t for t in (0.3, 0.8, 2))
            return 'eq =' if n == 0 else ('w ' + '+'*n if v > 0 else 'b ' + '−'*n)
        if [r.split(': ')[1] for r in rows] != [badge(v) for v in vals]: fails.append(f'badges {rows} vs values {vals}')
        borders = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item .asp-badge')].map(b=>['ok','near','far','bad'].find(c=>b.classList.contains(c)) || '?')")
        lv = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data; return ASPECTS.map(x=>aspectLevel(a[x.key])); })()")
        mine = [2, 0, 1, 0, -3, 0]
        want = ['ok' if m == l else 'near' if abs(m - l) == 1 else 'far' if abs(m - l) == 2 else 'bad' for m, l in zip(mine, lv)]
        print('borders:', borders)
        if borders != want: fails.append(f'borders: {borders}, expected {want}')
        final = await pg.text_content('#revealAcc')
        pts = round(sum(100 / 6 * max(0, 3 - abs(m - l)) / 3 for m, l in zip(mine, lv)))
        nums = [int(x[:-1]) for x in scores if x.endswith('%')]
        if final != f'{pts}%': fails.append(f'score {final}, expected {pts}%')
        if nums != sorted(nums) or not nums or nums[0] != 0: fails.append(f'the score should climb from 0: {scores}')
        rec = await pg.evaluate("[results[results.length-1].a, results[results.length-1].acc]")
        if rec != ['imbalances', pts]: fails.append(f'recorded {rec}')
        if await pg.evaluate("document.querySelector('.actions-row.split').classList.contains('pending')"): fails.append('buttons should be in at the end')
        h2 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        if h1 != h2: fails.append(f'panel height changed: {h1} -> {h2}')
        await pg.set_viewport_size({'width': 360, 'height': 760}); await pg.wait_for_timeout(200)
        cut = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-name')].filter(n=>n.scrollWidth>n.clientWidth).map(n=>n.textContent)")
        await pg.set_viewport_size({'width': 390, 'height': 760})
        if cut: fails.append(f'names cut at 360 px wide: {cut}')
        # 6. Tap an imbalance: its marks on the board; another: that one instead; again: none.
        async def tapped(k):
            await pg.click(f'#aspects .asp-item[data-asp="{k}"]'); await pg.wait_for_timeout(100)
            return await pg.evaluate("({ sel: [...document.querySelectorAll('#aspects .asp-item.sel')].map(e=>e.dataset.asp).join(), nums: document.querySelectorAll('#arrows text').length, marks: document.getElementById('arrows').children.length })")
        r1 = await tapped('activity'); r2 = await tapped('space'); r3 = await tapped('space')
        print('tap:', r1, r2, r3)
        if r1['sel'] != 'activity' or r1['nums'] < 1 or r2['sel'] != 'space' or r2['nums'] != 0 or r3['sel'] != '' or r3['marks'] != 0: fails.append(f'tapping: {r1} {r2} {r3}')
        # 7. Position evaluation: the bar alone, the tactics reminder beside Check; its review shows the
        #    engine's imbalances (no borders, not scored), tappable too.
        await pg.click('#homeBtn'); await pg.wait_for_timeout(200)
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
        await pg.evaluate("""()=>{ const p = pos(); engineEval = fen=>new Promise(res=>setTimeout(()=>res({ lines:[{cp: p.side==='w' ? 250 : -250, mate:null, uci:null}], bestUci:null }), 20)); fenEvalStore = {}; render(); }""")
        prompt = await pg.text_content('#anaPrompt'); note = await pg.text_content('#anaCheckRow .asp-note')
        if prompt != "Drag the bar to show who's better, and by how much." or note != 'Tactics can also shift the evaluation.': fails.append(f'evaluation question: {prompt} / {note}')
        if await pg.query_selector('#aspInput'): fails.append('Position evaluation asks for no imbalances')
        await pg.click('#check'); await pg.wait_for_function("(st('analysis').animT ?? 0) >= 1", timeout=8000); await pg.wait_for_timeout(300)
        r = await pg.evaluate("""(()=>{ const s = st('analysis'), p = pos(); return { acc: document.getElementById('revealAcc').textContent, want: evalAccuracyPct(s.guess, positionInfo(p, fenEval(p.fen)).pct),
            head: document.querySelector('#aspects .asp-head').textContent, lines: [...document.querySelectorAll('#aspects .plan-row:not(.empty)')].map(r=>r.textContent),
            badges: document.querySelectorAll('#aspects .asp-badge').length, rec: results[results.length-1].a, who: p.side==='w' ? 'White' : 'Black' }; })()""")
        print('evaluation review:', r)
        if r['acc'] != f"{r['want']}%" or r['head'] != 'Plan for ' + r['who'] or not 1 <= len(r['lines']) <= 3 or r['badges'] or r['rec'] != 'analysis': fails.append(f'evaluation review: {r}')
        row = await pg.query_selector('#aspects .plan-row.pickable')
        if row:
            k = await row.get_attribute('data-asp'); await row.click(); await pg.wait_for_timeout(100)
            if await pg.evaluate("st('analysis').aspView") != k: fails.append('tapping a plan line should show its imbalance')
        # the plan, from made-up imbalances (White to play)
        plans = await pg.evaluate("""(()=>{ const P = (vals, cp, side)=>planFor({ fen:'4k3/8/8/8/8/8/8/4K3 '+(side||'w')+' - - 0 1', side: side||'w' }, Object.assign({ material:0, pawns:0, space:0, activity:0, king:0, threats:0 }, vals), { cp, mate:null }).lines.map(x=>x.text);
          return { ahead: P({ material:1.5 }, 150), behind: P({ material:-1.5, activity:1 }, 0), king: P({ king:2.5 }, 200), cramped: P({ space:-0.5 }, -30),
                   blackAhead: P({ material:-1.5 }, -150, 'b'), even: P({}, 10), lost: P({ activity:-0.4 }, -400) }; })()""")
        print('plans:', plans)
        if plans['ahead'][0] != 'Trade pieces, not pawns' or plans['behind'][0] != 'Keep pieces on, play actively' \
           or plans['king'][0] != 'Attack the king, open lines' or plans['cramped'] != ['Trade pieces to free yourself'] \
           or plans['blackAhead'][0] != 'Trade pieces, not pawns' or plans['even'] != ['Improve pieces, find a break'] \
           or plans['lost'][0] != 'Avoid trades, complicate': fails.append(f'plans: {plans}')
        # Imbalance reading in your games: only positions whose evaluation is near the imbalances' total
        q = await pg.evaluate("""async t=>{
          const lines = t.split('\\n');   // total ≈ +0.8 for this table's position
          engineAspectsBg = ()=>Promise.resolve(lines);
          const fen = 'r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8';
          myGames.push({ id:'qtest', evals:[{cp:80}, {cp:900}] });
          const near = { key:'own:qtest:1', fen, gameId:'qtest', ply:1 }, far = { key:'own:qtest:2', fen, gameId:'qtest', ply:2 };
          quietOwn(near); quietOwn(far); await new Promise(r=>setTimeout(r, 50));
          const out = [quietOwn(near), quietOwn(far)]; myGames.pop(); return out; }""", TABLE)
        print('own quiet check:', q)
        if q != [True, False]: fails.append(f'own positions quiet check: {q}')
        # what each imbalance marks, on small positions
        marks = await pg.evaluate("""(()=>{ const M = (fen, k)=>{ const m = aspectMarks(fen, k); return {
            c: m.circles.map(x=>x.sq+x.c).sort().join(' '), a: m.arrows.map(x=>x.from+x.to+x.c).sort().join(' '), t: m.tints.length, n: m.nums.map(x=>x.sq+x.n).sort().join(' ') }; };
          return {
            material: M('4k3/8/8/8/8/8/3PP3/1R2K3 w - - 0 1', 'material').c,
            pair: M('4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1', 'material').c,
            pawns: M('4k3/8/8/3p4/8/8/P1P3PP/4K3 w - - 0 1', 'pawns').c,
            threats: M('4k3/8/2n5/3P4/8/8/8/4K3 w - - 0 1', 'threats').a,
            hanging: M('4k3/8/8/3r4/8/8/3Q4/4K3 b - - 0 1', 'threats').a,
            spaceFew: M('4k3/8/8/8/8/8/8/4K3 w - - 0 1', 'space').t,
            knight: M('4k3/8/8/8/8/8/8/1N2K3 w - - 0 1', 'activity').n,
          }; })()""")
        want = {'material': 'b1w d2w e2w', 'pair': 'c1w f1w', 'pawns': 'a2w c2b d5w g2w h2w', 'threats': 'd5c6w', 'hanging': 'd2d5w d5d2b', 'spaceFew': 0, 'knight': 'b13'}
        for k, v in want.items():
            if marks[k] != v: fails.append(f'{k} marks: {marks[k]}, expected {v}')
        # the pool: Position evaluation's positions less the tactical ones
        n = await pg.evaluate("[POOLS.imbalances.length, POOLS.analysis.length, IMBALANCE_SKIP.length, POOLS.imbalances.some(p=>IMBALANCE_SKIP.includes(p.key))]")
        print('pools:', n)
        if n[0] != n[1] - n[2] or n[3] or n[2] < 5: fails.append(f'Imbalance reading pool: {n}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
