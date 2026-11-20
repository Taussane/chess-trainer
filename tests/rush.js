// tests/rush.js (node; needs playwright and the engine): Rush. The home page's Rush switch: the cards show each
// exercise's best, the routine card becomes Mixed rush. A run of Move selection: the first position shown at once,
// the clock (on the line above the board) still until the move into the position has been played, stopped at Check
// for the usual review (its score line: the run's total), going on at Next position; at the end, the run's results
// (positions, average accuracy, total points), its timeline and history, the best and the run kept, nothing else
// recorded (results, played positions untouched). A mixed run: the four exercises in the routine's order, the Plan
// finder's clock running between its questions; left early, no score. The end page in French. Switched off: back to
// the averages.
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
  await p.goto('http://localhost:8798/'); await p.waitForFunction(() => typeof sfState !== 'undefined' && sfState === 'ready' && progressLoaded, null, { timeout: 60000 });
  await p.evaluate(() => { firstVisit = null; screen = 'home'; render(); }); await p.waitForTimeout(300);
  // the switch
  check('the Rush switch on the home page, off', await p.evaluate(() => { const t = document.getElementById('rushToggle'); return !!t && t.getAttribute('aria-pressed') === 'false'; }), null);
  await p.click('#rushToggle'); await p.waitForTimeout(300);
  const home = await p.evaluate(() => ({ on: rushOn, card: (document.querySelector('.rush-card .routine-title') || {}).textContent, best: [...document.querySelectorAll('.card[data-go] .card-level small')].map(x => x.textContent) }));
  check('on: the Mixed rush card, each exercise card its best', home.on && home.card === 'Mixed rush' && home.best.length === 4 && home.best.every(x => x === 'Best'), home);
  // a run of Move selection
  await p.click('.card[data-go="final"]');
  const first = await p.evaluate(() => ({ screen, rushMode, clock: !!document.querySelector('.pl-line #rushClock'), ticking: rushTicking() }));
  check('the first position at once, the clock above the board, not running yet', first.screen === 'final' && first.rushMode && first.clock && !first.ticking, first);
  await p.waitForFunction(() => rushTicking(), null, { timeout: 60000 });
  for (let i = 0; i < 2; i++) {
    await p.waitForFunction(() => rushMode && screen === 'final' && rushTicking() && !!document.getElementById('check') && !st('final').checked, null, { timeout: 60000 });
    await p.waitForTimeout(600); await p.evaluate(() => document.getElementById('check').click());
    const l0 = await p.evaluate(() => rushLeft()); await p.waitForTimeout(1200);
    const rv = await p.evaluate(() => ({ phase: rush.phase, left: rushLeft() }));
    check(`position ${i + 1}: Check stops the clock for the review`, rv.phase === 'review' && rv.left === l0, { ...rv, l0 });
    await p.waitForFunction(() => rush.items.length === rush.shown && !!document.getElementById('nextPos') && /Total \d+/.test((document.querySelector('#app .level') || {}).textContent || ''), null, { timeout: 60000 });
    await p.evaluate(() => document.getElementById('nextPos').click()); await p.waitForTimeout(300);
  }
  check('Next position: the next one, its clock going on', await p.evaluate(() => rush.shown === 3 && rushMode && screen === 'final'), null);
  await p.waitForFunction(() => rushTicking(), null, { timeout: 60000 });
  await p.evaluate(() => { rush.left = 60; rush.at = performance.now(); });
  await p.waitForFunction(() => rush && rush.phase === 'end', null, { timeout: 10000 }); await p.waitForTimeout(300);
  const end = await p.evaluate(() => ({ screen, n: rush.items.length, score: rush.score, tiles: [...document.querySelectorAll('.rush-stat b')].map(x => x.textContent),
    timeline: document.querySelectorAll('.rc-tl rect').length, history: document.querySelectorAll('.rc-hist rect').length, best: (profile.rushPts || {}).final,
    runs: ((profile.rushRuns || {}).final || []).length, results: results.length, played: rush.items.some(x => isPlayed(x.key)) }));
  check('the end: positions, average accuracy and total points', end.screen === 'rush' && end.n === 2 && end.tiles[0] === '2' && end.tiles[2] === String(end.score), end);
  check('its timeline (a bar per position) and history', end.timeline === 2 && end.history >= 1, end);
  check('the best and the run kept', end.best === end.score && end.runs === 1, end);
  check('nothing else recorded: no results, no position marked played', end.results === 0 && !end.played, end);
  // the end page in French
  await p.evaluate(() => { settings.lang = 'fr'; setLanguage(); render(); }); await p.waitForTimeout(300);
  const fr = await p.evaluate(() => [...document.querySelectorAll('#app .pf-h, .rush-stat small')].map(x => x.textContent.trim()));
  check('the end page in French', fr.includes('Résultats de la série') && fr.includes('Historique') && fr.some(x => /^Points au total/.test(x)), fr);
  await p.evaluate(() => { settings.lang = 'en'; setLanguage(); }); await p.click('#rushMenu'); await p.waitForTimeout(300);
  check('Done: the home page, the card showing the best', await p.evaluate(() => screen === 'home' && document.querySelector('.card[data-go="final"] .card-level b').textContent === String(profile.rushPts.final)), null);
  // a mixed run
  await p.click('#routineBtn');
  await p.waitForFunction(() => rushMode && screen === 'imbalances' && rushTicking(), null, { timeout: 60000 });
  await p.evaluate(() => { const c = document.getElementById('check'); c.disabled = false; c.click(); });
  await p.waitForFunction(() => rush.items.length === 1 && !!document.getElementById('nextPos'), null, { timeout: 60000 });
  await p.evaluate(() => document.getElementById('nextPos').click());
  await p.waitForFunction(() => rushMode && screen === 'planq' && rushTicking() && planq && !planq.done, null, { timeout: 60000 });
  check('mixed: Imbalance reading, then the Plan finder', true, null);
  await p.evaluate(() => { document.querySelectorAll('.layer:not(.ghost) .pq-side[data-first]').forEach((b, i) => { if (i % 3 === 0) b.click(); }); document.querySelectorAll('.layer:not(.ghost) .pq-side[data-row]').forEach((b, i) => { if (i % 2 === 0) b.click(); }); });
  await p.evaluate(() => { const c = document.getElementById('pqCheck'); c.disabled = false; c.click(); }); await p.waitForTimeout(300);
  const pq = await p.evaluate(() => ({ done: planq.done, phase: rush.phase }));
  check("the Plan finder's first Check: the clock goes on (unless it ends the position)", pq.done ? pq.phase === 'review' : pq.phase === 'run', pq);
  await p.click('#homeBtn'); await p.waitForTimeout(300);
  check('left early: the home page, no mixed score', await p.evaluate(() => screen === 'home' && !rush && !(profile.rushPts || {}).mixed), null);
  // switched off
  await p.click('#rushToggle'); await p.waitForTimeout(300);
  check('off: the routine card and the averages again', await p.evaluate(() => !rushOn && !document.querySelector('.rush-card') && [...document.querySelectorAll('.card[data-go] .card-level small')].every(x => x.textContent === 'Average')), null);
  check('no page errors', !errs.length, errs.slice(0, 2));
  await b.close(); server.kill();
  console.log(fail.length ? 'FAILED: ' + fail.join('; ') : 'ok'); process.exit(fail.length ? 1 : 0);
})();
