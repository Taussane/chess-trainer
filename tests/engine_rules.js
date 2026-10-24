// tests/engine_rules.js (node; needs playwright): the evaluation rules, timed with the real engine. Each exercise is
// answered like a player would (quickly, and after a long think) and how long the review (or Move selection's
// moves) waits is checked:
//  - every search goes to depth 20, at most 10 s ahead of time; once you wait for it (a review, Move selection's
//    moves), 3 s at most in all (a search already past 3 s stops at once);
//  - Candidate moves: its top 5 stops as the review opens (the finder's top 3 come with the app), then one search
//    of your picks with them, 3 s at most; none when the top 5 ran 3 s (or depth 20) and has all your picks;
//  - Imbalance reading's quick mate check never waits behind a long search;
//  - the next position is prepared from the review on, ahead of what the home page prepared.
// Prints the engine log with -v.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const server = spawn('python3', ['-m', 'http.server', '8792'], { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
const verbose = process.argv.includes('-v'); const fails = [];
const expect = (label, ms, max) => { if (ms > max) fails.push(`${label}: ${ms} ms (max ${max})`); };
const cj = fs.readFileSync(path.join(__dirname, '../vendor/chess.js/chess.js'), 'utf8');
const LOG = `
window.__log = []; window.__t0 = performance.now();
const tag = f => { const id = (window.__ids = window.__ids || {}); if(!(f in id)) id[f] = 'P' + Object.keys(id).length; return id[f]; };
window.__tag = tag;
const hook = ()=>{
  if(!sfWorker || sfWorker.__hooked) return; sfWorker.__hooked = true;
  const post = sfWorker.postMessage.bind(sfWorker);
  sfWorker.postMessage = m => {
    if(/^go /.test(m)) { const j = sfCurrentJob; window.__log.push([Math.round(performance.now()-__t0), 'go', tag(j.fen) + (j.fen===(curPos&&curPos.fen) ? '(open)' : ''), (j.searchmoves ? j.searchmoves.split(' ').length + ' moves' : 'top' + (j.multipv||5)), m.replace(/ searchmoves.*/, '')]); }
    if(m==='stop') window.__log.push([Math.round(performance.now()-__t0), 'stop', sfCurrentJob ? tag(sfCurrentJob.fen) : '-']);
    post(m);
  };
  const on = sfWorker.onmessage;
  sfWorker.onmessage = e => { if(typeof e.data==='string' && /^bestmove/m.test(e.data) && sfCurrentJob) window.__log.push([Math.round(performance.now()-__t0), 'done', tag(sfCurrentJob.fen), 'depth ' + sfCurrentDepth, Math.round(performance.now()-sfStartedAt) + 'ms']); on(e); };
};
setInterval(hook, 5);
`;
(async () => {
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 360, height: 740 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.route('**/*', r => { const u = r.request().url(); if (u.startsWith('http://localhost')) return r.continue(); if (u.includes('chess.js')) return r.fulfill({ body: cj, contentType: 'application/javascript' }); return r.abort(); });
  await p.goto('http://localhost:8792/');
  await p.evaluate(LOG);
  const mark = async s => { await p.evaluate(s => window.__log.push([Math.round(performance.now()-__t0), '----', s]), s); };
  const dump = async () => { const l = await p.evaluate(() => window.__log.splice(0)); if (verbose) l.forEach(x => console.log(x.join('  '))); };
  const t = () => p.evaluate(() => performance.now());
  const waitReady = async (fn) => { const t0 = await t(); await p.waitForFunction(fn, null, { timeout: 30000, polling: 20 }); return Math.round(await t() - t0); };
  

  await p.waitForTimeout(3000); await mark('home 3 s'); await dump();
  const open = async a => { await p.click(`.card[data-go="${a}"]`); await p.waitForTimeout(50); };
  const home = async () => { await p.click('#homeBtn'); await p.waitForTimeout(100); };
  const next = async () => { await p.evaluate(() => document.getElementById('nextPos').click()); await p.waitForTimeout(50); };

  {
    // Position evaluation: answer after 1 s, then after 5 s
    await open('analysis');
    for (const think of [1000, 5000]) {
      await mark(`analysis question (${await p.evaluate(()=>__tag(curPos.fen))}), answering after ${think} ms`); await p.waitForTimeout(think);
      await p.evaluate(() => { const s = st('analysis'); s.barMoved = true; render(); document.getElementById('check').click(); });
      const ms = await waitReady(() => !!fenEval(pos().fen)); await mark(`analysis review ready after ${ms} ms`); expect(`Position evaluation review after ${think} ms`, ms, think > 3000 ? 300 : 3300);
      await p.waitForTimeout(1500); await dump(); await next();
    }
    await home();
    // Imbalance reading: a long search is probably running for something prepared
    await open('imbalances');
    for (const think of [300, 3000]) {
      await mark(`imbalances question (${await p.evaluate(()=>__tag(curPos.fen))}), answering after ${think} ms`); await p.waitForTimeout(think);
      await p.evaluate(() => { const s = st('imbalances'); ASPECTS.forEach(x => { s.asp[x.key] = s.asp[x.key] || 1; }); render(); const c = document.getElementById('check'); c.disabled = false; c.click(); });
      const ms = await waitReady(() => aspectsEntry(pos().fen).status === 'done'); await mark(`imbalances review ready after ${ms} ms`); expect(`Imbalance reading review after ${think} ms`, ms, 800);
      await p.waitForTimeout(1000); await dump(); await next();
    }
    await home();
    // Candidate moves: pick the 2 first legal moves after 1 s; then the engine's top 2 after 12 s
    await open('candidates');
    for (const [think, how] of [[1000, 'any'], [12000, 'top']]) {
      await mark(`candidates question (${await p.evaluate(()=>__tag(curPos.fen))}), picking (${how}) after ${think} ms`); await p.waitForTimeout(think);
      await p.evaluate(how => { const s = st('candidates'), q = pos(); const g = new Chess(q.fen); let ms = g.moves({ verbose: true }).map(m => m.from + m.to + (m.promotion || ''));
        if (how === 'top') { const d = fenEval(q.fen); if (d) ms = d.lines.map(l => l.uci); }
        s.picks = ms.slice(0, 2).map(u => ({ uci: u, from: u.slice(0, 2), to: u.slice(2, 4), san: sanForUci(q.fen, u) })); render(); const c = document.getElementById('check'); c.disabled = false; c.click(); }, how);
      const ms = await waitReady(() => { const e = candidatesEval(pos(), st('candidates').picks); return e && !e.failed; }); await mark(`candidates review ready after ${ms} ms`); expect(`Candidate moves review (${how}, ${think} ms)`, ms, how === 'top' ? 300 : 3400);
      await p.waitForTimeout(1500); await dump(); await next();
    }
    await home();
    // Move selection
    await open('final');
    for (const think of [1000, 5000]) {
      const shown = await waitReady(() => !!document.getElementById('check'));
      expect('Move selection moves shown', shown, 3400); await mark(`final question (${await p.evaluate(()=>__tag(curPos.fen))}), moves shown after ${shown} ms, ranking for ${think} ms`); await p.waitForTimeout(think);
      await p.evaluate(() => { const s = st('final'); s.swapped = true; render(); document.getElementById('check').click(); });
      const ms = await waitReady(() => !!finalEval(pos(), finalMoves(pos()))); await mark(`final review ready after ${ms} ms`); expect(`Move selection review after ${think} ms`, ms, think > 3000 ? 300 : 3300);
      await p.waitForTimeout(1500); await dump(); await next();
    }
  }
  {
    await p.evaluate(() => { screen = 'home'; render(); }); await p.waitForTimeout(3000);
    await p.click('#routineBtn, .routine-card, [data-go="routine"]').catch(()=>{});
    for (let k = 0; k < 5; k++) {
      const a = await p.evaluate(() => screen);
      const shown = await waitReady(() => !!document.getElementById('check'));
      expect(`routine ${a} question shown`, shown, 3400); await mark(`routine ${a} (${await p.evaluate(()=>__tag(curPos.fen))}) question shown after ${shown} ms, answering after 2 s`); await p.waitForTimeout(2000);
      await p.evaluate(a => { const s = st(a), q = pos(); s.barMoved = true; s.swapped = true; if (a === 'imbalances') ASPECTS.forEach(x => { s.asp[x.key] = s.asp[x.key] || 1; });
        if (a === 'candidates') { const u = new Chess(q.fen).moves({ verbose: true })[0]; s.picks = [{ uci: u.from + u.to + (u.promotion || ''), from: u.from, to: u.to, san: u.san }]; }
        render(); const c = document.getElementById('check'); c.disabled = false; c.click(); }, a);
      const ms = await waitReady(() => !!document.getElementById('nextPos') && !document.querySelector('.actions-row.pending'));
      await mark(`routine ${a} review done after ${ms} ms; next is ${await p.evaluate(()=>{ const [t,i]=nextTarget(); return t+' '+__tag(posAt(t,i).fen); })}`);
      await p.waitForTimeout(1500); await dump(); await next();
    }
  }
  await dump();
  await b.close(); server.kill();
  if (errs.length) fails.push('page errors: ' + errs.join('; '));
  console.log(fails.length ? fails.map(f => 'FAIL ' + f).join('\n') : 'ok');
  process.exit(fails.length ? 1 : 0);
})();
