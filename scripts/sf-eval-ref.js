// Records Stockfish.js 10's `eval` tables for a list of positions, as the reference for the
// JavaScript port (app/sf-eval.js).
// Usage: node scripts/sf-eval-ref.js <stockfish.js> <fens.txt> <out.jsonl>
// (stockfish.js: the npm package stockfish@10.0.2, the build the app loads from cdnjs)
const [, , sfPath, fensPath, outPath] = process.argv;
const sf = require(require('path').resolve(sfPath))();
let buf = [], waiter = null;
sf.onmessage = l=>{ if(typeof l!=='string') l = l.data; buf.push(l); if(waiter) waiter(); };
const until = re=>new Promise(res=>{ const chk = ()=>{ const i = buf.findIndex(x=>re.test(x)); if(i >= 0){ const out = buf.splice(0, i + 1); waiter = null; res(out); } }; waiter = chk; chk(); });
(async()=>{
  sf.postMessage('uci'); await until(/^uciok/);
  const fens = require('fs').readFileSync(fensPath, 'utf8').trim().split('\n'), out = [];
  for(const fen of fens){
    sf.postMessage('position fen ' + fen); sf.postMessage('eval');
    const rows = {};
    for(const l of await until(/^Total evaluation/)){
      const m = l.match(/^\s*([A-Za-z ]+?)\s*\|(.*)$/);
      if(!m || /Term/.test(m[1]) || m[1]==='Variant') continue;
      const nums = m[2].match(/-?\d+\.\d+|----/g); if(nums) rows[m[1]] = nums.join(' ');
    }
    out.push(JSON.stringify({ fen, rows }));
  }
  require('fs').writeFileSync(outPath, out.join('\n') + '\n'); process.exit(0);
})();
