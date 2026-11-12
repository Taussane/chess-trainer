// tests/docs.js (node; needs playwright): the FAQ, privacy and terms open inside the app, as a page like
// Settings (title, back arrow): FAQ -> a guide -> back, the phone's back button one level at a time, the
// privacy page, the beta (its own folder), the desktop menu; no new tab, no page errors.
const { chromium } = require('playwright');
const path = require('path'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8797'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const cj = require('fs').readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
const SHOTS = process.env.SHOTS;
let fails = 0; const check = (name, ok, info) => { console.log(name + ': ' + JSON.stringify(info)); if (!ok) { fails++; console.log('  FAIL'); } };
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(); const errors = [];
  const page = async (vp, url) => {
    const ctx = await b.newContext({ viewport: vp }); const p = await ctx.newPage();
    p.on('pageerror', e => errors.push(String(e)));
    await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
    await p.goto(url); await p.waitForTimeout(1500); return [ctx, p];
  };
  const st = p => p.evaluate(() => ({ screen, title: document.querySelector('#app h1') && document.querySelector('#app h1').textContent, depth: doc ? doc.stack.length : null }));
  // phone
  const [ctx, p] = await page({ width: 390, height: 844 }, 'http://localhost:8797/');
  await p.click('#accountBtn'); await p.waitForTimeout(400);
  await p.click('.ac-foot a[data-doc]:has-text("FAQ")'); await p.waitForTimeout(800);
  let s = await st(p); check('FAQ opens inside the app', s.screen === 'doc' && s.title === 'Frequently asked questions' && ctx.pages().length === 1, s);
  check('its cards are there', await p.locator('.doc-page .card').count() === 4, await p.locator('.doc-page .card').count());
  if (SHOTS) await p.screenshot({ path: SHOTS + '/doc_faq.png' });
  await p.click('.doc-page .card >> nth=0'); await p.waitForTimeout(800);
  s = await st(p); check('a guide opens one level deeper', s.title === 'Imbalance reading' && s.depth === 1, s);
  check('its picture loads', await p.evaluate(() => { const i = document.querySelector('.doc-page figure img'); return !!i && new URL(i.src).pathname === '/learn/img/imbalance-reading.webp'; }), null);
  if (SHOTS) { await p.waitForTimeout(500); await p.screenshot({ path: SHOTS + '/doc_guide.png' }); }
  await p.goBack(); await p.waitForTimeout(500); s = await st(p); check('back: the FAQ', s.title === 'Frequently asked questions' && s.depth === 0, s);
  await p.goBack(); await p.waitForTimeout(500); s = await st(p); check('back: the profile', s.screen === 'account', s);
  await p.goBack(); await p.waitForTimeout(500); s = await st(p); check('back: home', s.screen === 'home', s);
  await p.click('#accountBtn'); await p.waitForTimeout(400);
  await p.click('.ac-foot a[data-doc]:has-text("Privacy")'); await p.waitForTimeout(800);
  s = await st(p); check('privacy opens inside the app', s.screen === 'doc' && /privacy/i.test(s.title || ''), s);
  if (SHOTS) await p.screenshot({ path: SHOTS + '/doc_privacy.png' });
  await p.click('#homeBtn'); await p.waitForTimeout(500); s = await st(p); check('the arrow: back to the profile', s.screen === 'account', s);
  await ctx.close();
  // the beta (its pages from the site's root)
  const [c2, p2] = await page({ width: 390, height: 844 }, 'http://localhost:8797/beta/');
  await p2.click('#accountBtn'); await p2.waitForTimeout(400);
  await p2.click('.ac-foot a[data-doc]:has-text("Terms")'); await p2.waitForTimeout(800);
  s = await st(p2); check('beta: terms open inside the app', s.screen === 'doc' && /terms/i.test(s.title || '') && await p2.locator('.doc-page p').count() > 2, s);
  await c2.close();
  // desktop: from the menu
  const [c3, p3] = await page({ width: 1400, height: 900 }, 'http://localhost:8797/');
  await p3.click('.side-links a[data-doc]:has-text("FAQ")'); await p3.waitForTimeout(800);
  s = await st(p3); check('desktop: the menu\'s FAQ', s.screen === 'doc' && s.title === 'Frequently asked questions' && c3.pages().length === 1, s);
  await p3.click('.doc-page .card >> nth=3'); await p3.waitForTimeout(800);
  check('desktop: a guide has its back arrow', await p3.locator('#homeBtn').isVisible(), null);
  if (SHOTS) await p3.screenshot({ path: SHOTS + '/doc_desk.png' });
  await p3.click('#homeBtn'); await p3.waitForTimeout(500); s = await st(p3); check('desktop: back to the FAQ', s.title === 'Frequently asked questions', s);
  await c3.close();
  check('no page errors', errors.length === 0, errors);
  await b.close(); server.kill();
  console.log(fails ? fails + ' FAILED' : 'ok'); process.exit(fails ? 1 : 0);
})();
