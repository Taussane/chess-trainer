// tests/repertoire.js (node; needs playwright): the Repertoire screen (beta, the owner only). A drill starts at a
// position where it's your move; a move not in your line is only said (the board stays), Show move draws the arrow;
// your move gets the opponent's reply from your repertoire; a line goes to its end. The pile: a shown position comes
// first next time. Review: a reply your games have no line for is listed and can be added (then it's in the drills).
// SHOTS=1 also saves screenshots (phone, desktop) to /tmp/rep-*.png.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8798'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const cj = fs.readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
const fail = []; const check = (what, ok, got) => { console.log((ok ? '' : 'FAIL ') + what + ':', JSON.stringify(got)); if (!ok) fail.push(what); };
const open = async (b, vp) => {
  const p = await b.newPage({ viewport: vp, deviceScaleFactor: process.env.SHOTS ? 2 : 1 });
  p.on('pageerror', e => fail.push('page error: ' + e.message));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto('http://localhost:8798/beta/');
  await p.waitForFunction(() => typeof render === 'function' && typeof renderRepertoire === 'function', null, { timeout: 60000 });
  await p.evaluate(() => { lichessAuth = { username: 'Taussane' }; localStorage.removeItem('cst.rep'); repStore = null; rep = null; screen = 'repertoire'; render(); });
  return p;
};
// plays a move by clicking its squares
const play = async (p, from, to) => { await p.click(`#board [data-sq="${from}"]`).catch(() => p.evaluate(([f, t]) => { const d = rep.drill; d.sel = f; render(); }, [from, to])); await p.click(`#board [data-sq="${to}"]`); };
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch();
  const p = await open(b, { width: 1440, height: 900 });
  check('the owner sees it in the menu', await p.evaluate(() => !!document.querySelector('[data-side="repertoire"]')), null);
  // White only: nothing played yet, one of the three new positions closest to the start; here, the start itself
  await p.evaluate(() => { rep.c = 'w'; repStart(); const it = repIndex('w').at[repKey(EXPLORER_START)]; rep.drill = Object.assign(rep.drill, { fens:it.fens.slice(), sans:[], moves:[] }); render(); });
  const d0 = await p.evaluate(() => ({ c: rep.drill.c, n: rep.drill.sans.length, prompt: document.querySelector('.layer:not(.ghost) .rep-prompt').textContent }));
  check('White: starts at the start, your move', d0.c === 'w' && d0.n === 0 && d0.prompt === 'Your move?', d0);
  const sqAttr = await p.evaluate(() => { const el = document.querySelector('#board > *'); return el ? [...el.attributes].map(a => a.name) : []; });
  // moves through the drill's own handler (the board's clicks are the explorer's, tested there)
  const tryMove = (from, to) => p.evaluate(([f, t]) => { const g = new Chess(rep.drill.fens[rep.drill.fens.length - 1]); repTry(g.moves({ verbose: true }).find(m => m.from === f && m.to === t)); }, [from, to]);
  await tryMove('d2', 'd4');
  const w1 = await p.evaluate(() => ({ n: rep.drill.sans.length, msg: rep.drill.msg, tries: rep.drill.tries, kept: repPos().fen.split(' ')[0] !== rep.drill.fens[0].split(' ')[0], btns: [...document.querySelectorAll('.layer:not(.ghost) .actions-row button')].map(b => b.id) }));
  check('a move not in your line: said, kept on the board, Try again and Skip line', w1.n === 0 && /Not your move/.test(w1.msg) && w1.tries === 1 && w1.kept && w1.btns.join() === 'repRetry,repSkip', w1);
  await p.waitForFunction(() => rep.drill.msg !== 'Not your move here.', null, { timeout: 60000 }).catch(() => {});
  const w1b = await p.evaluate(() => rep.drill.msg);
  check('1.d4 instead of 1.e4: playable, not your move', /^Playable, but not your move/.test(w1b), w1b);
  // Try again right away: the explanation still on its way stays with the wrong move, never over "Your move?"
  await tryMove('g1', 'f3'); await p.click('#repRetry'); await p.waitForTimeout(2500);
  const t1 = await p.evaluate(() => ({ msg: rep.drill.msg, prompt: document.querySelector('.layer:not(.ghost) .rep-prompt').textContent }));
  check('Try again before the explanation: "Your move?" stays', !t1.msg && t1.prompt === 'Your move?', t1);
  await tryMove('d2', 'd4'); await p.waitForFunction(() => /^Playable/.test(rep.drill.msg), null, { timeout: 60000 }).catch(() => {});
  check('the explanation shown while the move is on the board', await p.evaluate(() => !!rep.drill.wrong && /^Playable/.test(document.querySelector('.layer:not(.ghost) .rep-prompt').textContent)), null);
  await p.click('#repRetry');
  const t0 = await p.evaluate(() => ({ back: repPos().fen === rep.drill.fens[0], btns: [...document.querySelectorAll('.layer:not(.ghost) .actions-row button')].map(b => b.id + (b.disabled ? ':off' : '')) }));
  check('Try again: the position back, the toggles (Comment off: no comment at the start)', t0.back && t0.btns.join() === 'repComment:off,repMarks,repShow,repSkip', t0);
  await p.click('#repMarks');
  check('Marks: the study\'s arrows', await p.evaluate(() => document.querySelectorAll('#arrows line').length >= 1 && repStore.o.marks), null);
  await p.click('#repMarks');
  await p.click('#repShow');
  check('Show move: an arrow, the toggle on', await p.evaluate(() => document.querySelectorAll('#arrows line').length === 1 && document.getElementById('repShow').classList.contains('on')), null);
  await tryMove('e2', 'e4'); await p.waitForTimeout(700);
  const w2 = await p.evaluate(() => ({ sans: rep.drill.sans, mark: rep.drill.marks, st: repStore.s['w|' + repKey(EXPLORER_START)] }));
  check('your move, then the opponent’s reply from the repertoire', w2.sans.length === 2 && w2.sans[0] === 'e4' && w2.mark[0] === 0, w2.sans);
  check('shown: first in the pile', w2.st && w2.st[0] === 0 && w2.st[1] < Date.now(), w2.st);
  // play the line to its end with the right moves
  for (let i = 0; i < 30; i++) {
    const s = await p.evaluate(() => { const d = rep.drill; if (d.done) return 'done'; const m = repMain(d.c, repKey(d.fens[d.fens.length - 1])); const g = new Chess(d.fens[d.fens.length - 1]); repTry(g.move(m[0])); return m[0]; });
    if (s === 'done') break; await p.waitForTimeout(600);
  }
  const w3 = await p.evaluate(() => ({ done: rep.drill.done, prompt: document.querySelector('.layer:not(.ghost) .rep-prompt').textContent, line: rep.drill.sans.join(' ') }));
  check('a line goes to its end', w3.done && /^Line complete/.test(w3.prompt), w3);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-done.png' });
  await p.click('#repNext');
  check('next line: the shown start again first', await p.evaluate(() => rep.drill.sans.length === 0), await p.evaluate(() => rep.drill.sans));
  // Black: a drill starts at your move (after White's)
  await p.evaluate(() => { rep.c = 'b'; repStart(); render(); });
  const b0 = await p.evaluate(() => ({ side: repPos().side, sans: rep.drill.sans, flip: boardFlipped() }));
  check('Black: your move, the board turned', b0.side === 'b' && b0.flip && b0.sans.length >= 1, b0);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk.png' });
  // a move your study says to avoid: what your study answers with (the Slav's 4...Bf5)
  await p.evaluate(() => { const it = repIndex('b').at[repKey(new Chess('rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 3 4').fen())]; rep.c = 'b'; repStart(); Object.assign(rep.drill, { fens:it.fens.slice(), sans:it.sans.slice(), moves:it.moves.slice(), tries:0 }); render(); });
  await tryMove('c8', 'f5');
  const av = await p.evaluate(() => ({ msg: rep.drill.msg, note: rep.drill.note }));
  check('a move to avoid: what your study answers with', /^Not the move: met by 5\.cxd5 cxd5 6\.Qb3/.test(av.msg) && /double attack/.test(av.note), av);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-avoid.png' });
  // Review: a reply out of the repertoire in two games (1.d4 c6 2.Bf4) is listed, with a move to add
  await p.evaluate(() => { myGames.push({ id: 't1', me: 'b', sans: ['d4', 'c6', 'Bf4', 'd5', 'e3'], evals: [] }, { id: 't2', me: 'b', sans: ['d4', 'c6', 'Bf4', 'd5', 'Nf3'], evals: [] }, { id: 't3', me: 'b', sans: ['e4', 'c6', 'd4', 'd5', 'Nc3', 'dxe4', 'Nxe4', 'Bf5', 'Bd3', 'Qxd4'], evals: [] }); repGames = null; rep.view = 'review'; render(); });
  const r0 = await p.evaluate(() => [...document.querySelectorAll('.rep-item .rep-moves')].map(e => e.textContent));
  check('Review: the London listed', r0.some(t => t === '1.d4 c6 2.Bf4'), r0);
  await p.evaluate(() => { const x = Object.values(repGameStats().gaps).find(g => g.san === 'Bf4'); repProposals.set(x.id, { san: 'd5', cp: 0, yours: true }); render(); });
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-review.png' });
  await p.click('[data-radd]');
  const r1 = await p.evaluate(() => { const g = new Chess(); ['d4', 'c6', 'Bf4'].forEach(s => g.move(s)); return { main: (repMain('b', repKey(g.fen())) || [])[0], item: repIndex('b').items.includes(repKey(g.fen())) }; });
  check('Add: your move there, in the drills', r1.main === 'd5' && r1.item, r1);
  await p.close();
  // phone
  const ph = await open(b, { width: 412, height: 915 });
  await ph.evaluate(() => { rep.c = 'b'; repStart(); render(); });
  if (process.env.SHOTS) await ph.screenshot({ path: '/tmp/rep-phone.png' });
  const fit = await ph.evaluate(() => { const b = document.getElementById('board').getBoundingClientRect(), a = document.querySelector('.layer:not(.ghost) .actions-row').getBoundingClientRect(); return { board: Math.round(b.width), actionsBottom: Math.round(a.bottom), h: innerHeight }; });
  check('phone: board and buttons on screen', fit.actionsBottom <= fit.h, fit);
  await b.close(); server.kill();
  console.log(fail.length ? `${fail.length} FAILED: ${fail.join(' | ')}` : 'all passed'); process.exit(fail.length ? 1 : 0);
})().catch(e => { console.error(e); server.kill(); process.exit(1); });
