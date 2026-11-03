// The Plan finder's master positions: question 1's answer (planqUrgent) against Stockfish's lines, for the side to
// move and for the other side as if it were its turn (1 s each, the app's own engine; planqEngineAgrees). The positions
// it contradicts go into PLANQ_ENGINE_SKIP in app/index.html. About 35 minutes; results kept in OUT, so a run that stops
// carries on. Usage: node scripts/planq-engine-check.js [limit] [ms]   then python3 scripts/build-site.py
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = path.join(__dirname, '..'), OUT = process.env.OUT || '/tmp/planq-engine-check.json';
const server = spawn('python3', ['-m', 'http.server', '8798'], { cwd: ROOT, stdio: 'ignore' });
const cj = fs.readFileSync(path.join(ROOT, 'vendor/chess.js/chess.js'), 'utf8');
const LIMIT = +(process.argv[2] || 100000), MS = +(process.argv[3] || 1000);
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 390, height: 800 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto('http://localhost:8798/'); await p.waitForTimeout(3000);
  await p.evaluate(() => { masterEvals = null; loadMasterEvals(); });
  await p.waitForTimeout(3000);
  console.log('engine', await p.evaluate(() => sfState + ' ' + sfVersion + ' ' + Object.keys(masterEvals || {}).length));
  const keys = await p.evaluate(n => { const pq = new Set(PLANQ_POOL); return POOLS.analysis.filter(x => pq.has(x.key)).slice(0, n).map(x => x.key); }, LIMIT);   // (all the pool, before this check)
  const out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
  for (let i = 0; i < keys.length; i++) {
    if (out[keys[i]] && out[keys[i]].ms === MS) continue;
    const r = await p.evaluate(async ([key, ms]) => {
      const pos = POOLS.analysis.find(x => x.key === key);
      const run = fen => new Promise(res => { bgQueue.push({ fen, multipv: 1, movetime: ms, resolve: res }); pumpEngineQueue(); });
      const info = planqInfo(pos), vals = explorerVals(pos.fen);
      const c = planqMake(pos, info, vals, new Set()), u = c.urgent;
      const us = await run(pos.fen), f = flipSide(pos.fen), them = f ? await run(f) : null;
      const ul = us && us.lines && us.lines[0], tl = them && them.lines && them.lines[0];
      return { ms, kind: u.kind, stop: u.stop, amb: !!u.ambiguous, fit: !u.ambiguous && (u.stop || c.rows.some(r => r.answer)) && planqFits(pos, c),
        W: lineGain(pos.fen, ul), T: f ? lineGain(f, tl) : null, agree: planqEngineAgrees(u, ul, tl, pos.fen),
        usPv: ul && (ul.pv || []).slice(0, 8).join(' '), themPv: tl && (tl.pv || []).slice(0, 8).join(' '), usMate: ul && ul.mate, themMate: tl && tl.mate };
    }, [keys[i], MS]);
    out[keys[i]] = r;
    if (i % 20 === 0) { fs.writeFileSync(OUT, JSON.stringify(out)); console.log(i, Object.keys(out).length); }
  }
  fs.writeFileSync(OUT, JSON.stringify(out));
  const skip = Object.keys(out).filter(k => !out[k].agree).sort(), app = path.join(ROOT, 'app/index.html');
  fs.writeFileSync(app, fs.readFileSync(app, 'utf8').replace(/\/\*PLANQ_ENGINE_SKIP\*\/[\s\S]*?\/\*END PLANQ_ENGINE_SKIP\*\//, '/*PLANQ_ENGINE_SKIP*/' + JSON.stringify(skip) + '/*END PLANQ_ENGINE_SKIP*/'));
  console.log('left out:', skip.length, 'of', Object.keys(out).length);
  console.log('done', Object.keys(out).length, 'errors', errs.filter(e => !/importScripts/.test(e)));
  await b.close(); server.kill();
})();
