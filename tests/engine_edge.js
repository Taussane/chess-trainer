// tests/engine_edge.js (node; needs playwright): the exercises with the real engine in awkward moments: leaving a
// review before its evaluation is in (it finishes and is recorded once), the engine failing mid-review ("Engine
// unavailable", never stuck), a hung engine (given up within seconds), rapid switching, a quick routine.
const { chromium } = require('playwright');
const path = require('path'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8794'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const cj = require('fs').readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
const res = [];
const ok = (name, cond, extra) => res.push((cond ? 'ok   ' : 'FAIL ') + name + (extra ? '  (' + extra + ')' : ''));
async function page(b) {
  const p = await b.newPage({ viewport: { width: 360, height: 740 } });
  p.errs = []; p.on('pageerror', e => p.errs.push(e.message));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto('http://localhost:8794/'); await p.waitForFunction(() => sfState === 'ready', null, { timeout: 30000 }); await p.waitForTimeout(500);
  return p;
}
const answer = (p, a) => p.evaluate(a => { const s = st(a), q = pos(); s.barMoved = true; s.swapped = true;
  if (a === 'imbalances') ASPECTS.forEach(x => { s.asp[x.key] = 1; });
  if (a === 'candidates') { const u = new Chess(q.fen).moves({ verbose: true })[0]; s.picks = [{ uci: u.from + u.to + (u.promotion || ''), from: u.from, to: u.to, san: u.san, slot: 0 }]; }
  render(); const c = document.getElementById('check'); if (!c) throw new Error('no Check button on ' + a); c.disabled = false; c.click(); }, a);
const open = async (p, a) => { await p.evaluate(a => { screen = 'home'; render(); document.querySelector(`.card[data-go="${a}"]`).click(); }, a); };
const reviewDone = (p, ms) => p.waitForFunction(() => !!document.getElementById('nextPos') && !document.querySelector('.actions-row.pending'), null, { timeout: ms }).then(() => true, () => false);
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch();
  // 1. Leave a review before its evaluation is in, come back: it completes and is recorded once
  for (const a of ['analysis', 'candidates', 'final']) {
    const p = await page(b);
    await open(p, a); await p.waitForFunction(() => !!document.getElementById('check'), null, { timeout: 30000 });
    const n0 = await p.evaluate(() => results.length);
    await answer(p, a); await p.waitForTimeout(100);
    await p.evaluate(() => document.getElementById('homeBtn').click()); await p.waitForTimeout(1500);
    await open(p, a);
    const done = await reviewDone(p, 15000);
    await p.waitForTimeout(500);
    const n1 = await p.evaluate(() => results.length), same = await p.evaluate(() => !!st(screen).checked);
    ok(`${a}: left during the review, came back`, done && same && n1 === n0 + 1, `review finished: ${done}, recorded ${n1 - n0}`);
    ok(`${a}: no page errors`, !p.errs.length, p.errs.join('; '));
    await p.close();
  }
  // 2. The engine stops working in the middle of a review: "Engine unavailable", never stuck
  for (const a of ['analysis', 'candidates', 'final', 'imbalances']) {
    const p = await page(b);
    await open(p, a); await p.waitForFunction(() => !!document.getElementById('check'), null, { timeout: 30000 });
    if (a !== 'final') await p.evaluate(() => { fenEvalStore = {}; poolEvalStore = {}; aspectsStore = {}; });   // nothing prepared
    await answer(p, a); await p.waitForTimeout(150);
    await p.evaluate(() => failEngine('stopped'));
    await p.waitForTimeout(1500);
    const t = await p.evaluate(() => document.querySelector('#app .layer:not(.ghost)') ? document.querySelector('#app .layer:not(.ghost)').innerText : document.getElementById('app').innerText);
    const next = await p.evaluate(() => !!document.getElementById('nextPos'));
    ok(`${a}: engine failure mid-review`, a === 'imbalances' ? next : /unavailable|couldn't|stopped working/i.test(t) && !/Evaluating/.test(t) && next, t.replace(/\s+/g, ' ').slice(0, 120));
    ok(`${a}: no page errors after failure`, !p.errs.length, p.errs.join('; '));
    await p.close();
  }
  // 3. A hung engine (no answer): the watchdog gives up instead of waiting forever
  {
    const p = await page(b);
    await open(p, 'analysis'); await p.waitForFunction(() => !!document.getElementById('check'), null, { timeout: 30000 });
    await p.evaluate(() => { fenEvalStore = {}; try { sfWorker.postMessage('stop'); } catch (e) {} });
    await p.waitForTimeout(300);
    await p.evaluate(() => { const post = sfWorker.postMessage.bind(sfWorker); sfWorker.postMessage = m => { if (/^go |^stop/.test(m)) return; post(m); }; sfWorker.onmessage = () => {}; });
    await answer(p, 'analysis');
    const t0 = Date.now();
    const gave = await p.waitForFunction(() => sfState === 'error', null, { timeout: 30000 }).then(() => true, () => false);
    ok('hung engine: gives up within 8 s', gave && Date.now() - t0 < 8000, `after ${Math.round((Date.now() - t0) / 1000)} s`);
    await p.close();
  }
  // 4. Rapid switching between exercises, then each one still works
  {
    const p = await page(b);
    for (let i = 0; i < 12; i++) { await open(p, ['analysis', 'candidates', 'final', 'imbalances'][i % 4]); await p.waitForTimeout(60); }
    const q = await p.evaluate(() => sfQueue.length);
    for (const a of ['final', 'candidates', 'analysis']) {
      await open(p, a);
      const shown = await p.waitForFunction(() => !!document.getElementById('check'), null, { timeout: 15000 }).then(() => true, () => false);
      await answer(p, a); const done = await reviewDone(p, 15000);
      ok(`rapid switching, then ${a}`, shown && done, `queue was ${q}`);
    }
    ok('rapid switching: no page errors', !p.errs.length, p.errs.join('; '));
    await p.close();
  }
  // 5. Routine through two rounds, quickly: every question shows, every review finishes
  {
    const p = await page(b);
    await p.evaluate(() => document.getElementById('routineBtn').click());
    let fails = [];
    for (let k = 0; k < 8; k++) {
      const a = await p.evaluate(() => screen);
      const shown = await p.waitForFunction(() => !!document.getElementById('check'), null, { timeout: 15000 }).then(() => true, () => false);
      if (!shown) { fails.push(a + ' question'); break; }
      await answer(p, a); if (!await reviewDone(p, 15000)) { fails.push(a + ' review'); break; }
      await p.evaluate(() => document.getElementById('nextPos').click()); await p.waitForTimeout(100);
    }
    ok('routine, 2 rounds answered quickly', !fails.length, fails.join(', '));
    ok('routine: no page errors', !p.errs.length, p.errs.join('; '));
    await p.close();
  }
  await b.close(); server.kill();
  const bad = res.filter(x => x.startsWith('FAIL'));
  console.log(process.argv.includes('-v') ? res.join('\n') : bad.length ? bad.join('\n') : 'ok');
  process.exit(bad.length ? 1 : 0);
})();
