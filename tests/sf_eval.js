// The JavaScript port of Stockfish 10's evaluation (app/sf-eval.js) against the engine's own
// `eval` tables (tests/sf-eval-ref.jsonl, recorded by scripts/sf-eval-ref.js): every term, both
// sides, middlegame and endgame, to the printed hundredth; the endings Stockfish evaluates on their
// own (and its quick exit when one side is far ahead) show as an all-zero table.
// Usage: node tests/sf_eval.js [ref.jsonl]
const SF = require('../app/sf-eval.js');
const path = process.argv[2] || require('path').join(__dirname, 'sf-eval-ref.jsonl');
const lines = require('fs').readFileSync(path, 'utf8').trim().split('\n').map(JSON.parse);
const fails = [];
for(const { fen, rows } of lines){
  const ref = Object.fromEntries(Object.entries(rows).map(([k, v])=>[k, v.split(' ')]));
  const zero = Object.values(ref).every(a=>a.every(x=>x==='----' || +x===0));
  let r; try{ r = SF.traceRows(fen); }catch(e){ fails.push(`${fen}: ${e.message}`); continue; }
  if(r.special || zero){ if(!(r.special && zero)) fails.push(`${fen}: special ${r.special}, engine ${zero ? 'all zero' : 'scored'}`); continue; }
  for(const [k, want] of Object.entries(ref)){
    const o = r[k], got = want[0]==='----' ? [null, null, null, null, ...o.t] : [...o.w, ...o.b, ...o.t];
    const i = want.findIndex((x, j)=>x!=='----' && +x!==+got[j]);
    if(i >= 0){ fails.push(`${fen}: ${k} ${want.join(' ')} vs ${got.join(' ')}`); break; }
  }
}
console.log(`${lines.length - fails.length}/${lines.length} positions match`);
if(fails.length){ console.log(fails.slice(0, 10).join('\n')); console.log('FAIL'); process.exit(1); }
console.log('ok');
