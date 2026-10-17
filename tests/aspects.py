# Imbalance reading, and the imbalances in Position evaluation's review: Stockfish 10's `eval` table,
# grouped into six imbalances, gauged as signs (−− to ++), revealed one by one, drawn on the board.
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
        # 1. Parsing: Material in points, the rest adding up to Stockfish's own total less its material lines.
        r = await pg.evaluate("([t, f])=>{ const a = parseAspects(t.split('\\n').concat(['Total evaluation: 0.88 (white side)']), f); return a && {a, sum: Object.values(a).reduce((x,y)=>x+y,0)}; }", [TABLE, FEN])
        print('parsed:', r and {k: round(v, 2) for k, v in r['a'].items()}, 'sum', r and round(r['sum'], 2))
        # Material is counted in points (White a pawn up: 1); the other five keep Stockfish's own figures, which
        # add up to its total less its Material and Imbalance lines (about −0.15 here)
        if not r or r['a']['material'] != 1 or abs(r['sum'] - 1 + 0.15) > 0.2: fails.append(f'aspects do not add up to the total: {r}')
        if r and not 0.6 < r['a']['material'] < 1.2: fails.append('White is a pawn up: material should be about +0.9')
        n = await pg.evaluate("parseAspects(['Total evaluation: none (in check)'], 'k7/8/8/8/8/8/8/K7 w - - 0 1')")
        if n is not None: fails.append('in check should give no aspects')
        # 2. The table now comes from the JavaScript port of Stockfish's evaluation: the same as the engine's.
        r = await pg.evaluate("""([t, fen])=>{ const a = parseAspects(t.split('\\n'), fen), b = parseAspects(sfTableLines(fen), fen);
          return ASPECTS.map(x=>[x.key, +a[x.key].toFixed(3), +b[x.key].toFixed(3)]); }""", [TABLE, FEN])
        if any(abs(x[1] - x[2]) > 0.006 for x in r): fails.append(f'port table differs from the engine: {r}')
        await pg.evaluate("sfWorker = null")
        # 3. Imbalance reading: no bar; the prompt; every imbalance "=" at first.
        await pg.click('.card[data-go="imbalances"]'); await pg.wait_for_timeout(300)
        # (all six criteria in play, whatever position comes up: Space counted)
        await pg.evaluate("""t=>{ window._spaceCounts = spaceCounts; spaceCounts = ()=>true; engineAspects = fen=>Promise.resolve(t.split('\\n')); aspectsStore = {}; render(); }""", TABLE)
        prompt = await pg.text_content('#imbPrompt')
        if prompt != 'Gauge each positional imbalance.': fails.append(f'prompt: {prompt}')
        if await pg.query_selector('#evalBar'): fails.append('Imbalance reading has no evaluation bar')
        start = await pg.evaluate("[...document.querySelectorAll('#aspInput .asp-pick')].map(b=>b.textContent).join(' ')")
        if start != '= = = = = =': fails.append(f'imbalances should start at =: {start}')
        h1 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        n1 = await pg.evaluate("(()=>{ const p = document.querySelector('.panel').getBoundingClientRect().top; return [...document.querySelectorAll('.panel .layer:not(.ghost) .asp-name')].map(n=>Math.round(n.getBoundingClientRect().top - p)); })()")
        # 4. Gauging: tap a badge, then a level (the scale opens above it); slide; arrow keys; a tap elsewhere closes it.
        await pg.click('.asp-pick[data-asp="material"]'); await pg.wait_for_timeout(100)
        above = await pg.evaluate("document.querySelector('.asp-picker').getBoundingClientRect().bottom <= document.querySelector('.asp-pick[data-asp=\"material\"]').getBoundingClientRect().top")
        if not above: fails.append('the scale should open above the badge')
        await pg.click('.asp-picker [data-l="2"]'); await pg.wait_for_timeout(100)
        await pg.click('.asp-pick[data-asp="king"]'); await pg.wait_for_timeout(100)
        xy = await pg.evaluate("[0,-2].map(l=>{ const r = document.querySelector('.asp-picker [data-l=\"'+l+'\"]').getBoundingClientRect(); return [r.x+r.width/2, r.y+r.height/2]; })")
        await pg.mouse.move(*xy[0]); await pg.mouse.down(); await pg.mouse.move(xy[1][0], xy[1][1], steps=8); await pg.mouse.up(); await pg.wait_for_timeout(100)
        await pg.focus('.asp-pick[data-asp="space"]'); await pg.keyboard.press('ArrowUp'); await pg.keyboard.press('ArrowUp'); await pg.keyboard.press('ArrowDown')
        await pg.click('.asp-pick[data-asp="threats"]'); await pg.wait_for_timeout(100)
        if not await pg.evaluate("document.querySelector('.asp-pick[data-asp=\"threats\"]').classList.contains('editing')"): fails.append('the badge being set should be highlighted')
        await pg.mouse.click(5, 5); await pg.wait_for_timeout(100)
        r = await pg.evaluate("({ asp: st('imbalances').asp, badges: [...document.querySelectorAll('#aspInput .asp-pick')].map(b=>b.textContent).join(' '), open: !!document.querySelector('.asp-picker') })")
        print('gauged:', r)
        if await pg.query_selector('.asp-pick.editing'): fails.append('highlight should go when the scale closes')
        # A choice drawn over another row: picking it doesn't open that row's scale.
        await pg.click('.asp-pick[data-asp="pawns"]'); await pg.wait_for_timeout(100)
        await pg.click('.asp-picker [data-l="0"]'); await pg.wait_for_timeout(100)
        if await pg.query_selector('.asp-picker'): fails.append('a choice should not click through to the badge under it')
        if r['asp'] != {'material': 2, 'king': -2, 'space': 1} or r['badges'] != '++ = + = −− =' or r['open']: fails.append(f'gauging: {r}')
        # 5. The review: your levels first; then one by one the engine's, the score climbing; the buttons last.
        await pg.click('#check'); await pg.wait_for_selector('#aspects', timeout=5000); await pg.wait_for_timeout(150)
        first = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item .asp-badge')].map(b=>b.textContent).join(' | ')"); acc0 = await pg.text_content('#revealAcc')
        print('at first:', first, acc0)
        if first != '++ | = | + | = | −− | =' or acc0 not in ('—', '0%'): fails.append(f'the review should open on your levels: {first} {acc0}')
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
        if [x.split(':')[0] for x in rows] != ['Material', 'Pawns', 'Space', 'Activity', 'King safety', 'Other threats']: fails.append(f'rows: {rows}')
        if heads != ['Static', 'Dynamic']: fails.append(f'column titles: {heads}')
        vals = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data; return ASPECTS.map(x=>a[x.key]); })()")
        LEVELS = await pg.evaluate("ASPECTS.map(x=>x.levels)")   # the app's own thresholds
        def badge(v, t):
            n = sum(abs(v) >= x for x in t)
            return 'eq =' if n == 0 else ('w ' + '+'*n if v > 0 else 'b ' + '−'*n)
        # the engine's level, or your own where it earns the green (80% or more of the share)
        kept = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data, g = st('imbalances').asp; return ASPECTS.map(x=>aspectCredit(a[x.key], g[x.key]||0, x.key) >= 0.8 ? (g[x.key]||0) : null); })()")
        def mine(n): return 'eq =' if n == 0 else ('w ' + '+'*n if n > 0 else 'b ' + '−'*-n)
        want = [badge(v, t) if k is None else mine(k) for v, t, k in zip(vals, LEVELS, kept)]
        if [r.split(': ')[1] for r in rows] != want: fails.append(f'badges {rows} vs values {vals}')
        borders = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item .asp-badge')].map(b=>['ok','near','far','bad'].find(c=>b.classList.contains(c)) || '?')")
        lv = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data; return ASPECTS.map(x=>aspectLevel(a[x.key], x.key)); })()")
        mine = [2, 0, 1, 0, -2, 0]
        POINTS = await pg.evaluate("ASPECTS.map(x=>!!x.points)")   # counted in points (Material, Pawns): exact levels
        def credit(v, g, t, pts=False):   # the app's aspectCredit: a level off scores more near the line between the two
            n = sum(abs(v) >= x for x in t); lv = n if v >= 0 else -n
            if g == lv: return 1
            if abs(g - lv) > 1 or pts: return 0
            e = [float('-inf'), -t[1], -t[0], t[0], t[1], float('inf')]; lo, hi = e[g + 2], e[g + 3]
            d, th = (lo - v, abs(lo)) if v < lo else (v - hi, abs(hi))
            d = max(0, d)
            return max(0, 1 - d / (0.5 * th))
        cr = [credit(v, m, t, q) for v, m, t, q in zip(vals, mine, LEVELS, POINTS)]
        want = ['ok' if c >= 0.8 else 'near' if c > 0 else 'bad' for c in cr]
        print('borders:', borders)
        if borders != want: fails.append(f'borders: {borders}, expected {want}')
        final = await pg.text_content('#revealAcc')
        pts = round(sum(100 / 6 * c for c in cr))
        nums = [int(x[:-1]) for x in scores if x.endswith('%')]
        if final != f'{pts}%': fails.append(f'score {final}, expected {pts}%')
        if nums != sorted(nums) or not nums or nums[0] != 0: fails.append(f'the score should climb from 0: {scores}')
        rec = await pg.evaluate("[results[results.length-1].a, results[results.length-1].acc]")
        if rec != ['imbalances', pts]: fails.append(f'recorded {rec}')
        if await pg.evaluate("document.querySelector('.actions-row.split').classList.contains('pending')"): fails.append('buttons should be in at the end')
        h2 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        if h1 != h2: fails.append(f'panel height changed: {h1} -> {h2}')
        n2 = await pg.evaluate("(()=>{ const p = document.querySelector('.panel').getBoundingClientRect().top; return [...document.querySelectorAll('.panel .layer:not(.ghost) .asp-name')].map(n=>Math.round(n.getBoundingClientRect().top - p)); })()")
        if n1 != n2: fails.append(f'imbalances should stay in place: {n1} -> {n2}')
        await pg.set_viewport_size({'width': 360, 'height': 760}); await pg.wait_for_timeout(200)
        cut = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-name')].filter(n=>n.scrollWidth>n.clientWidth).map(n=>n.textContent)")
        await pg.set_viewport_size({'width': 390, 'height': 760})
        if cut: fails.append(f'names cut at 360 px wide: {cut}')
        # 6. Tap an imbalance: its marks on the board; another: that one instead; again: none.
        async def tapped(k):
            await pg.click(f'#aspects .asp-item[data-asp="{k}"]'); await pg.wait_for_timeout(100)
            return await pg.evaluate("({ sel: [...document.querySelectorAll('#aspects .asp-item.sel')].map(e=>e.dataset.asp).join(), nums: document.querySelectorAll('#arrows text').length, marks: document.getElementById('arrows').children.length })")
        # only imbalances with something to draw are tappable (and underlined)
        pk = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item')].map(e=>[e.dataset.asp, e.classList.contains('pickable'), hasMarks(pos().fen, e.dataset.asp)])")
        if any(x[1] != x[2] for x in pk): fails.append(f'pickable should match marks: {pk}')
        other_k = next(x[0] for x in pk if x[1] and x[0] != 'activity')
        r1 = await tapped('activity'); r2 = await tapped(other_k); r3 = await tapped(other_k)
        print('tap:', r1, r2, r3, other_k)
        if r1['sel'] != 'activity' or r1['nums'] < 1 or r2['sel'] != other_k or r3['sel'] != '' or r3['marks'] != 0: fails.append(f'tapping: {r1} {r2} {r3}')
        # 7. Position evaluation: the bar alone, the tactics reminder beside Check; its review shows the
        #    engine's imbalances (no borders, not scored), tappable too.
        await pg.click('#homeBtn'); await pg.wait_for_timeout(200)
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
        await pg.evaluate("""()=>{ const p = pos(); engineEval = fen=>new Promise(res=>setTimeout(()=>res({ lines:[{cp: p.side==='w' ? 250 : -250, mate:null, uci:null}], bestUci:null }), 20)); fenEvalStore = {}; render(); }""")
        prompt = await pg.text_content('#anaPrompt'); note = await pg.query_selector('#anaCheckRow .asp-note')
        if prompt != "Drag the evaluation bar to where you think it sits." or note: fails.append(f'evaluation question: {prompt} / {note}')
        if await pg.query_selector('#aspInput'): fails.append('Position evaluation asks for no imbalances')
        e1 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        await pg.click('#check'); await pg.wait_for_function("(st('analysis').animT ?? 0) >= 1", timeout=8000); await pg.wait_for_timeout(300)
        e2 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        if e1 != e2: fails.append(f'Position evaluation panel height changed: {e1} -> {e2}')
        r = await pg.evaluate("""(()=>{ const s = st('analysis'), p = pos(); return { acc: document.getElementById('revealAcc').textContent, want: evalAccuracyPct(s.guess, positionInfo(p, fenEval(p.fen)).pct),
            head: document.querySelector('#aspects .asp-head').textContent, lines: [...document.querySelectorAll('#aspects .plan-row:not(.plan-blank)')].map(r=>r.textContent),
            badges: document.querySelectorAll('#aspects .asp-badge').length, rec: results[results.length-1].a, who: p.side==='w' ? 'White' : 'Black' }; })()""")
        print('evaluation review:', r)
        if r['acc'] != f"{r['want']}%" or r['head'] != 'Possible plans for ' + r['who'] or not 1 <= len(r['lines']) <= 3 or r['badges'] or r['rec'] != 'analysis': fails.append(f'evaluation review: {r}')
        row = await pg.query_selector('#aspects .plan-row.pickable')
        if row:
            k = await row.get_attribute('data-asp'); await row.click(); await pg.wait_for_timeout(100)
            if await pg.evaluate("st('analysis').aspView") != k: fails.append('tapping a plan line should show its imbalance')
            if await pg.evaluate("getComputedStyle(document.querySelector('#aspects .plan-row.sel .plan-sit')).textDecorationLine") != 'none': fails.append('the selected plan line should not be underlined')
        # the plan, from made-up imbalances (White to play)
        plans = await pg.evaluate("""(()=>{ const P = (vals, cp, side)=>planFor({ fen:'4k3/8/8/8/8/8/8/4K3 '+(side||'w')+' - - 0 1', side: side||'w' }, Object.assign({ material:0, pawns:0, space:0, activity:0, king:0, threats:0 }, vals), { cp, mate:null }).lines.map(x=>x.plan);
          const Q = (vals, side)=>planFor({ fen:'4k2r/8/8/8/8/8/P7/R3K3 '+side+' - - 0 1', side }, Object.assign({ material:0, pawns:0, space:0, activity:0, king:0, threats:0 }, vals), { cp:0, mate:null }).lines.map(x=>x.situation+': '+x.plan);
          return { passed: Q({ pawns:0.5 }, 'w'), blockade: Q({ pawns:0.5 }, 'b'),
                   ahead: P({ material:1.5 }, 150), behind: P({ material:-1.5, activity:1 }, 0), king: P({ king:2.5 }, 200), cramped: P({ space:-4 }, -30),
                   blackAhead: P({ material:-1.5 }, -150, 'b'), even: P({}, 10), lost: P({ activity:-0.4 }, -400), conflict: P({ material:1.5, space:4 }, 150) }; })()""")
        print('plans:', plans)
        if plans['ahead'][0] != 'Trade pieces' or plans['behind'][0] != 'Avoid trades, attack' \
           or plans['king'][0] != 'Open lines to it' or plans['cramped'] != ['Trade to breathe'] \
           or plans['blackAhead'][0] != 'Trade pieces' or plans['even'] != ['Find a pawn break'] \
           or 'Simplify, stay safe' in plans['king'] or plans['conflict'] != ['Trade pieces'] \
           or plans['lost'][0] != 'Complicate' or plans['passed'] != ['Passed pawn: Push it'] or plans['blockade'] != ['Enemy passed pawn: Blockade it']: fails.append(f'plans: {plans}')
        # Imbalance reading in your games: only positions whose evaluation is near the imbalances' total
        q = await pg.evaluate("""async t=>{
          const lines = t.split('\\n');   // total ≈ +0.8 for this table's position
          engineAspectsBg = ()=>Promise.resolve(lines);
          const fen = 'r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8';
          myGames.push({ id:'qtest', evals:[{cp:80}, {cp:900}] });
          const near = { key:'own:qtest:1', fen, gameId:'qtest', ply:1 }, far = { key:'own:qtest:2', fen, gameId:'qtest', ply:2 };
          quietOwn(near); quietOwn(far); await new Promise(r=>setTimeout(r, 400));
          const out = [quietOwn(near), quietOwn(far)]; myGames.pop(); return out; }""", TABLE)
        print('own quiet check:', q)
        if q != [True, False]: fails.append(f'own positions quiet check: {q}')
        # Material, on the "Material marks" test position: per piece type, the extra ones; the bishop pair labelled.
        mm = await pg.evaluate("(()=>{ const m = aspectMarks(TEST_POSITIONS.find(p=>p.title==='Material marks').fen, 'material'); return [m.circles.map(c=>c.sq+c.c).sort().join(' '), m.labels.map(l=>l.sq+l.c+':'+l.text).sort().join(' ')]; })()")
        print('material marks:', mm)
        if mm != ['a1w c3w d5w d8b e3w f6b', 'c4w:Pair e3w:Pair']: fails.append(f'material marks: {mm}')
        pm = await pg.evaluate("(()=>{ const m = aspectMarks(TEST_POSITIONS.find(p=>p.title==='Pawn marks').fen, 'pawns'); return [m.labels.map(l=>l.sq+l.c+':'+l.text).sort().join(' '), m.arrows.map(a=>a.from+a.to+a.c).join(' ')]; })()")
        print('pawn marks:', pm)
        if pm != ['a4w:Isolated c3w:Doubled c7b:Backward d5w:Connected e5w:Passed h5b:Passed', 'e2f3w']: fails.append(f'pawn marks: {pm}')
        sm = await pg.evaluate("(()=>{ const m = aspectMarks(TEST_POSITIONS.find(p=>p.title==='Space marks').fen, 'space'); return [m.circles.map(c=>c.sq+c.c).sort().join(' '), m.tints.length, m.labels.map(l=>l.sq+':'+l.text).sort().join(' '), m.arrows.map(a=>a.from+a.to+a.c).sort().join(' ')]; })()")
        print('space marks:', sm)
        if sm != ['c2w c3w c7b d2w d3w d7b e2w e3w e7b', 0, '', 'c5d4b d5c6w d5e6w e5d4b']: fails.append(f'space marks: {sm}')
        am = await pg.evaluate("(()=>{ const m = aspectMarks(TEST_POSITIONS.find(p=>p.title==='Activity marks').fen, 'activity'); return m.labels.map(l=>l.sq+l.c+':'+l.text).sort().join(' '); })()")
        print('activity marks:', am)
        un = await pg.evaluate("['r3k2r/pb1n1p2/2p1pq1p/1p6/P1pP4/2P2N2/4BPPP/R2Q1RK1 w kq - 1 14', 'r3k2r/pb1n1p2/2p1pq1p/1p6/P1pP4/2P2N2/4BPPP/R2Q1RK1 w - - 1 14', 'r3k2r/pb1n1p2/2p1pq1p/1p6/P1pP4/2P2N2/4BPPP/R2QK2R w - - 1 14'].map(f=>aspectMarks(f, 'king').labels.filter(l=>l.text==='Uncastled').map(l=>l.sq+l.c).join(' '))")
        if un != ['', 'e8w', '']: fails.append(f'uncastled king (King safety; not while it can castle, nor when both kings are): {un}')
        # one label per piece: Hanging over Pinned (Threats), Pinned over Outpost (Activity)
        one = await pg.evaluate("[['r3r2k/pp3pbp/n5q1/8/5Bb1/PN2N1R1/1PPQ4/2K4R b - - 4 26','threats'], ['6k1/2p5/8/p2PP2p/2PR2bq/6p1/PP4P1/5KQ1 w - - 5 38','activity']].map(([f,k])=>aspectMarks(f, k).labels.filter(l=>l.sq==='g4').map(l=>l.text).join(' '))")
        if one != ['Hanging', 'Pinned']: fails.append(f'one label per piece: {one}')
        # Pawns in points: Black's a6 isolated (−0.5) and d5 passed on its 4th rank (+1): −0.5 for White; each
        # counted pawn's points in its corner, Passed and Connected with their rank, each king its side's total
        isl = await pg.evaluate("""(()=>{ const f = 'r4rk1/4bppp/p3bn2/3p4/N7/3BB3/PP3PPP/R3R1K1 w - - 3 16', g = '2r3k1/2p3p1/1p6/3PP2p/P7/2P2P2/2P1PP2/3R2K1 w - - 0 30';
          return [adaptAspects(parseAspects(sfTableLines(f), f), f).pawns, aspectMarks(f, 'pawns').nums.map(n=>n.sq+n.c+n.n).sort().join(' '), aspectMarks(g, 'pawns').nums.map(n=>n.sq+n.c+n.n).sort().join(' ')]; })()""")
        if isl != [-0.5, 'a6b−0.5 d5b1 d5b4th g8b+0.5', 'a4w−0.5 c3w−0.5 c7b−0.5 d5w1 d5w5th e5w2 e5w5th g1w+2 g8b+0.5 h5b1 h5b4th']: fails.append(f'pawn points: {isl}')
        # our adaptations, on one position: Activity loses the kings' middlegame squares and the pieces' distance
        # to their king (both to King safety) and the trapped rook while castling is possible; King safety also
        # takes the shelter where the king stands and drops the attacks on the king's wing; threats by the side
        # to move count in full, the other side's at half, without weak pawns exposed on their file
        ad = await pg.evaluate("""(()=>{ const f = 'r3k2r/pb1n1p2/2p1pq1p/1p6/P1pP4/2P2N2/4BPPP/R2Q1RK1 w kq - 1 14';
          const raw = parseAspects(sfTableLines(f), f), a = adaptAspects(parseAspects(sfTableLines(f), f), f), ev = sfEvalOf(f);
          const pw = ([mg, eg])=>(mg*ev.phase + eg*(128 - ev.phase)) / 128 / SF_PAWN_EG;
          const sum = pred=>ev.features.filter(pred).reduce((t, x)=>t + pw(x.v) * (x.c===0 ? 1 : -1), 0);
          const sh = c=>{ const x = ev.features.find(x=>x.term==='king' && x.kind==='shelter' && x.c===c);
            return x.own.safety - x.v[0] + x.own.files.filter(fl=>fl.ourRank >= 3).reduce((t, fl)=>t + fl.empty - fl.shelter, 0); };
          const ks = pw([ev.trace.kingSquares[0], 0]), far = sum(x=>x.kind==='kingProtector'), trop = sum(x=>x.kind==='tropism'), trapped = sum(x=>['trappedRook','bishopPawns','minorBehindPawn','longDiagonal','kingProtector'].includes(x.kind)) + sum(x=>x.kind==='weakQueen' && queenExposedBy(f, sqName(x.sq)));
          const T = ev.trace.threats.map(x=>x.slice()); const bm = boardMap(f), am = attackMaps(bm), K = { byMinor:'nb', byRook:'r', safePawn:'p', byKing:'k', hanging:'pnbrqk' }, lc = c=>{ const pz = f.split(' '); pz[1] = c; pz[3] = '-'; return new Set(new Chess(pz.join(' ')).moves({ verbose: true }).filter(x=>x.captured).map(x=>x.from + x.to)); };
          const trades = x=>{ if(!K[x.kind]) return false; const c = x.c ? 'b' : 'w', L = lc(c), ts = x.kind==='byKing' ? bbSquares(x.squares) : [sqName(x.sq)];
            return !ts.some(t=>(am[c][t] || []).some(a=>K[x.kind].includes(bm[a].t) && L.has(a + t) && see(bm, am, a, t) > 0)); };
          ev.features.filter(x=>['weakUnopposed', 'byRank', 'restricted', 'knightOnQueen', 'sliderOnQueen'].includes(x.kind) || trades(x)).forEach(x=>{ T[x.c][0] -= x.v[0]; T[x.c][1] -= x.v[1]; });
          return [+(a.activity - (raw.activity - ks - trapped - pw(ev.trace.pieceSquares))).toFixed(4), +(a.king - (raw.king + ks + pw([sh(0) - sh(1), 0]) - trop - sum(x=>x.kind==='pawnDistance'))).toFixed(4),
                  +(a.threats - (pw(T[0]) - 0.5*pw(T[1]))).toFixed(4), +ks.toFixed(2), +far.toFixed(3), +trop.toFixed(3)]; })()""")
        print('adaptations:', ad)
        if ad[0] != 0 or ad[1] != 0 or ad[2] != 0 or ad[3] <= 0.3 or ad[5] == 0: fails.append(f'adaptations: {ad}')
        kg = await pg.evaluate("[kingSquareGain(boardMap('r1b1n1k1/pp3ppp/8/8/8/4K3/PP3PPP/R1B1N3 w - - 0 1'), 'e3', 'w'), kingSquareGain(boardMap('r2qr1k1/pp3ppp/8/8/8/4K3/PP3PPP/R2QR3 w - - 0 1'), 'e3', 'w')].map(x=>Math.round(x*100)/100)")
        print('king square gain (Stockfish: +0.38 with R+B+N each, -0.27 with Q+R+R each):', kg)
        if not (0.33 <= kg[0] <= 0.43 and -0.32 <= kg[1] <= -0.22): fails.append(f'king square gain: {kg}')
        if am != 'd5w:Outpost d6w:Outpost e3w:Central e8b:Half-open f1w:Open g5b:Outpost': fails.append(f'activity marks: {am}')
        ad = await pg.evaluate("(()=>{ const d = activityDetail(TEST_POSITIONS.find(p=>p.title==='Activity marks').fen, 'd5'); return [d.circles.map(c=>c.sq).sort().join(' '), d.arrows.map(a=>a.from+a.to).sort().join(' '), d.nums[0].n]; })()")
        print('activity detail, knight d5:', ad)
        if ad != ['b6 c3 c7 e7 f4', 'c5b4 g7f6', 5]: fails.append(f'activity detail: {ad}')
        di = await pg.evaluate("aspectMarks('4k3/p7/3p4/8/8/2P5/2P5/4K3 w - - 0 1', 'pawns').labels.map(l=>l.sq+':'+l.text).sort().join(' ')")
        if di != 'a7:Passed c2:Isolated c3:Doubled d6:Isolated': fails.append(f'doubled isolated pair: {di}')
        # Space left out when few pieces remain: scored over the other five, greyed in the question
        await pg.evaluate("void (spaceCounts = window._spaceCounts)")
        so = await pg.evaluate("""(()=>{ const v = { material:0, pawns:0, space:0.5, activity:0, king:0, threats:0 }; Object.defineProperty(v, 'off', { value:['space'] });
          return [Math.round(imbalanceScore(v, { space:2 }, 6)), Math.round(imbalanceScore(v, { material:2 }, 6)), spaceCounts('r1bq1rk1/pp2npbp/3p1np1/2pPp3/2P1P3/2N2N2/PP2BPPP/R1BQ1RK1 w - - 0 9'), spaceCounts(TEST_POSITIONS.find(p=>p.title==='Activity marks').fen)]; })()""")
        print('space left out:', so)
        if so != [100, 80, True, False]: fails.append(f'space left out: {so}')
        # a level off near a threshold (King safety, t where + starts): all of it at the line, fading to nothing
        # at half t away; two levels off: nothing
        ac = await pg.evaluate("(()=>{ const t = ASPECTS.find(x=>x.key==='king').levels[0]; return [[1,1],[0.85,1],[0.6,1],[0.2,1],[1.1,0],[1.3,0],[1.8,0],[0.98,2],[1,0]].map(([v,g])=>+aspectCredit(v*t, g, 'king').toFixed(2)); })()")
        if ac != [1, 0.7, 0.2, 0, 0.8, 0.4, 0, 0, 1]: fails.append(f'credit near a threshold: {ac}')
        # an ending Stockfish rates on its own (all-zero table): only Material (in points: the queen's 9), the rest left out
        sp = await pg.evaluate("""(()=>{ const z = ['Material','Imbalance','Initiative','Pawns','Knights','Bishops','Rooks','Queens','Mobility','King safety','Threats','Passed','Space'].map(k=>`  ${k} |  0.00  0.00 |  0.00  0.00 |  0.00  0.00`).concat(['Total evaluation: 61.20 (white side)']);
          const v = parseAspects(z, '7k/8/5K2/8/8/8/8/6Q1 w - - 0 60'); return [Math.round(v.material), v.activity, v.off.join(' '), !!v.special]; })()""")
        print('special ending:', sp)
        if sp != [9, 0, 'pawns space activity king threats', True]: fails.append(f'special ending: {sp}')
        km = await pg.evaluate("(()=>{ const m = aspectMarks(TEST_POSITIONS.find(p=>p.title==='King safety marks').fen, 'king'); return [m.labels.map(l=>l.sq+':'+l.text).sort().join(' '), m.arrows.filter(a=>!a.outline).map(a=>a.from+a.to+a.c).sort().join(' '), m.arrows.filter(a=>a.outline).map(a=>a.from+a.to).join(' '), m.zones.map(z=>z.a+z.b).join(' '), m.circles.filter(c=>c.sq==='e3'||c.sq==='a5').length]; })()")
        print('king marks:', km)
        # mates found by the short search: any mate in King safety (++), Other threats untouched
        mt = await pg.evaluate("""(()=>{ const V = ()=>{ const v = { material:0, pawns:0, space:0, activity:0, king:0, threats:0 }; Object.defineProperty(v, 'off', { value:[] }); return v; };
          const a = applyMate(V(), { lines:[{ mate:1, uci:'d1d8' }] }, '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 30'), b = applyMate(V(), { lines:[{ mate:3, uci:'d1d8' }] }, '8/8/8/8/8/8/8/8 b - - 0 1'), c = applyMate(V(), { lines:[{ mate:-2, uci:'a1a2' }] }, '8/8/8/8/8/8/8/8 w - - 0 1');
          return [a.king, a.threats, a.mate.uci, b.king, b.threats, c.king, c.threats, c.mate.uci]; })()""")
        if mt != [9, 0, 'd1d8', -9, 0, -9, 0, None]: fails.append(f'mates: {mt}')
        # a pawn push attacking a piece; not while the push is illegal (the side to move in check): not counted then
        push = await pg.evaluate("""(()=>{ const chk = TEST_POSITIONS.find(p=>p.title==='White in check').fen, free = 'rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 3 5';
          const A = f=>aspectMarks(f, 'threats').arrows.map(a=>a.from+a.to+a.c).join(' '), L = f=>aspectLevel(adaptAspects(parseAspects(sfTableLines(f), f), f).threats, 'threats');
          const bc = TEST_POSITIONS.find(p=>p.title==='Black in check').fen;   // c6 blocks the check (and hits Bb5), a6 can't be played
          return [A(free).includes('a2a3w'), A(chk).includes('a2a3w'), L(chk), A(bc).includes('c7c6b'), A(bc).includes('a7a6b')]; })()""")
        if push != [True, False, 0, True, False]: fails.append(f'pawn push threats (legal only for the side to move): {push}')
        if km != ['b2:Shelter c2:Shelter c3:Storm f7:Shelter g6:Storm g7:Shelter h6:Shelter', 'a5c3b c6c3b e4g6w g5f7w', 'd1d8', 'b1d3 f6h8', 0]: fails.append(f'king marks: {km}')
        cs = await pg.evaluate("aspectMarks(TEST_POSITIONS.find(p=>p.title==='Castling').fen, 'king').arrows.filter(a=>a.from==='e1'||a.from==='e8').map(a=>a.from+a.to+(a.dash?'-':'')).sort().join(' ')")
        if cs != 'e1g1': fails.append(f'castling arrows (only O-O is possible now): {cs}')
        np = await pg.evaluate("aspectMarks('4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1', 'material').labels.map(l=>l.sq+':'+l.text).sort().join(' ')")
        if np != 'c1:Pair f1:Pair': fails.append(f'bishop pair against no bishop: {np}')
        both = await pg.evaluate("aspectMarks('2b1k1b1/8/8/8/8/8/8/2B1KB2 w - - 0 1', 'material').labels.length")
        if both: fails.append('no bishop pair label when both sides have the pair')
        # what each imbalance marks, on small positions
        marks = await pg.evaluate("""(()=>{ const M = (fen, k)=>{ const m = aspectMarks(fen, k); return {
            c: m.circles.map(x=>x.sq+x.c).sort().join(' '), a: m.arrows.map(x=>x.from+x.to+x.c+(x.dash ? '-' : '')).sort().join(' '), t: m.tints.length, n: m.nums.map(x=>x.sq+x.n).sort().join(' ') }; };
          return {
            material: M('4k3/8/8/8/8/8/3PP3/1R2K3 w - - 0 1', 'material').c,
            pair: M('4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1', 'material').c,
            pawns: M('4k3/8/8/3p4/8/8/P1P3PP/4K3 w - - 0 1', 'pawns').c,
            threats: M('4k3/8/2n5/3P4/8/8/8/4K3 w - - 0 1', 'threats').a,
            hanging: M('4k3/7q/8/3r4/8/8/3Q4/4K1R1 b - - 0 1', 'threats').a,
            fork: M('4k3/8/2n1b3/8/2PP4/8/8/4K3 w - - 0 1', 'threats'),
            pin: M('8/4k3/5n2/6B1/4P3/8/8/4K3 w - - 0 1', 'threats'),
            queenFork: M('8/2q1k3/8/8/8/2N5/1Q6/4K3 w - - 0 1', 'threats'),
            guarded: M('4k3/1p6/2n5/1B6/8/8/8/4K3 w - - 0 1', 'threats').a,
            spaceFew: M('4k3/8/8/8/8/8/8/4K3 w - - 0 1', 'space').t,
            knight: M('4k3/8/8/8/8/8/8/1N2K3 w - - 0 1', 'activity').n,
          }; })()""")
        want = {'material': 'b1w d2w e2w', 'pair': 'c1w f1w', 'pawns': 'a2w c2w d5b g2w h2w', 'threats': 'd5c6w', 'hanging': 'd2d5w d5d2b', 'guarded': '', 'spaceFew': 0, 'knight': 'b13'}
        for k, v in want.items():
            if marks[k] != v: fails.append(f'{k} marks: {marks[k]}, expected {v}')
        # Threats: a pawn fork, a pawn hitting a pinned knight, a knight forking queen and king (the move's arrow, no rings)
        for k, a, c in [('fork', 'c6d4b d4d5w e6c4b', 'c4b d4b'), ('pin', 'e4e5w', 'f6w'), ('queenFork', 'c3d5w', '')]:
            if marks[k]['a'] != a or marks[k]['c'] != c: fails.append(f'{k} threats: {marks[k]}')
        # the pool: Position evaluation's positions less the tactical ones; neither has a castling right
        # lost with king and rook still on their first squares
        n = await pg.evaluate("[POOLS.imbalances.length, POOLS.analysis.length, POOLS.analysis.filter(p=>IMBALANCE_SKIP.includes(p.key)).length, POOLS.imbalances.some(p=>IMBALANCE_SKIP.includes(p.key)), POOLS.analysis.some(p=>hiddenCastlingLoss(p.fen)), ['r3k2r/8/8/8/8/8/8/R3K2R w Kkq - 0 1', 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1', 'r4rk1/8/8/8/8/8/8/R3K3 w Q - 0 1'].map(hiddenCastlingLoss)]")
        print('pools:', n)
        if n[0] != n[1] - n[2] or n[3] or n[2] < 5 or n[4] or n[5] != [True, False, False]: fails.append(f'Imbalance reading pool: {n}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
