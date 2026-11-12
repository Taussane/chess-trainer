// Imbalance reading's and the Plan finder's own master positions: a pass over every half-move of the master games
// (from the middlegame's start to just past the endgame's start, moves 5 to 40), each exercise keeping its own
// positions 7 half-moves apart within a game. A half-move that fails is followed by the next one, so a rejected
// position leaves room for its neighbours.
//  - every candidate: not in check, 4+ legal moves, the last move not a capture, material within 3 pawns, a reading
//    from Stockfish 10 (not a special ending), no hidden castling loss; for Imbalance reading also 3 criteria graded at
//    least and none read otherwise by Stockfish 10's own terms (gradesDisagree);
//  - then the app's engine (Stockfish 19 lite in the page, 1.2 s, top 3: kept in master-evals.json for the reviews):
//    Imbalance reading: no mate, under 5 pawns, the search within 2 squares of the bar of Stockfish 10's static
//    evaluation, the grades not leaning against Stockfish's better side (0.5 or more), no decisive criterion ranked last by
//    Stockfish's scaled terms (decisiveDisagree), not all level against 1.0
//    or more; the Plan finder: its own rules (planqFits, question 1 not ambiguous, a decided row or a stop after
//    phase 1), and Stockfish's check of question 1 for both sides (1 s each: planqEngineAgrees). A position that ends after
//    phase 1 (a piece or more, or a mate, at stake) gives way to one of the next 2 half-moves whose plan questions follow.
// Results are kept in OUT as it goes (a run that stops carries on). At the end: writes the two lists into
// app/index.html (/*POOLS*/: "imbalances" and "planq") and the new evaluations into master-evals.json.
// Usage: node scripts/strategy-pass.js   (about 1.5 hours with SHARD=0/2 and 1/2 side by side), then python3 scripts/build-site.py,
// python3 scripts/starters.py and python3 scripts/planq-starters.py
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = path.join(__dirname, '..'), OUT = process.env.OUT || '/tmp/strategy-pass.json', PORT = +(process.env.PORT || 8811);
// SHARD=i/n: only every n-th game from i (one engine per process: run n of them side by side, each with its own OUT and
// PORT; then merge their OUT files into one and run once more without SHARD: every game is in, it only writes the results)
const [SH_I, SH_N] = (process.env.SHARD || '0/1').split('/').map(Number);
const SPACING = 7, MS = 1200, CHECK_MS = 1000;
const server = spawn('python3', ['-m', 'http.server', String(PORT)], { cwd: ROOT, stdio: 'ignore' });
const cj = fs.readFileSync(path.join(ROOT, 'vendor/chess.js/chess.js'), 'utf8');
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const p = await b.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto(`http://localhost:${PORT}/`); await p.waitForTimeout(3000);
  await p.evaluate(async () => { masterEvals = null; loadMasterEvals(); for (let i = 0; i < 100 && !(masterEvals && Object.keys(masterEvals).length); i++) await new Promise(r => setTimeout(r, 100)); });
  console.log('engine', await p.evaluate(() => sfState + ' ' + sfVersion), 'evals', await p.evaluate(() => Object.keys(masterEvals).length));
  const out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
  const games = (await p.evaluate(() => Object.keys(GAME_MOVES))).slice(0, +(process.env.LIMIT || 1e9)).filter((g, i) => i % SH_N === SH_I);
  const t0 = Date.now(); let done = 0;
  for (const gid of games) {
    if (out[gid]) { done++; continue; }
    out[gid] = await p.evaluate(async ([gid, SPACING, MS, CHECK_MS]) => {
      const run = (fen, multipv, ms) => new Promise(res => { bgQueue.push({ fen, multipv, movetime: ms, resolve: res }); pumpEngineQueue(); });
      const wp = cp => Math.max(1, Math.min(99, 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1)));
      const sans = (GAME_MOVES[gid] || '').split(' ').filter(Boolean), c = new Chess(), fens = [c.fen()], hist = [];
      for (const s of sans) { const m = c.move(s); if (!m) break; hist.push(m); fens.push(c.fen()); }
      // Development's reading needs the moves played before each position (as the app has them for its own positions)
      { const rs = replaySans(sans, hist.length); for (let ply = 0; ply <= hist.length; ply++) if (rs.fens[ply]) DEV_HIST.set(rs.fens[ply], devTouched(rs.moves, ply)); }
      const res = { imb: [], plan: [], evals: {}, tried: 0, searched: 0 };
      const div = divideGame(fens), from = div.mid >= 0 ? div.mid : div.end; if (from < 0) return res;
      const to = div.end >= 0 ? div.end + 3 : hist.length - 1;
      let lastImb = -99, lastPlan = -99;   // (the Plan finder: a piece or more at stake, or a mate, is left out by planqFits)
      for (let ply = Math.max(1, from); ply <= Math.min(to, hist.length - 1); ply++) {
        const imbOk = ply - lastImb >= SPACING, planOk = ply - lastPlan >= SPACING;
        if (!imbOk && !planOk) continue;
        const fen = fens[ply], moveNo = +fen.split(' ')[5]; if (moveNo < 5 || moveNo > 40) continue;
        const g = new Chess(fen); if (g.in_check() || g.moves().length < 4) continue;
        const prev = hist[ply - 1]; if (prev && prev.captured) continue;
        if (Math.abs(materialDiff(g)) > 3) continue;
        let vals; try { vals = explorerVals(fen, true); } catch (e) { continue; }
        if (!vals || vals.special || hiddenCastlingLoss(fen) || staticEval(fen) == null) continue;
        // Imbalance reading's own: 3 criteria graded at least, none read otherwise by Stockfish 10 (the Plan finder checks its own)
        const imbCand = imbOk && ASPECTS.filter(x => !isOff(vals, x) && aspectLevel(vals[x.key], x.key, vals)).length >= 3 && !gradesDisagree(fen, vals);
        if (!imbCand && !planOk) continue;
        res.tried++;
        const key = fen.split(' ').slice(0, 4).join(' ');
        let usLine = null;
        if (!(masterEvals[key] && [].concat(masterEvals[key][0]).length >= 3)) {
          const r = await run(fen, 3, MS); res.searched++;
          const ls = r && !r.failed && r.lines || []; if (!ls.length) continue;
          usLine = ls[0];
          masterEvals[key] = res.evals[key] = [ls.slice(0, 3).map(l => l.uci), ls[0].mate != null ? null : ls[0].cp, ls[0].mate];
        }
        const m = masterEvals[key], info = toWhitePerspective({ cp: m[1], mate: m[2] }, fen), cpW = info.mate != null ? null : info.cp;
        // Imbalance reading
        if (imbCand && info.mate == null && Math.abs(cpW) < 500 && Math.abs(wp(staticEval(fen) * 100) - wp(cpW)) < 25) {
          const lean = ASPECTS.reduce((t, x) => t + (isOff(vals, x) ? 0 : aspectLevel(vals[x.key], x.key)), 0);
          if (!imbalanceLeanWrong(vals, cpW) && !(lean === 0 && Math.abs(cpW) >= 100) && !decisiveDisagree(fen, vals)) { res.imb.push(ply); lastImb = ply; }
        }
        // the Plan finder
        if (planOk) {
          const pos = { key, fen, side: fen.split(' ')[1], moveNo };
          const q = planqMake(pos, info, vals, new Set());
          if (!q.urgent.pending && !q.urgent.ambiguous && q.rows.some(r => r.answer) && planqFits(pos, q)) {
            if (!usLine || !usLine.pv) { const r = await run(fen, 1, CHECK_MS); res.searched++; usLine = r && !r.failed && r.lines && r.lines[0] || null; }
            const f = flipSide(fen), them = f ? await run(f, 1, CHECK_MS) : null; if (f) res.searched++;
            if (usLine && planqEngineAgrees(q.urgent, usLine, them && !them.failed && them.lines && them.lines[0], fen)) {
              res.plan.push(ply); lastPlan = ply;
            }
          }
        }
      }
      return res;
    }, [gid, SPACING, MS, CHECK_MS]);
    done++;
    if (done % 10 === 0) { fs.writeFileSync(OUT, JSON.stringify(out)); const tot = Object.values(out); console.log(done, '/', games.length, 'imb', tot.reduce((t, x) => t + x.imb.length, 0), 'plan', tot.reduce((t, x) => t + x.plan.length, 0), Math.round((Date.now() - t0) / 60000), 'min'); }
  }
  fs.writeFileSync(OUT, JSON.stringify(out));
  if (SH_N > 1) { console.log('shard done', SH_I, '/', SH_N); await b.close(); server.kill(); return; }
  // into the app and master-evals.json
  const num = g => +g.slice(1), imb = [], plan = [], evals = JSON.parse(fs.readFileSync(path.join(ROOT, 'master-evals.json'), 'utf8'));
  for (const [gid, r] of Object.entries(out)) { r.imb.forEach(ply => imb.push([num(gid), ply])); r.plan.forEach(ply => plan.push([num(gid), ply])); Object.assign(evals, r.evals); }
  const sortRefs = a => a.sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  const app = path.join(ROOT, 'app/index.html'); let s = fs.readFileSync(app, 'utf8');
  s = s.replace(/\/\*POOLS\*\/(.*?)\/\*END POOLS\*\//s, (m0, j) => { const P = JSON.parse(j); P.imbalances = sortRefs(imb); P.planq = sortRefs(plan); return '/*POOLS*/' + JSON.stringify(P) + '/*END POOLS*/'; });
  fs.writeFileSync(app, s);
  fs.writeFileSync(path.join(ROOT, 'master-evals.json'), JSON.stringify(evals));
  console.log('done: Imbalance reading', imb.length, '| Plan finder', plan.length, '| evaluations', Object.keys(evals).length, '| errors', errs.filter(e => !/importScripts/.test(e)));
  await b.close(); server.kill();
})();
