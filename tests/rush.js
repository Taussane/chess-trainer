// tests/rush.js (node; needs playwright and the engine): the beta's Rush on Move selection. From the home card: the
// first position prepared, a 3-2-1 countdown, then positions one after another, each Check adding its accuracy,
// the score their average (no review); at the end, the score, the positions with their points, the best kept; nothing recorded
// (results, played positions untouched). Not on the main site.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8798'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const cj = fs.readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
const fail = []; const check = (what, ok, got) => { console.log((ok ? '' : 'FAIL ') + what + ':', JSON.stringify(got)); if (!ok) fail.push(what); };
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 390, height: 844 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto('http://localhost:8798/'); await p.waitForTimeout(2000);
  check('no Rush on the main site', await p.evaluate(() => !document.getElementById('rushOpen')), null);
  await p.goto('http://localhost:8798/beta/'); await p.waitForFunction(() => typeof sfState !== 'undefined' && sfState === 'ready' && progressLoaded, null, { timeout: 60000 });
  await p.click('#rushOpen'); await p.waitForTimeout(300); await p.click('[data-rush="final"]');
  const t0 = Date.now();
  await p.waitForFunction(() => rush && rush.phase === 'count', null, { timeout: 60000 });
  check('the first position ready within 30 s', Date.now() - t0 < 30000, Math.round((Date.now() - t0) / 1000) + ' s');
  await p.waitForFunction(() => rush && rush.phase === 'run' && rushMode && screen === 'final', null, { timeout: 10000 });
  check('a run: clock and score on the top line, chips above the board', await p.evaluate(() => !!document.getElementById('rushClock') && !!document.querySelector('.rush-bar')), null);
  for (let i = 0; i < 3; i++) {
    await p.waitForFunction(() => rushMode && screen === 'final' && !!document.getElementById('check') && !st('final').checked, null, { timeout: 60000 });
    await p.waitForTimeout(800); await p.evaluate(() => document.getElementById('check').click()); await p.waitForTimeout(300);
  }
  const mid = await p.evaluate(() => ({ n: rush.items.length, avg: Math.round(rush.items.reduce((t, x) => t + x.pts, 0) / rush.items.length), score: rush.score }));
  check('three positions scored, the score their average', mid.n === 3 && mid.avg === mid.score, mid);
  await p.evaluate(() => { if (rush.phase === 'run') rush.at = performance.now() - rush.left + 50; else rush.left = 50; });
  await p.waitForFunction(() => rush && rush.phase === 'end', null, { timeout: 60000 });
  const end = await p.evaluate(() => ({ screen, rows: document.querySelectorAll('.rush-row').length, best: (profile.rushBest || {}).final, score: rush.score, results: results.length, played: [...document.querySelectorAll('.rush-row')].length && rush.items.some(x => isPlayed(x.key)) }));
  check('the end: score, a row per position, the best kept', end.screen === 'rush' && end.rows === 3 && end.best === end.score, end);
  check('nothing recorded: no results, no position marked played', end.results === 0 && !end.played, end);
  await p.click('#rushMenu'); await p.waitForTimeout(300);
  check('the Rush page shows the best', await p.evaluate(() => /Best: \d+%/.test(document.querySelector('[data-rush="final"]').textContent)), null);
  check('no page errors', !errs.length, errs.slice(0, 2));
  await b.close(); server.kill();
  console.log(fail.length ? 'FAILED: ' + fail.join('; ') : 'ok'); process.exit(fail.length ? 1 : 0);
})();
