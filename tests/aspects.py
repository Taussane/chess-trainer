# Key aspects (Position evaluation review): Stockfish 10's `eval` table, grouped into aspects, and
# shown under the review with a Dynamics row (the search minus the aspects).
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
        # 3. The review: six aspects, a divider, Dynamics = search minus the aspects.
        await pg.click('.card[data-go="analysis"]'); await pg.wait_for_timeout(300)
        await pg.evaluate("""t=>{ const p = pos(); engineAspects = fen=>Promise.resolve(t.split('\\n'));
          engineEval = fen=>new Promise(res=>setTimeout(()=>res({ lines:[{cp: p.side==='w' ? 250 : -250, mate:null, uci:null}], bestUci:null }), 20));
          fenEvalStore = {}; aspectsStore = {}; render(); }""", TABLE)
        note = await pg.evaluate("(()=>{ const n = document.querySelectorAll('#aspInput .asp-note'); return n.length + ' ' + (n[0] ? n[0].textContent + ' ' + getComputedStyle(n[0]).color : ''); })()")
        grey = await pg.evaluate("getComputedStyle(document.querySelector('.hint, .score-label, .asp-head')).color")
        if note != '1 Tactics can also shift the positional evaluation. ' + await pg.evaluate("getComputedStyle(document.querySelector('.asp-head')).color"): fails.append(f'tactics reminder: {note}')
        prompt = await pg.text_content('#anaPrompt')
        if prompt != 'Gauge each positional aspect, then drag the bar to your evaluation.': fails.append(f'prompt: {prompt}')
        # 4. Gauging the aspects before Check: all "=" at first; tap a badge, then a level; slide; arrow keys.
        start = await pg.evaluate("[...document.querySelectorAll('#aspInput .asp-pick')].map(b=>b.textContent).join(' ')")
        if start != '= = = = = =': fails.append(f'aspects should start at =: {start}')
        await pg.click('.asp-pick[data-asp="material"]'); await pg.wait_for_timeout(100)
        above = await pg.evaluate("document.querySelector('.asp-picker').getBoundingClientRect().bottom <= document.querySelector('.asp-pick[data-asp=\"material\"]').getBoundingClientRect().top")
        if not above: fails.append('the scale should open above the badge')
        await pg.click('.asp-picker [data-l="2"]'); await pg.wait_for_timeout(100)
        await pg.click('.asp-pick[data-asp="king"]'); await pg.wait_for_timeout(100)
        xy = await pg.evaluate("[0,-3].map(l=>{ const r = document.querySelector('.asp-picker [data-l=\"'+l+'\"]').getBoundingClientRect(); return [r.x+r.width/2, r.y+r.height/2]; })")
        await pg.mouse.move(*xy[0]); await pg.mouse.down(); await pg.mouse.move(xy[1][0], xy[1][1], steps=8); await pg.mouse.up(); await pg.wait_for_timeout(100)
        await pg.focus('.asp-pick[data-asp="space"]'); await pg.keyboard.press('ArrowUp'); await pg.keyboard.press('ArrowUp'); await pg.keyboard.press('ArrowDown')
        await pg.click('.asp-pick[data-asp="threats"]'); await pg.wait_for_timeout(100)
        await pg.mouse.click(5, 5); await pg.wait_for_timeout(100)   # a tap elsewhere closes the scale
        r = await pg.evaluate("({ asp: st('analysis').asp, badges: [...document.querySelectorAll('#aspInput .asp-pick')].map(b=>b.textContent).join(' '), open: !!document.querySelector('.asp-picker') })")
        print('gauged:', r)
        if r['asp'] != {'material': 2, 'king': -3, 'space': 1} or r['badges'] != '++ = + = −−− =' or r['open']: fails.append(f'gauging: {r}')
        await pg.click('#check'); await pg.wait_for_selector('#aspects', timeout=5000)
        rows = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item')].map(r=>r.querySelector('.asp-name').textContent+': '+r.querySelector('.asp-badge').className.split(' ').pop()+' '+r.querySelector('.asp-badge').textContent)")
        heads = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-head')].map(h=>h.textContent)")
        print('rows:', rows, heads)
        if [x.split(':')[0] for x in rows] != ['Material', 'Pawns', 'Space', 'Activity', 'King safety', 'Threats']: fails.append(f'rows: {rows}')
        if heads != ['Static', 'Dynamic']: fails.append(f'column titles: {heads}')
        vals = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data; return ASPECTS.map(x=>a[x.key]); })()")
        def badge(v):
            n = sum(abs(v) >= t for t in (0.3, 0.8, 2))
            return 'eq =' if n == 0 else ('w ' + '+'*n if v > 0 else 'b ' + '−'*n)
        if rows and [r.split(': ')[1] for r in rows] != [badge(v) for v in vals]: fails.append(f'badges {rows} vs values {vals}')
        yours = await pg.evaluate("[...document.querySelectorAll('#aspects .asp-item')].map(i=>(i.querySelector('.asp-yours')||{}).textContent||'')")
        lv = await pg.evaluate("(()=>{ const a = aspectsStore[pos().fen].data; return ASPECTS.map(x=>aspectLevel(a[x.key])); })()")
        mine = [2, 0, 1, 0, -3, 0]
        want = [('=' if m == 0 else ('+' if m > 0 else '−') * abs(m)) if m != l else '' for m, l in zip(mine, lv)]
        print('yours:', yours)
        if yours != want: fails.append(f'your guesses in the review: {yours}, expected {want}')
        if await pg.query_selector('text=Dynamics') or await pg.query_selector('text=Aspects alone') or await pg.query_selector('text=Decisive move'): fails.append('Dynamics / Aspects alone / Decisive move should be gone')
        if await pg.query_selector('#aspects .asp-note'): fails.append('the tactics reminder belongs to the question, not the review')
        if await pg.query_selector('.recap'): fails.append('the recap sentence should be gone')
        # the panel keeps its height from the question to the review
        await pg.click('#nextPos'); await pg.wait_for_timeout(400)
        h1 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        await pg.click('#check'); await pg.wait_for_selector('#aspects .asp-badge.w, #aspects .asp-badge.b, #aspects .asp-badge.eq', timeout=5000); await pg.wait_for_timeout(1500)
        h2 = await pg.evaluate("document.querySelector('.panel').offsetHeight")
        if h1 != h2: fails.append(f'panel height changed: {h1} -> {h2}')
        await b.close()
    errs = [e for e in errs if 'importScripts' not in e]
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok'); sys.exit(1 if fails else 0)
if __name__=='__main__': asyncio.run(main())
