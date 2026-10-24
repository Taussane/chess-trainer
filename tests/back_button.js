// tests/back_button.js (node; needs playwright): the phone's back button goes up one level at a time (settings ->
// profile -> home), closes the grades' scale first, and only leaves the site from the home page.
const { chromium } = require('playwright');
const path = require('path'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8793'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const cj = require('fs').readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 360, height: 740 } });
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); if (u.startsWith('data:')) return r.continue(); return r.abort(); });
  await p.goto('data:text/html,<p>before</p>');
  await p.goto('http://localhost:8793/'); await p.waitForTimeout(1500);
  const where = async () => p.url().startsWith('data:') ? 'LEFT THE SITE' : await p.evaluate(() => screen + (aspPicker ? '+scale' : ''));
  const back = async () => { await p.goBack({ timeout: 3000 }).catch(() => {}); await p.waitForTimeout(400); return where(); };
  const out = [];
  // 1. settings, then back x3
  await p.click('#accountBtn'); await p.waitForTimeout(300); await p.click('#settingsBtn'); await p.waitForTimeout(300);
  out.push('home > profile > settings: back -> ' + await back() + ', back -> ' + await back() + ', back -> ' + await back());
  await p.goto('http://localhost:8793/'); await p.waitForTimeout(1500);
  // 2. profile > settings > page arrow to profile > page arrow home, then back
  await p.click('#accountBtn'); await p.waitForTimeout(300); await p.click('#settingsBtn'); await p.waitForTimeout(300);
  await p.click('#homeBtn'); await p.waitForTimeout(300); await p.click('#homeBtn'); await p.waitForTimeout(500);
  out.push('arrows back to home (' + await where() + '), then back -> ' + await back());
  await p.goto('http://localhost:8793/'); await p.waitForTimeout(1500);
  // 3. exercise with the grades scale open
  await p.click('.card[data-go="imbalances"]'); await p.waitForTimeout(500);
  await p.click('#aspInput .asp-pick'); await p.waitForTimeout(300);
  out.push('imbalances with scale (' + await where() + '): back -> ' + await back() + ', back -> ' + await back());
  await p.goto('http://localhost:8793/'); await p.waitForTimeout(1500);
  // 4. exercise, back, profile, back
  await p.click('.card[data-go="analysis"]'); await p.waitForTimeout(300);
  const a = await back(); await p.click('#accountBtn'); await p.waitForTimeout(300);
  out.push('analysis: back -> ' + a + '; profile: back -> ' + await back() + ', back -> ' + await back());
  // 5. reload inside settings
  await p.goto('http://localhost:8793/'); await p.waitForTimeout(1500);
  await p.click('#accountBtn'); await p.waitForTimeout(300); await p.click('#settingsBtn'); await p.waitForTimeout(300);
  await p.reload(); await p.waitForTimeout(1500);
  out.push('reload in settings (' + await where() + '): back -> ' + await back());
  await b.close(); server.kill();
  const want = ['home > profile > settings: back -> account, back -> home, back -> LEFT THE SITE',
    'arrows back to home (home), then back -> LEFT THE SITE',
    'imbalances with scale (imbalances+scale): back -> imbalances, back -> home',
    'analysis: back -> home; profile: back -> home, back -> LEFT THE SITE',
    'reload in settings (home): back -> LEFT THE SITE'];
  const bad = want.filter((w, i) => out[i] !== w).map((w, i) => 'FAIL got: ' + out[want.indexOf(w)] + ' | want: ' + w);
  console.log(bad.length ? bad.join('\n') : 'ok'); process.exit(bad.length ? 1 : 0);
})();
