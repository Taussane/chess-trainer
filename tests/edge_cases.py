# Edge cases: opens every test position in Candidate moves and Final choice (fake engine), enters
# special moves by tapping squares (en passant, castling, promotion via the piece picker), checks
# the review, and saves screenshots to tests/shots/.
# Needs: pip install playwright (with a Chromium browser).
import asyncio, pathlib, sys
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT/'app'/'index.html').read_text()
CHESS = (ROOT/'vendor'/'chess.js'/'chess.js').read_text()
SHOTS = ROOT/'tests'/'shots'; SHOTS.mkdir(exist_ok=True)
# Fake engine: the side to move's legal moves, best first in chess.js order, but the game move
# and promotions to a knight are always included, so every special move gets graded.
FAKE = """engineEval = (fen, sm)=>new Promise(res=>{ setTimeout(()=>{ const g=new Chess(fen);
  const all=g.moves({verbose:true}).map(m=>m.from+m.to+(m.promotion||''));
  const ms=sm?sm.split(' '):all.slice(0,5);
  res({lines:ms.map((u,i)=>({uci:u,cp:120-i*60,mate:null})), bestUci:ms[0]}); }, 30); });
  fenEvalStore={}; poolEvalStore={}; engineErrorBanner=()=>''; failEngine=()=>{}; sfState='ready'; render();"""
# Moves to enter in Candidate moves, by test title: list of (from, to, promotion piece or None).
CAND = {
  'White in check': [('c1','d2',None), ('b1','c3',None)],
  'Black in check': [('c7','c6',None)],
  'En passant (White)': [('e5','d6',None)],
  'En passant (Black)': [('e4','d3',None)],
  'Castling': [('e1','g1',None)],
  'Promotion: knight fork (White)': [('e7','e8','n'), ('e7','e8','q')],
  'Promotion: knight fork (Black)': [('e2','e1','n')],
  'Promotion with captures': [('b7','a8','r'), ('b7','b8','q')],
  'Mate in one': [('d1','d8',None)],
  'Stalemate trap (game move stalemates)': [('g1','g6',None)],
}
async def main():
    fails = []
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width':390,'height':760})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        async def route(r):
            if 'chess.js' in r.request.url: await r.fulfill(body=CHESS, content_type='application/javascript')
            else: await r.abort()
        await pg.route('http*://**/*', lambda r: asyncio.ensure_future(route(r)))
        await pg.set_content('<!doctype html><html><head><meta charset="utf-8"></head><body>'+SRC+'</body></html>')
        await pg.wait_for_timeout(300)
        await pg.evaluate("(()=>{"+FAKE+"})()")
        await pg.click('#accountBtn'); await pg.click('#testsBtn'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=str(SHOTS/'00_list.png'))
        names = await pg.evaluate("TEST_POSITIONS.map(p=>p.title)")
        for i, name in enumerate(names):
            # ---- Candidate moves: tap the moves in
            await pg.click(f'.chip-btn[data-i="{i}"][data-a="candidates"]'); await pg.wait_for_timeout(300)
            check = await pg.evaluate("document.querySelectorAll('#board .sq.check').length")
            if 'in check' in name and check != 1: fails.append(f'{name}: no check glow')
            if 'in check' not in name and check: fails.append(f'{name}: unexpected check glow')
            for (fr, to, promo) in CAND[name]:
                await pg.evaluate(f"(()=>{{ const sqs=[...document.querySelectorAll('#board .sq')]; const idx=s=>{{ const f='abcdefgh'.indexOf(s[0]), r=+s[1]; return boardFlipped() ? (r-1)*8+(7-f) : (8-r)*8+f; }}; sqs[idx('{fr}')].click(); }})()")
                await pg.wait_for_timeout(80)
                await pg.evaluate(f"(()=>{{ const sqs=[...document.querySelectorAll('#board .sq')]; const idx=s=>{{ const f='abcdefgh'.indexOf(s[0]), r=+s[1]; return boardFlipped() ? (r-1)*8+(7-f) : (8-r)*8+f; }}; sqs[idx('{to}')].click(); }})()")
                await pg.wait_for_timeout(120)
                if promo:
                    if not await pg.query_selector('.promo-overlay'): fails.append(f'{name}: no promotion picker'); continue
                    if promo=='n': await pg.screenshot(path=str(SHOTS/f'{i:02d}_picker.png'))
                    await pg.click(f'.promo-piece[data-p="{promo}"]'); await pg.wait_for_timeout(120)
            picks = await pg.evaluate("st('candidates').picks.map(m=>m.san+' '+m.uci)")
            if len(picks) != len(CAND[name]): fails.append(f'{name}: picks {picks}')
            await pg.screenshot(path=str(SHOTS/f'{i:02d}_cand_pick.png'))
            await pg.click('#check'); await pg.wait_for_timeout(4500)
            res = await pg.evaluate("[...document.querySelectorAll('.layer:not(.ghost) .review-col')[0].querySelectorAll('.mini-row')].map(r=>r.innerText.replace(/\\s+/g,' ')).join(' | ')")
            if '—' in res or '…' in res: fails.append(f'{name}: candidate not graded: {res}')
            await pg.screenshot(path=str(SHOTS/f'{i:02d}_cand_review.png'))
            print('cand ', name, '|', picks, '|', res)
            await pg.click('#homeBtn'); await pg.wait_for_timeout(200)
            # ---- Final choice: four moves, game move among them, all graded
            await pg.click(f'.chip-btn[data-i="{i}"][data-a="final"]'); await pg.wait_for_timeout(600)
            moves = await pg.evaluate("finalMoves(pos()).map(m=>m.san+(m.historical?'*':''))")
            if len(moves) != 4 or not any(m.endswith('*') for m in moves): fails.append(f'{name}: final moves {moves}')
            await pg.click('#check'); await pg.wait_for_timeout(4500)
            rows = await pg.evaluate("[...document.querySelectorAll('.layer:not(.ghost) .review-row')].map(r=>r.innerText.replace(/\\s+/g,' ')).join(' | ')")
            if '—' in rows: fails.append(f'{name}: final not graded: {rows}')
            await pg.screenshot(path=str(SHOTS/f'{i:02d}_final_review.png'))
            print('final', name, '|', rows)
            await pg.click('#homeBtn'); await pg.wait_for_timeout(200)
        recorded = await pg.evaluate("results.length")
        if recorded: fails.append(f'test positions were recorded ({recorded})')
        errs = [e for e in errs if 'importScripts' not in e]
        await b.close()
    if errs: fails.append(f'page errors: {errs}')
    print('\n'.join(['FAIL '+f for f in fails]) or 'ok')
    sys.exit(1 if fails else 0)
asyncio.run(main())
