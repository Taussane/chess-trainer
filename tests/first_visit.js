// tests/first_visit.js (node; needs playwright and the engine): a first visit (nothing played, not logged in, no link)
// opens straight on Move selection; its review offers "All exercises" in place of the Lichess, explorer and share
// buttons, beside Next position; Next goes on with Move selection, All exercises goes home. A returning visitor (a
// result in this browser) starts on the home screen.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8797'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const cj = fs.readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
const fail = []; const check = (what, ok, got) => { console.log((ok ? '' : 'FAIL ') + what + ':', JSON.stringify(got)); if (!ok) fail.push(what); };
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 390, height: 844 } });
  await p.addInitScript(() => { try { localStorage.setItem('cst.testFirstVisit', '1'); } catch (e) {} });
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto('data:text/html,<p>before</p>');
  await p.goto('http://localhost:8797/');
  await p.waitForFunction(() => typeof screen !== 'undefined' && screen === 'final', null, { timeout: 60000 }).catch(() => {});
  check('a first visit opens on Move selection', await p.evaluate(() => screen === 'final' && firstVisit === 'on'), await p.evaluate(() => [screen, firstVisit]));
  const answer = async () => {
    await p.waitForFunction(() => !!document.getElementById('check') && sfState === 'ready', null, { timeout: 60000 });
    await p.evaluate(() => { const s = st('final'); s.swapped = true; render(); const c = document.getElementById('check'); if (c) c.disabled = false; });
    await p.click('#check'); await p.waitForSelector('#allExercises', { timeout: 60000 }); await p.waitForTimeout(400);
  };
  await answer();
  const row = await p.evaluate(() => [...document.querySelectorAll('.layer:not(.ghost) .actions-row.split > *')].map(e => e.id || e.className));
  check('its review: All exercises and Next position only', JSON.stringify(row) === JSON.stringify(['allExercises', 'nextPos']), row);
  await p.click('#nextPos'); await p.waitForTimeout(1500);
  check('Next position: Move selection again, still the first visit', await p.evaluate(() => screen === 'final' && firstVisit === 'on' && !st('final').checked), await p.evaluate(() => [screen, firstVisit]));
  await answer();
  await p.click('#allExercises'); await p.waitForTimeout(500);
  check('All exercises: the home screen, the first visit over', await p.evaluate(() => screen === 'home' && !firstVisit), await p.evaluate(() => [screen, firstVisit]));
  await p.goBack({ timeout: 3000 }).catch(() => {}); await p.waitForTimeout(400);
  check('back from there leaves the site', p.url().startsWith('data:'), p.url().slice(0, 30));
  // a returning visitor: the home screen, and its reviews keep their Lichess, explorer and share buttons
  await p.goto('http://localhost:8797/'); await p.waitForTimeout(2500);
  check('a returning visitor starts at home', await p.evaluate(() => screen === 'home' && !firstVisit && results.length > 0), await p.evaluate(() => [screen, firstVisit, results.length]));
  await b.close(); server.kill();
  console.log(fail.length ? 'FAILED: ' + fail.join('; ') : 'ok'); process.exit(fail.length ? 1 : 0);
})();
