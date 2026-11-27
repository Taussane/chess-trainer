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
  // (the chunk from move 1: the Scotch's opening moves)
  await p.evaluate(() => { rep.c = 'w'; repStart(); const ch = repChunks('w').find(x => x.start === 0 && x.sans[1] === 'e5'); rep.drill = Object.assign(rep.drill, { fens:[EXPLORER_START], sans:[], moves:[], chunk:ch, plan:ch.plan, end:ch.sans.length, ch:ch.ch }); render(); });
  const d0 = await p.evaluate(() => ({ c: rep.drill.c, n: rep.drill.sans.length, prompt: document.querySelector('.layer:not(.ghost) .rep-prompt').textContent }));
  check('White: starts at the start, your move', d0.c === 'w' && d0.n === 0 && d0.prompt === 'Your move?', d0);
  const sqAttr = await p.evaluate(() => { const el = document.querySelector('#board > *'); return el ? [...el.attributes].map(a => a.name) : []; });
  // moves through the drill's own handler (the board's clicks are the explorer's, tested there)
  const tryMove = (from, to) => p.evaluate(([f, t]) => { const g = new Chess(rep.drill.fens[rep.drill.fens.length - 1]); repTry(g.moves({ verbose: true }).find(m => m.from === f && m.to === t)); }, [from, to]);
  await tryMove('d2', 'd4');
  const w1 = await p.evaluate(() => ({ n: rep.drill.sans.length, msg: rep.drill.msg, tries: rep.drill.tries, kept: repPos().fen.split(' ')[0] !== rep.drill.fens[0].split(' ')[0], btns: [...document.querySelectorAll('.layer:not(.ghost) .actions-row button')].map(b => b.id) }));
  check('a move not in your line: said, kept on the board, Try again (no Skip line)', w1.n === 0 && /Not your move/.test(w1.msg) && w1.tries === 1 && w1.kept && w1.btns.join() === 'repXp,repComment,repRetry', w1);
  await p.waitForFunction(() => rep.drill.msg !== 'Not your move here.', null, { timeout: 60000 }).catch(() => {});
  const w1b = await p.evaluate(() => rep.drill.msg);
  check('1.d4 instead of 1.e4: graded as the reviews grade (Best/Good/Ok), not your move', /^<b style="color:[^"]+">(Good|Ok)<\/b>, but not your move/.test(w1b), w1b);
  // Try again right away: the explanation still on its way stays with the wrong move, never over "Your move?"
  await tryMove('g1', 'f3'); await p.click('#repRetry'); await p.waitForTimeout(2500);
  const t1 = await p.evaluate(() => ({ msg: rep.drill.msg, prompt: document.querySelector('.layer:not(.ghost) .rep-prompt').textContent }));
  check('Try again before the explanation: "Your move?" stays', !t1.msg && t1.prompt === 'Your move?', t1);
  await tryMove('d2', 'd4'); await p.waitForFunction(() => /not your move\.$/.test(rep.drill.msg), null, { timeout: 60000 }).catch(() => {});
  check('the explanation shown while the move is on the board, with Lichess and Explore', await p.evaluate(() => !!rep.drill.wrong && /^(Good|Ok), but not your move/.test(document.querySelector('.layer:not(.ghost) .rep-prompt').textContent) && !!document.querySelector('.layer:not(.ghost) .actions-row a.xp-li[href*="d4"]')), null);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-grade.png' });
  const xp = await p.evaluate(() => { document.querySelector('.layer:not(.ghost) #repXp').click(); const r = { screen, at: explorer.at, n: explorer.sans.join(' '), flip: explorer.flip }; exploreReturn(); return Object.assign(r, { back: screen, wrong: !!rep.drill.wrong }); });
  check('Explore: the line and the wrong move in the explorer, back to the drill as it was', xp.screen === 'explorer' && !xp.flip && xp.n === 'd4' && xp.at === 1 && xp.back === 'repertoire' && xp.wrong, xp);
  await p.click('#repRetry');
  const t0 = await p.evaluate(() => ({ back: repPos().fen === rep.drill.fens[0], btns: [...document.querySelectorAll('.layer:not(.ghost) .actions-row button')].map(b => b.id + (b.disabled ? ':off' : '') + (b.classList.contains('rep-none') ? ':none' : '')) }));
  check('Try again: the position back, the toggles (Comment and marks, Show move; no Skip line)', t0.back && t0.btns.join() === 'repComment,repShow', t0);
  await p.click('#repComment');
  check('Comment and marks: the study\'s arrows too', await p.evaluate(() => document.querySelectorAll('#arrows line').length >= 1 && repStore.o.comment), null);
  await p.click('#repComment');
  await p.click('#repShow');
  check('Show move: an arrow, the toggle on', await p.evaluate(() => document.querySelectorAll('#arrows line').length === 1 && document.getElementById('repShow').classList.contains('on')), null);
  await tryMove('e2', 'e4'); await p.waitForTimeout(700);
  const w2 = await p.evaluate(() => ({ sans: rep.drill.sans, mark: rep.drill.marks, st: repStore.s['w|' + repKey(EXPLORER_START)] }));
  check('your move, then the opponent’s reply from the repertoire', w2.sans.length === 2 && w2.sans[0] === 'e4' && w2.mark[0] === 0, w2.sans);
  check('shown: checked for today (back tomorrow), one miss', w2.st && w2.st[0] === 0 && w2.st[1] > Date.now() && w2.st[1] <= new Date().setHours(24, 0, 0, 0) && w2.st[4] === 1, w2.st);
  // the pile: unchecked first, then checked not played this round, then played this round (earliest first); a round
  // over once all played: a new one, all still checked
  const pile = await p.evaluate(() => {
    const save = JSON.stringify(repStore), now = Date.now(), c = rep.c; rep.c = 'w';
    const L = repChunks('w'), id = x => 'w|' + x.key;
    repStore.l = {}; repStore.r = { t: now - 1000, seed: 1 }; rep.lastCh = null;
    L.forEach((x, i) => { repStore.l[id(x)] = [1, now + 5 * REP_DAY, 1, now - 500 + i, 0]; });   // all checked, played this round
    const a = L[5], b = L[3];
    repStore.l[id(a)][1] = now - 1; repStore.l[id(a)][4] = 2;    // a due
    repStore.l[id(b)][3] = now - 5000;                            // b checked, not played in this round
    const first = repPickChunk();
    repStore.l[id(a)][1] = now + REP_DAY; rep.lastCh = null;
    const second = repPickChunk();
    const r0 = repStore.r.t; repStore.l[id(b)][3] = now;          // every line played this round
    repPickChunk(); const newRound = repStore.r.t !== r0, cn = repCounts(), gaps = repGaps();
    // a line graded as a whole: a retry anywhere in it, due again tomorrow
    rep.drill = { chunk: a, marks: [2, 1, 2] }; repLineGrade(rep.drill);
    const g = repStore.l[id(a)], tomorrow = g[1] === repMidnight(now) + REP_DAY && g[0] === 0;
    repStore = JSON.parse(save); rep.c = c; repStart();
    return { ok1: first === a, ok2: second === b, newRound, checked: cn.due === 0, tomorrow, gaps };
  });
  check('the pile, by lines: due, then not played this round, then a new round with all checked; a retry: the line due tomorrow', pile.ok1 && pile.ok2 && pile.newRound && pile.checked && pile.tomorrow, pile);
  check('no position past a move to avoid (4...Qf6 5.c3 Bc5: only as 5.Be3 Bc5 6.c3)', await p.evaluate(() => repIndex('w').items.every(k => { const it = repIndex('w').at[k]; return !it.sans.join(' ').startsWith('e4 e5 Nf3 Nc6 d4 exd4 Nxd4 Qf6 c3'); })), null);
  const chunks = await p.evaluate(() => ['w', 'b'].map(c => { const l = repChunks(c); return { n: l.length, ok: l.every(x => x.pos.length > 0 && x.sans.length > x.start), setup: l.some(x => x.ch === 'Caro-Kann: Setup') }; }));
  check('lines: chunks by chapter, each with a move of yours (Caro-Kann setup its own)', chunks.every(x => x.n > 20 && x.ok) && chunks[1].setup, chunks);
  const nx = await p.evaluate(() => { const save = JSON.stringify(repStore); rep.c = 'b'; const out = []; for (let i = 0; i < 6; i++) { repStart(); const d = rep.drill; out.push({ ch: d.ch, start: d.sans.length, mine: d.fens[d.fens.length - 1].split(' ')[1] === 'b' }); repStore.l['b|' + d.chunk.key] = [1, Date.now() + REP_DAY, 1, Date.now(), 0]; } repStore = JSON.parse(save); rep.c = 'w'; return out; });
  check('next lines: each from your first move in its chunk, never the same chapter twice in a row', nx.every((x, i) => x.mine && (i === 0 || x.ch !== nx[i - 1].ch)), nx);
  check('gaps follow the repertoire: about 3 weeks at most here', pile.gaps[pile.gaps.length - 1] >= 14 && pile.gaps[pile.gaps.length - 1] <= 30, pile.gaps);
  // play the line to its end with the right moves
  for (let i = 0; i < 30; i++) {
    const s = await p.evaluate(() => { const d = rep.drill; if (d.done) return 'done'; const m = repMain(d.c, repKey(d.fens[d.fens.length - 1])); const g = new Chess(d.fens[d.fens.length - 1]); repTry(g.move(m[0])); return m[0]; });
    if (s === 'done') break; await p.waitForTimeout(600);
  }
  const w3 = await p.evaluate(() => ({ done: rep.drill.done, prompt: document.querySelector('.layer:not(.ghost) .rep-prompt').textContent, line: rep.drill.sans.join(' ') }));
  check('a line goes to its end', w3.done && /^Line complete/.test(w3.prompt), w3);
  const xd = await p.evaluate(() => { const n = rep.drill.sans.length; document.querySelector('.layer:not(.ghost) #repXp').click(); const r = { screen, at: explorer.at, n: explorer.sans.length, want: n }; exploreReturn(); return Object.assign(r, { back: screen, done: rep.drill.done }); });
  check('line complete: Explore opens it at its end, back to it', xd.screen === 'explorer' && xd.at === xd.want && xd.n === xd.want && xd.back === 'repertoire' && xd.done, xd);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-done.png' });
  await p.click('#repNext');
  check('next line: a line due (the one just played is checked for today, or due again tomorrow)', await p.evaluate(() => { const d = rep.drill, st = repLineSt(d.chunk); return !st || st[1] <= Date.now(); }), await p.evaluate(() => rep.drill.sans));
  // Black: a drill starts at your move (after White's)
  await p.evaluate(() => { rep.c = 'b'; repStart(); render(); });
  const b0 = await p.evaluate(() => ({ side: repPos().side, sans: rep.drill.sans, flip: boardFlipped() }));
  check('Black: your move, the board turned', b0.side === 'b' && b0.flip && b0.sans.length >= 1, b0);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk.png' });
  // a move your study says to avoid: what your study answers with (the Slav's 4...Bf5)
  await p.evaluate(() => { const it = repIndex('b').at[repKey(new Chess('rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 3 4').fen())]; rep.c = 'b'; repStart(); Object.assign(rep.drill, { fens:it.fens.slice(), sans:it.sans.slice(), moves:it.moves.slice(), tries:0 }); render(); });
  await tryMove('c8', 'f5');
  const av = await p.evaluate(() => ({ msg: rep.drill.msg, note: rep.drill.note }));
  check('a move to avoid: what your study answers with', /^Not the move: met by 5\. <b>cxd5<\/b> <b>cxd5<\/b> 6\. <b>Qb3<\/b>/.test(av.msg) && /double attack/.test(av.note), av);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-avoid.png' });
  // Review: a reply out of the repertoire in two games (1.d4 c6 2.Bf4) is listed, with a move to add
  await p.evaluate(() => { myGames.push({ id: 't1', me: 'b', sans: ['d4', 'c6', 'Bf4', 'd5', 'e3'], evals: [] }, { id: 't2', me: 'b', sans: ['d4', 'c6', 'Bf4', 'd5', 'Nf3'], evals: [] }, { id: 't3', me: 'b', sans: ['e4', 'c6', 'd4', 'd5', 'Nc3', 'dxe4', 'Nxe4', 'Bf5', 'Bd3', 'Qxd4'], evals: [] }); repGames = null; rep.view = 'review'; render(); });
  // (the proposed line given, as the engine would: 2...d5 3.e3 Bf5)
  const stub = n => p.evaluate(n => { const x = Object.values(repGameStats().gaps).find(g => g.san === 'Bf4'); repStore.prop[x.id] = { line: ['d4', 'c6', 'Bf4', 'd5', 'e3', 'Bf5'], auto: false }; render(); return x.id; }, n);
  check('the list searches nothing (a line is searched when opened)', await p.evaluate(() => Object.keys(repStore.prop).length === 0), null);
  const id = await stub();
  const r0 = await p.evaluate(() => { const row = document.querySelector('.layer:not(.ghost) [data-rline]') || document.querySelector('[data-rline]'); const h = row && row.closest('.rep-lines').previousElementSibling; return { text: row && row.textContent.replace(/\s+/g, ' ').trim(), head: h && h.textContent, lines: document.querySelectorAll('.rep-lines .rep-moves').length }; });
  check('Review: your lines by chapter, the London proposed under the setup it branches from', /\+ ?2\. Bf4 2 games/.test(r0.text) && /2 games/.test(r0.text) && /Black · (Slav Defense|Caro-Kann) · Setup/.test(r0.head) && r0.lines > 10, r0);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-review.png' });
  await p.click('[data-rline]');
  const l0 = await p.evaluate(() => ({ view: rep.view, top: document.querySelector('.pos-title').textContent, ply: rep.lv.ply, cur: (document.querySelector('#repMv .rep-cur') || {}).textContent }));
  check('the line on the board: their move not in your study, games against it, at their move', l0.view === 'line' && /2\. Bf4 isn't in your study/.test(l0.top) && /2 games against it/.test(l0.top) && l0.ply === 3 && l0.cur === 'Bf4', l0);
  await p.click('#repNextMv'); await p.keyboard.press('ArrowRight'); await p.keyboard.press('ArrowLeft');
  check('back and forth through it (buttons, arrow keys)', await p.evaluate(() => rep.lv.ply === 4), null);
  if (process.env.SHOTS) await p.screenshot({ path: '/tmp/rep-desk-line.png' });
  // your own move at their move: the line changed from there
  await p.evaluate(() => { rep.lv.ply = 3; render(); });
  const sq = s => p.evaluate(s => { const sqs = [...document.querySelectorAll('#board .sq')]; const f = 'abcdefgh'.indexOf(s[0]), r = +s[1]; sqs[boardFlipped() ? (r - 1) * 8 + (7 - f) : (8 - r) * 8 + f].click(); }, s);
  await sq('g8'); await sq('f6');
  const own = await p.evaluate(() => { const x = Object.values(repGameStats().gaps).find(g => g.san === 'Bf4'); return { line: repStore.prop[x.id].line.join(' '), ply: rep.lv.ply }; });
  check('your own move: the line from there is yours', own.line === 'd4 c6 Bf4 Nf6' && own.ply === 4, own);
  await p.click('#repSkipLine');
  check('Skip: no longer proposed', await p.evaluate(() => rep.view === 'review' && !document.querySelector('[data-rline]')), null);
  await p.evaluate(() => { myGames.push({ id: 't4', me: 'b', sans: ['d4', 'c6', 'Bf4', 'Qb6'], evals: [] }); repGames = null; render(); });
  await stub();
  const r2 = await p.evaluate(() => (document.querySelector('[data-rline]') || {}).textContent || '');
  check('more games against it: proposed again, with the new count', /3 games/.test(r2), r2);
  await p.click('[data-rline]'); await p.click('#repAddLine');
  const r1 = await p.evaluate(() => { const g = new Chess(); ['d4', 'c6', 'Bf4'].forEach(s => g.move(s)); const k = repKey(g.fen()); g.move('d5'); g.move('e3'); return { main: (repMain('b', k) || [])[0], main2: (repMain('b', repKey(g.fen())) || [])[0], line: repChunks('b').some(ch => ch.sans.join(' ') === 'd4 c6 Bf4 d5 e3 Bf5'), added: !!document.querySelector('.rep-lines .rep-tag'), copy: repStore.lines.some(l => l.line.join(' ') === 'd4 c6 Bf4 d5 e3 Bf5') }; });
  check('Add: the whole line in your repertoire, a line to drill, marked Added, to copy', r1.main === 'd5' && r1.main2 === 'Bf5' && r1.line && r1.added && r1.copy, r1);
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
