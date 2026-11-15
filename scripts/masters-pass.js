// The master games through the same core as your own games: one pass per game (one top-5 search per position, 1 s, the
// app's engine), then each exercise's positions read from it. Two steps, both resumable:
//  1. node scripts/masters-pass.js                 the pass (SHARD=i/n runs every n-th game, one engine per process:
//                                                  run n side by side with their own PORT; their results all go to
//                                                  finder/.cache/pass/, one file per game)
//  2. STEP=select node scripts/masters-pass.js     the selection, once every game has its pass (only the Plan finder's
//                                                  check of the other side searches again: 1 s per candidate)
// The selection, per exercise (the general rules first: moves 5 to 40, 4+ legal moves, not right after a capture that
// can simply be taken back, not in a mate already under way; a position found in several games is kept once):
//  - Candidate moves and Move selection: the game's mistakes first (a move that lost 10+ points, either side), when
//    they pass the exercise's rule, then the other positions by the same rule: Candidate moves a trap among the top 5
//    and at most 3 decent moves, 10 half-moves apart; Move selection its four moves spread enough (the game move judged
//    from the next position), 2 apart.
//  - Imbalance reading and the Plan finder: as scripts/strategy-pass.js (from the middlegame's start to just past the
//    endgame's start, 7 apart, the same rules), with the pass's evaluation and best line.
// Writes app/index.html (/*POOLS*/), data/pools.json (Candidate moves and Move selection with their measurements, for
// starters.py) and master-evals.json (each kept position's top 3 moves). Then: python3 scripts/build-site.py,
// python3 scripts/starters.py, python3 scripts/planq-starters.py.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = path.join(__dirname, '..'), PASS_DIR = path.join(ROOT, 'finder/.cache/pass'), PORT = +(process.env.PORT || 8821);
const [SH_I, SH_N] = (process.env.SHARD || '0/1').split('/').map(Number), STEP = process.env.STEP || 'pass';
const MAX_MIN = +(process.env.MAX_MIN || 1e9);   // stop cleanly after this many minutes (a run resumes where it stopped)
fs.mkdirSync(PASS_DIR, { recursive: true });
const server = spawn('python3', ['-m', 'http.server', String(PORT)], { cwd: ROOT, stdio: 'ignore' });
const cj = fs.readFileSync(path.join(ROOT, 'vendor/chess.js/chess.js'), 'utf8');
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const p = await b.newPage(); p.setDefaultTimeout(0); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto(`http://localhost:${PORT}/`); await p.waitForTimeout(3000);
  console.log('engine', await p.evaluate(() => sfState + ' ' + sfVersion));
  const games = (await p.evaluate(() => Object.keys(GAME_MOVES))).slice(0, +(process.env.LIMIT || 1e9));   // (LIMIT=n: the first n games, for a try)
  const file = gid => path.join(PASS_DIR, gid + '.json');
  if (STEP === 'pass') {
    const mine = games.filter((g, i) => i % SH_N === SH_I), t0 = Date.now(); let done = 0;
    for (const gid of mine) {
      if (fs.existsSync(file(gid))) { done++; continue; }
      if ((Date.now() - t0) / 60000 > MAX_MIN) { console.log('stopping after', MAX_MIN, 'min'); break; }
      const pass = await p.evaluate(async gid => {
        const g = { id: gid, site: 'master', evalBy: 'none', status: 'queued', me: 'w', sans: GAME_MOVES[gid].split(' ').filter(Boolean), evals: null };
        myGames = [g]; myGamesLoaded = true;
        const r = await ownPass(gid); return r === 'ok' ? g.pass : null;
      }, gid);
      if (pass) fs.writeFileSync(file(gid), JSON.stringify(pass));
      done++;
      if (done % 5 === 0) console.log(new Date().toISOString().slice(11, 19), done, '/', mine.length, Math.round((Date.now() - t0) / 1000) + 's');
    }
    console.log('pass done for this shard:', mine.filter(g => fs.existsSync(file(g))).length, '/', mine.length, errs.slice(0, 3));
    await b.close(); server.kill(); return;
  }
  // STEP=select
  const missing = games.filter(g => !fs.existsSync(file(g)));
  if (missing.length) { console.log('pass missing for', missing.length, 'games, e.g.', missing.slice(0, 5)); await b.close(); server.kill(); return; }
  const out = { imbalances: [], planq: [], candidates: [], final: [] }, evals = {}, seen = { imbalances: new Set(), planq: new Set(), candidates: new Set(), final: new Set() };
  let n = 0;
  for (const gid of games) {
    const r = await p.evaluate(async ([gid, pass]) => {
      const run = (fen, multipv, ms) => new Promise(res => { bgQueue.push({ fen, multipv, movetime: ms, resolve: res }); pumpEngineQueue(); });
      const g = { id: gid, site: 'master', evalBy: 'none', status: 'queued', me: 'w', sans: GAME_MOVES[gid].split(' ').filter(Boolean), pass };
      const c = new Chess(), fens = [c.fen()], hist = [];
      for (const s of g.sans) { const m = c.move(s); if (!m) break; hist.push(m); fens.push(c.fen()); }
      g.sans = g.sans.slice(0, hist.length);
      for (let ply = 0; ply <= hist.length; ply++) DEV_HIST.set(fens[ply], devTouched(hist, ply));
      const ev = passEvals(g, fens, hist), uci = m => m.from + m.to + (m.promotion || ''), keyOf = fen => fen.split(' ').slice(0, 4).join(' ');
      const nextLine = ply => { const nx = passLines(g, ply + 1); if (nx && nx.length) return { cp: nx[0].cp == null ? null : -nx[0].cp, mate: nx[0].mate == null ? null : -nx[0].mate };
        if (nx) { const e = new Chess(fens[ply + 1]); return e.in_checkmate() ? { cp: null, mate: 1 } : { cp: 0, mate: null }; } return null; };
      const decentOf = top => { const best = winPercent(top[0].cp, top[0].mate); return top.filter(l => best - winPercent(l.cp, l.mate) < OWN.trapMinDrop).length; };
      const res = { imbalances: [], planq: [], candidates: [], final: [], evals: {}, meta: {} };
      const sc = l => l.mate != null ? 'm' + l.mate : String(Math.round(l.cp));
      // master-evals.json: the top 3 and best evaluation (as before), then the top 5 with their values and the game move's
      // value when it isn't among them (from the next position): Move selection picks its four moves from those at once
      const keep = (list, ply, meta) => { res[list].push(ply); const top = passLines(g, ply);
        if (top && top.length) { const gmU = uci(hist[ply]), gl = top.some(l => l.uci === gmU) ? null : nextLine(ply);
          res.evals[keyOf(fens[ply])] = [top.slice(0, 3).map(l => l.uci), top[0].mate != null ? null : top[0].cp, top[0].mate, top.map(l => l.uci + ':' + sc(l)).join(','), gl ? sc(gl) : null]; }
        res.meta[list + ':' + ply] = { key: keyOf(fens[ply]), fen: fens[ply], moveNo: +fens[ply].split(' ')[5], side: fens[ply].split(' ')[1], ...meta }; };
      // Candidate moves and Move selection: mistakes first, then the rest
      const C = {}, F = {}, mist = [];
      for (let ply = 1; ply < hist.length; ply++) {
        const fen = fens[ply], mn = +fen.split(' ')[5]; if (mn < OWN.minMove || mn > OWN.maxMove) continue;
        const pc = new Chess(fen); if (pc.moves().length < 4) continue;
        const prev = hist[ply - 1]; if (prev && prev.captured && pc.moves({ verbose: true }).some(m => m.to === prev.to && m.captured)) continue;
        if (ev[ply - 2] && ev[ply - 1] && ev[ply - 2].mate != null && ev[ply - 1].mate != null) continue;   // (a mate already under way)
        const top = passLines(g, ply); if (!top || top.length < 2) continue;
        const t = fen.split(' ')[1], bf = winForMover(ev[ply - 1], t), af = winForMover(ev[ply], t), drop = bf != null && af != null ? bf - af : 0;
        const dec = decentOf(top);
        C[ply] = { trap: dec < top.length && dec <= OWN.maxDecent, dec }; F[ply] = passFinalOk(top, uci(hist[ply]), nextLine(ply));
        if (drop >= OWN.mistakeDrop) mist.push({ ply, drop: Math.round(drop) });
      }
      const near = (k, x, gap) => k.some(y => Math.abs(y - x) < gap), plies = Object.keys(C).map(Number).sort((a, b) => a - b);
      const keptC = mist.filter(m => C[m.ply].dec <= OWN.maxDecent).map(m => m.ply), keptF = mist.filter(m => F[m.ply]).map(m => m.ply);
      const mistDrop = Object.fromEntries(mist.map(m => [m.ply, m.drop]));
      for (const x of plies) { if (!keptC.includes(x) && C[x].trap && !near(keptC, x, OWN.candidatesSpacing)) keptC.push(x); }
      for (const x of plies) { if (!keptF.includes(x) && F[x] && !near(keptF, x, OWN.finalSpacing)) keptF.push(x); }
      keptC.sort((a, b) => a - b).forEach(x => keep('candidates', x, { metrics: { decentMoves: C[x].dec, ...(mistDrop[x] ? { mistake: mistDrop[x] } : {}) } }));
      keptF.sort((a, b) => a - b).forEach(x => keep('final', x, { metrics: mistDrop[x] ? { mistake: mistDrop[x] } : {} }));
      // Imbalance reading and the Plan finder (as strategy-pass.js, from the pass)
      const div = divideGame(fens), from = div.mid >= 0 ? div.mid : div.end;
      if (from >= 0) {
        const to = div.end >= 0 ? div.end + 3 : hist.length - 1, SP = 7, wp = cp => Math.max(1, Math.min(99, 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1)));
        let lastImb = -99, lastPlan = -99;
        for (let ply = Math.max(1, from); ply <= Math.min(to, hist.length - 1); ply++) {
          const imbOk = ply - lastImb >= SP, planOk = ply - lastPlan >= SP; if (!imbOk && !planOk) continue;
          const fen = fens[ply], moveNo = +fen.split(' ')[5]; if (moveNo < 5 || moveNo > 40) continue;
          const q0 = new Chess(fen); if (q0.in_check() || q0.moves().length < 4) continue;
          const prev = hist[ply - 1]; if (prev && prev.captured) continue;
          if (Math.abs(materialDiff(q0)) > 3) continue;
          let vals; try { vals = explorerVals(fen, true); } catch (e) { continue; }
          if (!vals || vals.special || hiddenCastlingLoss(fen) || staticEval(fen) == null) continue;
          const imbCand = imbOk && ASPECTS.filter(x => !isOff(vals, x) && aspectLevel(vals[x.key], x.key, vals)).length >= 3 && !gradesDisagree(fen, vals);
          if (!imbCand && !planOk) continue;
          const top = passLines(g, ply); if (!top || !top.length) continue;
          const info = toWhitePerspective({ cp: top[0].mate != null ? null : top[0].cp, mate: top[0].mate }, fen), cpW = info.mate != null ? null : info.cp;
          if (imbCand && info.mate == null && Math.abs(cpW) < 500 && Math.abs(wp(staticEval(fen) * 100) - wp(cpW)) < 25) {
            const lean = ASPECTS.reduce((t, x) => t + (isOff(vals, x) ? 0 : aspectLevel(vals[x.key], x.key)), 0);
            if (!imbalanceLeanWrong(vals, cpW) && !(lean === 0 && Math.abs(cpW) >= 100) && !decisiveDisagree(fen, vals)) { keep('imbalances', ply, {}); lastImb = ply; }
          }
          if (planOk) {
            const pos = { key: keyOf(fen), fen, side: fen.split(' ')[1], moveNo };
            const q = planqMake(pos, info, vals, new Set());
            if (!q.urgent.pending && !q.urgent.ambiguous && q.rows.some(r => r.answer) && planqFits(pos, q)) {
              const pv = g.pass.pv && g.pass.pv[ply], usLine = { ...top[0], pv: pv ? pv.split(' ') : [top[0].uci] };
              const f = flipSide(fen), them = f ? await run(f, 1, 1000) : null;
              if (planqEngineAgrees(q.urgent, usLine, them && !them.failed && them.lines && them.lines[0], fen)) { keep('planq', ply, {}); lastPlan = ply; }
            }
          }
        }
      }
      return res;
    }, [gid, JSON.parse(fs.readFileSync(file(gid), 'utf8'))]);
    const num = +gid.slice(1);
    for (const k of Object.keys(out)) for (const ply of r[k]) {
      const m = r.meta[k + ':' + ply]; if (seen[k].has(m.key)) continue; seen[k].add(m.key);
      out[k].push({ ...m, game: gid, ply, num });
    }
    Object.assign(evals, r.evals);
    if (++n % 50 === 0) console.log(n, '/', games.length, Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])));
  }
  if (process.env.DRY) { console.log('dry run:', Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])), errs.slice(0, 3)); await b.close(); server.kill(); return; }
  // into the app, data/pools.json and master-evals.json
  const app = path.join(ROOT, 'app/index.html'); let s = fs.readFileSync(app, 'utf8');
  s = s.replace(/\/\*POOLS\*\/(.*?)\/\*END POOLS\*\//s, () => '/*POOLS*/' + JSON.stringify(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.map(e => [e.num, e.ply])]))) + '/*END POOLS*/');
  fs.writeFileSync(app, s);
  const pj = path.join(ROOT, 'data/pools.json'), old = JSON.parse(fs.readFileSync(pj, 'utf8'));
  const strip = e => { const { num, ...rest } = e; return rest; };
  fs.writeFileSync(pj, JSON.stringify({ ...old, version: 'masters-pass ' + new Date().toISOString().slice(0, 10), generated: new Date().toISOString(),
    pools: { candidates: out.candidates.map(strip), final: out.final.map(strip), imbalances: out.imbalances.map(strip), planq: out.planq.map(strip) } }, null, 1) + '\n');
  fs.writeFileSync(path.join(ROOT, 'master-evals.json'), JSON.stringify(evals));
  console.log('done:', Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])), '| mistakes first: candidates', out.candidates.filter(e => e.metrics && e.metrics.mistake).length,
    'final', out.final.filter(e => e.metrics && e.metrics.mistake).length, '| evaluations', Object.keys(evals).length, '| errors', errs.filter(e => !/importScripts/.test(e)).slice(0, 3));
  await b.close(); server.kill();
})();
