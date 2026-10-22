// Runs the master-game Stockfish searches on a faster computer, using all its cores.
// It takes the World Championship games not yet in the library (library/wch-matches-all.pgn
// minus library/gm-classics.pgn), splits them into one share per 2 cores, and runs the finder
// on each share at the same time (same depth, MultiPV and threads as finder/rules.js).
// The result is ONE file, masters-searches.jsonl (in the repository folder): the searches only,
// to merge into finder/.cache/searches.jsonl, after which the finder runs on all games in minutes.
// It can be stopped and started again: finished searches are kept and skipped.
//
// Needs Node.js 18+ and Stockfish 19 (official build for your computer, from
// https://github.com/official-stockfish/Stockfish/releases/tag/sf_19).
// Usage: node scripts/masters-batch.js /path/to/stockfish
const fs = require('fs'), path = require('path'), os = require('os');
const { spawn } = require('child_process');
const ROOT = path.resolve(__dirname, '..');
const sf = process.argv[2] || process.env.STOCKFISH;
if(!sf || !fs.existsSync(sf)){ console.error('Give the path to Stockfish 19: node scripts/masters-batch.js /path/to/stockfish'); process.exit(1); }

const split = t=>t.trim().split(/\n\s*\n(?=\[Event )/).map(g=>g.trim()).filter(Boolean);
const moves = g=>(g.split(/\n\s*\n/)[1] || '').replace(/\s+/g, ' ').trim();
const have = new Set(split(fs.readFileSync(path.join(ROOT, 'library/gm-classics.pgn'), 'utf8')).map(moves));
const rest = split(fs.readFileSync(path.join(ROOT, 'library/wch-matches-all.pgn'), 'utf8')).filter(g=>!have.has(moves(g)));

const jobs = Math.max(1, Math.floor(os.cpus().length / 2));
const work = path.join(ROOT, 'masters-work'); fs.mkdirSync(work, { recursive:true });
console.log(`${rest.length} games, ${jobs} at a time (${os.cpus().length} cores). This takes hours; leave the computer awake.`);

const done = Array(jobs).fill(0), sizes = Array(jobs).fill(0);
const runs = [];
for(let j=0; j<jobs; j++){
  const share = rest.filter((g,i)=>i % jobs === j); sizes[j] = share.length;
  if(!share.length) continue;
  fs.writeFileSync(path.join(work, `share-${j}.pgn`), share.join('\n\n') + '\n');
  runs.push(new Promise((resolve, reject)=>{
    const p = spawn(process.execPath, [path.join(ROOT, 'finder/finder.js'), path.join(work, `share-${j}.pgn`), path.join(work, `out-${j}`)],
      { env:{ ...process.env, STOCKFISH:sf, CACHE:path.join(work, `searches-${j}.jsonl`) } });
    p.stderr.on('data', d=>{ const m = String(d).match(/\[(\d+)\/\d+\]/g); if(m){ done[j] = +m.pop().match(/\d+/)[0] - 1; report(); } });
    p.on('exit', c=>c === 0 ? (done[j] = sizes[j], report(), resolve()) : reject(new Error(`share ${j} stopped (code ${c})`)));
  }));
}
const t0 = Date.now();
function report(){
  const d = done.reduce((a,b)=>a+b, 0), min = (Date.now()-t0)/60000;
  const left = d ? Math.round(min/d*(rest.length-d)) : '?';
  process.stdout.write(`\r${d}/${rest.length} games done, ${Math.round(min)} min so far, about ${left} min left   `);
}
Promise.all(runs).then(()=>{
  const out = path.join(ROOT, 'masters-searches.jsonl');
  fs.writeFileSync(out, '');
  for(let j=0; j<jobs; j++){ const f = path.join(work, `searches-${j}.jsonl`); if(fs.existsSync(f)) fs.appendFileSync(out, fs.readFileSync(f)); }
  console.log(`\nDone. Send this file: ${out} (${Math.round(fs.statSync(out).size/1e6)} MB)`);
}).catch(e=>{ console.error('\n' + e.message + '. Run the same command again to continue.'); process.exit(1); });
