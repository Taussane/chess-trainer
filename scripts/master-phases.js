// Writes library/master-phases.json: where each master game's middlegame and endgame start (the half-move index, as
// the game review's chart and the beta Filter divide a game: gameDivision, Lichess's rules), { "g0": [mid, end] }
// (null when the game never gets there). Read by scripts/master-info.py into GAME_INFO (ph), so the Filter doesn't
// replay 721 games in the browser.
// Usage: NODE_PATH=$(npm root -g) node scripts/master-phases.js   (then python3 scripts/master-info.py and the build)
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const fs = require('fs'); const path = require('path');
const ROOT = path.join(__dirname, '..');
(async () => {
  const srv = spawn('python3', ['-m', 'http.server', '8921'], { cwd: ROOT, stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 800));
  const b = await chromium.launch(), p = await b.newPage();
  await p.route(/workers\.dev/, r => r.abort());
  await p.goto('http://localhost:8921/index.html'); await p.waitForTimeout(2000);
  const out = await p.evaluate(() => Object.fromEntries(Object.keys(GAME_MOVES).map(id => {
    const c = new Chess(), fens = [c.fen()]; for (const m of GAME_MOVES[id].split(' ').filter(Boolean)) { if (!c.move(m)) break; fens.push(c.fen()); }
    const d = gameDivision(fens); return [id, [d.mid, d.end]];
  })));
  fs.writeFileSync(path.join(ROOT, 'library/master-phases.json'), JSON.stringify(out));
  console.log(Object.keys(out).length, 'games');
  await b.close(); srv.kill();
})();
