// Lists the Position evaluation master positions left out of Imbalance reading: those where the
// engine's evaluation and the imbalances' total are 2 squares of the bar apart or more (tactics take
// the evaluation away from them). Writes the list into app/index.html (/*IMBALANCE_SKIP*/).
// Needs Stockfish.js 10 for Node (the engine the app runs): STOCKFISH_JS=/path/to/stockfish.js
//   node scripts/imbalance-skip.js
const fs = require('fs'), path = require('path');
const APP = path.join(__dirname, '../app/index.html');
const html = fs.readFileSync(APP, 'utf8');
const POOLS = JSON.parse(html.match(/\/\*POOLS\*\/(.*?)\/\*END POOLS\*\//s)[1]);
const src = html.match(/\/\/ ================= Key aspects[\s\S]*?(?=let aspectsStore)/)[0];
const { parseAspects, ASPECTS } = new Function(src + '; return { parseAspects, ASPECTS };')();
const MS = 1200, FAR = 25;   // the app's search time; 2 squares of the bar, in winning chances
const winPct = cp=>Math.max(1, Math.min(99, 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1)));
const sf = require(process.env.STOCKFISH_JS || 'stockfish.js')();
let buf = [], waiter = null;
sf.onmessage = l=>{ if(typeof l!=='string') l = l.data; buf.push(...l.split('\n')); if(waiter) waiter(); };
const until = re=>new Promise(res=>{ const c = ()=>{ const i = buf.findIndex(x=>re.test(x)); if(i>=0){ const o = buf.splice(0, i+1); waiter = null; res(o); } }; waiter = c; c(); });
(async()=>{
  sf.postMessage('uci'); await until(/^uciok/);
  const skip = [];
  for(const p of POOLS.analysis){
    sf.postMessage('ucinewgame'); sf.postMessage('position fen ' + p.fen); sf.postMessage('go movetime ' + MS);
    let score = null;
    for(const l of await until(/^bestmove/)){ if(/bound/.test(l)) continue; const m = l.match(/score (cp|mate) (-?\d+)/); if(m) score = m[1]==='cp' ? +m[2] : (+m[2] > 0 ? 1e5 : -1e5); }
    if(p.side==='b') score = -score;
    sf.postMessage('position fen ' + p.fen); sf.postMessage('eval');
    const a = parseAspects(await until(/^Total evaluation/), p.fen);
    if(!a) continue;
    const sum = ASPECTS.reduce((t, x)=>t + a[x.key], 0) * 100;
    if(Math.abs(winPct(sum) - (Math.abs(score) >= 1e5 ? (score > 0 ? 99 : 1) : winPct(score))) >= FAR) skip.push(p.key);
    process.stderr.write('.');
  }
  fs.writeFileSync(APP, fs.readFileSync(APP, 'utf8').replace(/\/\*IMBALANCE_SKIP\*\/.*?\/\*END IMBALANCE_SKIP\*\//s, '/*IMBALANCE_SKIP*/' + JSON.stringify(skip) + '/*END IMBALANCE_SKIP*/'));
  console.log(`\n${skip.length} of ${POOLS.analysis.length} positions left out of Imbalance reading`);
  process.exit(0);
})();
