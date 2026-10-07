// How well does "no thinking at all" score, with the app's own scoring? Per exercise:
//  - Board analysis: always answering 50/50 (the cursor left in the middle);
//  - Candidate moves: one move picked at random among the engine's top 5;
//  - Final choice: the four moves left in a random order (average of all 24 orders).
// Run on the saved depth-18 searches (finder/.cache), for any pools.json (masters or own games):
//   node finder/baseline.js data/pools.json [label]
// The scoring copies the app's: evalAccuracyPct, pickAccuracyPct, rankAccuracyPct, pickFinalUcis.
const fs = require('fs'), path = require('path');
const [file, label] = process.argv.slice(2);
const pools = JSON.parse(fs.readFileSync(file, 'utf8')).pools;

// Saved searches: key "[engine|]depth|multipv|fen|searchmoves" -> lines (mover's view).
const cache = new Map();
for (const l of fs.readFileSync(path.join(__dirname, '.cache', 'searches.jsonl'), 'utf8').split('\n')) {
  if (!l) continue;
  const [k, v] = JSON.parse(l);
  cache.set(k.replace(/^Stockfish 16\.1\|/, ''), v);
}
const top5 = fen => cache.get(`18|5|${fen}|`);
const restricted = (fen, ucis) => cache.get(`18|${ucis.length}|${fen}|${ucis.join(' ')}`);

// ---- The app's scoring ----
const winPercent = (cp, mate) => mate != null ? (mate > 0 ? 100 : 0) : Math.max(0, Math.min(100, 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1)));
const moverScore = l => l.mate != null ? (l.mate > 0 ? 1000 : -1000) : Math.max(-1000, Math.min(1000, l.cp));
const sortBest = ls => ls.slice().sort((a, b) => winPercent(b.cp, b.mate) - winPercent(a.cp, a.mate));
function dubiousDistance(bestCp) { const k = 0.00368208, target = winPercent(bestCp, null) - 10; if (target <= 0.5) return 1000; const w = target / 100; return bestCp - Math.log(w / (1 - w)) / k; }
const evalAccuracyPct = (guess, truePct) => Math.max(0, Math.round(100 * (1 - Math.abs(guess - truePct) / 49)));
function pickAccuracyPct(pickUcis, lines) {
  const n = pickUcis.length, picks = pickUcis.map(u => lines.find(l => l.uci === u)).filter(Boolean);
  const bestCp = moverScore(lines[0]), cap = dubiousDistance(bestCp);
  const dist = l => Math.min(cap, Math.max(0, bestCp - moverScore(l)));
  const r1 = winPercent(lines[0].cp, lines[0].mate);
  const good = lines.slice(0, n).filter(l => r1 - winPercent(l.cp, l.mate) < 10);
  const zero = n * cap, full = good.reduce((t, l) => t + dist(l), 0), yours = picks.reduce((t, l) => t + dist(l), 0) + (n - picks.length) * cap;
  if (zero - full <= 0) return yours <= full ? 100 : 0;
  return Math.round(100 * Math.max(0, Math.min(1, (zero - yours) / (zero - full))));
}
function rankAccuracyPct(ids, cp) {
  const left = ids.slice().sort((a, b) => cp[b] - cp[a]), cap = dubiousDistance(cp[left[0]]), W = [0.5, 0.3, 0.2];
  let got = 0;
  ids.forEach((id, i) => { if (i < 3) got += W[i] * (1 - Math.min(cap, Math.max(0, cp[left[0]] - cp[id])) / cap); left.splice(left.indexOf(id), 1); });
  return Math.round(100 * got);
}
const perms = a => a.length < 2 ? [a] : a.flatMap((x, i) => perms([...a.slice(0, i), ...a.slice(i + 1)]).map(p => [x, ...p]));
function gradeOf(drop) { return drop >= 30 ? 'Blunder' : drop >= 20 ? 'Mistake' : drop >= 10 ? 'Dubious' : drop >= 3 ? 'Ok' : 'Good'; }
function pickFinalUcis(gm, lines) {   // the app's rule (best, game move, new grades down the list, then least-represented)
  const best = winPercent(lines[0].cp, lines[0].mate), g = l => l ? gradeOf(best - winPercent(l.cp, l.mate)) : 'unknown';
  const picks = [], add = (u, gr) => { if (!picks.some(m => m.u === u)) picks.push({ u, gr }); }, have = () => picks.map(m => m.gr);
  add(lines[0].uci, 'Good'); add(gm, g(lines.find(l => l.uci === gm)));
  for (const l of lines) { if (picks.length >= 4) break; if (!have().includes(g(l))) add(l.uci, g(l)); }
  const BAD = ['Dubious', 'Mistake', 'Blunder'], repeats = l => BAD.includes(g(l)) && have().includes(g(l));
  while (picks.length < 4) {
    const left = lines.filter(l => !picks.some(m => m.u === l.uci)), rest = left.some(l => !repeats(l)) ? left.filter(l => !repeats(l)) : left;
    if (!rest.length) break;
    const count = gr => have().filter(x => x === gr).length;
    rest.sort((a, b) => count(g(a)) - count(g(b))); add(rest[0].uci, g(rest[0]));
  }
  return picks.map(m => m.u);
}

// ---- Baselines ----
const avg = xs => xs.length ? xs.reduce((t, x) => t + x, 0) / xs.length : NaN;
const out = { analysis: [], candidates: [], final: [] }, missing = { analysis: 0, candidates: 0, final: 0 };
for (const p of pools.analysis) {
  const ls = top5(p.fen); if (!ls) { missing.analysis++; continue; }
  const l = sortBest(ls)[0], white = p.side === 'w' ? 1 : -1;
  const pct = Math.max(1, Math.min(99, winPercent(l.cp != null ? white * l.cp : null, l.mate != null ? white * l.mate : null)));
  out.analysis.push(evalAccuracyPct(50, pct));
}
for (const p of pools.candidates) {
  const ls = top5(p.fen); if (!ls) { missing.candidates++; continue; }
  const lines = sortBest(ls).slice(0, 5);
  out.candidates.push(avg(lines.map(l => pickAccuracyPct([l.uci], lines))));
}
for (const p of pools.final) {
  const ls = top5(p.fen); if (!ls) { missing.final++; continue; }
  let lines = sortBest(ls).slice(0, 5); const gm = p.hist.uci;
  if (!lines.some(l => l.uci === gm)) { const c = restricted(p.fen, [...lines.map(l => l.uci), gm]); if (!c) { missing.final++; continue; } lines = sortBest(c); }
  const four = pickFinalUcis(gm, lines), cp = {}; four.forEach(u => { const l = lines.find(x => x.uci === u); cp[u] = moverScore(l); });
  out.final.push(avg(perms(four).map(o => rankAccuracyPct(o, cp))));
}
const fmt = xs => `${avg(xs).toFixed(0)}% average (${xs.length} positions; half of them under ${[...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)].toFixed(0)}%)`;
console.log(`${label || file}`);
console.log(`  Board analysis, always 50/50:         ${fmt(out.analysis)}`);
console.log(`  Candidate moves, one random top-5 move: ${fmt(out.candidates)}`);
console.log(`  Final choice, random order:            ${fmt(out.final)}`);
console.log(`  Final choice positions where a random order scores over 60%: ${out.final.filter(x => x > 60).length}`);
if (Object.values(missing).some(Boolean)) console.log('  (no saved search for', missing, ')');
