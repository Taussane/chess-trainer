// tests/csp.js (node; needs playwright): the website (index.html, with its Content-Security-Policy) used through
// every screen with the real engine: the policy never blocks anything the page needs.
const { chromium } = require('playwright');
const path = require('path'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8795'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 360, height: 740 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  // only this site (the page, its files): every other address is cut off, as in the other tests
  await p.route('**/*', r => r.request().url().startsWith('http://localhost:8795') ? r.continue() : r.abort());
  await p.addInitScript(() => { window.__csp = []; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI)); });
  await p.goto('http://localhost:8795/');
  const fails = [];
  const ready = await p.waitForFunction(() => sfState === 'ready', null, { timeout: 30000 }).then(() => true, () => false);
  if (!ready) fails.push('the engine did not start: ' + await p.evaluate(() => sfState + ' ' + sfLastError));
  const open = a => p.evaluate(a => { screen = 'home'; render(); document.querySelector(`.card[data-go="${a}"]`).click(); }, a);
  for (const a of ['imbalances', 'analysis', 'candidates', 'final']) {
    await open(a);
    await p.waitForFunction(() => !!document.getElementById('check'), null, { timeout: 30000 });
    await p.evaluate(() => document.getElementById('helpBtn').click()); await p.waitForTimeout(200);
    await p.evaluate(() => { helpVisible = false; render(); });
    await p.evaluate(a => { const s = st(a), q = pos(); s.barMoved = true; s.swapped = true; if (a === 'imbalances') ASPECTS.forEach(x => { s.asp[x.key] = 1; });
      if (a === 'candidates') { const u = new Chess(q.fen).moves({ verbose: true })[0]; s.picks = [{ uci: u.from + u.to + (u.promotion || ''), from: u.from, to: u.to, san: u.san, slot: 0 }]; }
      render(); const c = document.getElementById('check'); c.disabled = false; c.click(); }, a);
    const done = await p.waitForFunction(() => !!document.getElementById('nextPos') && !document.querySelector('.actions-row.pending'), null, { timeout: 20000 }).then(() => true, () => false);
    if (!done) fails.push(a + ': review did not finish');
  }
  for (const s of ['account', 'settings', 'support']) { await p.evaluate(s => { screen = s; render(); }, s); await p.waitForTimeout(400); }
  const v = await p.evaluate(() => window.__csp);
  if (v.length) fails.push('blocked by the policy: ' + [...new Set(v)].join(', '));
  if (errs.length) fails.push('page errors: ' + errs.join('; '));
  await b.close(); server.kill();
  console.log(fails.length ? fails.map(f => 'FAIL ' + f).join('\n') : 'ok');
  process.exit(fails.length ? 1 : 0);
})();
