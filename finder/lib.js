// Shared tools of the position finders (finder.js for the library, own.js for a player's games):
// PGN reading, the engine with its saved results, game phases, grades, and sharing positions out.
const fs = require('fs'), path = require('path');
const { spawn } = require('child_process');
const { Chess } = require('../vendor/chess.js/chess.js');
const R = require(process.env.RULES||'./rules.js');

// ---------- PGN ----------
function splitGames(txt){ return txt.split(/(?=\[Event )/).filter(g=>g.includes('[White')); }
function header(g,k){ const m = g.match(new RegExp('\\['+k+' "([^"]*)"\\]')); return m ? m[1] : ''; }
function mainline(g){
  const body = g.replace(/^\[.*\]\s*$/mg,'');
  let out='', inC=false, depthV=0;
  for(const ch of body){
    if(ch==='{'){ inC=true; continue; } if(ch==='}'){ inC=false; continue; } if(inC) continue;
    if(ch==='('){ depthV++; continue; } if(ch===')'){ depthV--; continue; } if(depthV>0) continue;
    out+=ch;
  }
  out = out.replace(/\$\d+/g,'').replace(/\d+\.(\.\.)?/g,' ').replace(/[!?]+/g,'').replace(/0-0-0/g,'O-O-O').replace(/0-0/g,'O-O');
  return out.split(/\s+/).filter(t=>t && !/^(1-0|0-1|1\/2-1\/2|\*)$/.test(t));
}

// ---------- Engine (UCI) ----------
const SF = process.env.STOCKFISH || path.join(__dirname, '../engine/stockfish');
const sf = spawn(SF); let buf = '', waiter = null;
sf.stdout.on('data', d=>{ buf += d; if(waiter && buf.includes(waiter.t)){ const w = waiter; waiter = null; const o = buf; buf = ''; w.r(o); } });
const send = s=>sf.stdin.write(s+'\n');
const until = t=>new Promise(r=>{ waiter = {t, r}; if(buf.includes(t)){ waiter = null; const o = buf; buf = ''; r(o); } });
const winPct = (cp, mate)=> mate!=null ? (mate>0 ? 100 : 0) : 50 + 50*(2/(1+Math.exp(-0.00368208*cp)) - 1);
const moverScore = l=> l.mate!=null ? (l.mate>0 ? 1000 : -1000) : Math.max(-1000, Math.min(1000, l.cp));
async function search(fen, searchmoves){
  const mpv = searchmoves ? searchmoves.length : R.ENGINE.multipv;
  send('setoption name MultiPV value '+mpv); send('position fen '+fen);
  send('go depth '+R.ENGINE.depth + (searchmoves ? ' searchmoves '+searchmoves.join(' ') : ''));
  const out = await until('bestmove'); const L = {};
  out.split('\n').forEach(l=>{
    if(!l.startsWith('info') || !l.includes(' pv ')) return;
    const r = +(l.match(/multipv (\d+)/)||[0,1])[1];
    const cp = l.match(/score cp (-?\d+)/), mt = l.match(/score mate (-?\d+)/);
    L[r] = { cp: cp ? +cp[1] : null, mate: mt ? +mt[1] : null, uci: l.match(/ pv (\S+)/)[1] };
  });
  return Object.values(L).sort((a,b)=>winPct(b.cp,b.mate) - winPct(a.cp,a.mate));   // mover's view, best first
}
// Every search is kept on disk (one JSON line each), keyed by depth, MultiPV, position and move
// restriction, so a re-run (new rules, more games, or after an interruption) only searches what
// it hasn't seen. Delete the file to start fresh.
const CACHE_FILE = process.env.CACHE || path.join(__dirname, '.cache', 'searches.jsonl');
const cache = new Map();
fs.mkdirSync(path.dirname(CACHE_FILE), {recursive:true});
if(fs.existsSync(CACHE_FILE)) fs.readFileSync(CACHE_FILE,'utf8').split('\n').forEach(l=>{ if(l){ try{ const [k,v] = JSON.parse(l); cache.set(k,v); }catch(e){} } });
let searched = 0, reused = 0;
async function analyse(fen, searchmoves){
  const k = [R.ENGINE.depth, searchmoves ? searchmoves.length : R.ENGINE.multipv, fen, (searchmoves||[]).join(' ')].join('|');
  if(cache.has(k)){ reused++; return cache.get(k); }
  const v = await search(fen, searchmoves); searched++;
  cache.set(k, v); fs.appendFileSync(CACHE_FILE, JSON.stringify([k,v])+'\n');
  return v;
}
async function lines(fen){ return analyse(fen); }

// ---------- Board helpers ----------
const VAL = { p:1, n:3, b:3, r:5, q:9, k:0 };
function pieces(ch){ const out = []; ch.board().forEach((row,ri)=>row.forEach((c,fi)=>{ if(c) out.push({ ...c, file:fi, rank:7-ri }); })); return out; }
function materialDiff(ch){ return pieces(ch).reduce((t,p)=>t + (p.color==='w' ? 1 : -1)*VAL[p.type], 0); }
// Lichess Divider (scalachess core/Divider.scala), ported as is.
function majorsAndMinors(ps){ return ps.filter(p=>p.type!=='k' && p.type!=='p').length; }
function backrankSparse(ps){ return ps.filter(p=>p.color==='w' && p.rank===0).length < 4 || ps.filter(p=>p.color==='b' && p.rank===7).length < 4; }
function score(y, white, black){
  switch(white){
    case 0: switch(black){ case 1: return 1+y; case 2: return y<6 ? 2+(6-y) : 0; case 3: case 4: return y<7 ? 3+(7-y) : 0; default: return 0; }
    case 1: switch(black){ case 0: return 1+(8-y); case 1: return 5+Math.abs(4-y); case 2: return 4+(7-y); case 3: return 5+(7-y); default: return 0; }
    case 2: switch(black){ case 0: return y>2 ? 2+(y-2) : 0; case 1: return 4+(y-1); case 2: return 7; default: return 0; }
    case 3: switch(black){ case 0: return y>1 ? 3+(y-1) : 0; case 1: return 5+(y-1); default: return 0; }
    case 4: switch(black){ case 0: return y>1 ? 3+(y-1) : 0; default: return 0; }
    default: return 0;
  }
}
function mixedness(ps){
  let acc = 0;
  for(let y=0; y<7; y++) for(let x=0; x<7; x++){
    const inR = p=>p.file>=x && p.file<=x+1 && p.rank>=y && p.rank<=y+1;
    acc += score(y+1, ps.filter(p=>p.color==='w' && inR(p)).length, ps.filter(p=>p.color==='b' && inR(p)).length);
  }
  return acc;
}
function divide(fens){
  const boards = fens.map(f=>pieces(new Chess(f)));
  const mid = boards.findIndex(ps=>majorsAndMinors(ps)<=10 || backrankSparse(ps) || mixedness(ps)>150);
  const end = mid>=0 ? boards.findIndex(ps=>majorsAndMinors(ps)<=6) : -1;
  return { mid: mid>=0 && (end<0 || mid<end) ? mid : -1, end };
}

// ---------- Grades & scoring (same as the app) ----------
function gradeOf(drop){ let g = R.GRADES[0][0]; R.GRADES.forEach(([name, min])=>{ if(drop>=min) g = name; }); return g; }
function dubiousDistance(bestCp){
  const k = 0.00368208, target = winPct(bestCp, null) - 10;
  if(target <= 0.5) return 1000;
  const w = target/100; return bestCp - Math.log(w/(1-w))/k;
}
function rankAccuracy(order, cp){        // order: ids; cp: id -> mover-view centipawns
  const left = order.slice().sort((a,b)=>cp[b]-cp[a]), cap = dubiousDistance(cp[left[0]]);
  let got = 0;
  order.forEach((id,i)=>{ if(i<R.FINAL.weights.length) got += R.FINAL.weights[i]*(1 - Math.min(cap, Math.max(0, cp[left[0]]-cp[id]))/cap); left.splice(left.indexOf(id),1); });
  return 100*got / R.FINAL.weights.reduce((t,w)=>t+w,0);
}
function perms(a){ return a.length<2 ? [a] : a.flatMap((x,i)=>perms([...a.slice(0,i), ...a.slice(i+1)]).map(p=>[x,...p])); }
const randomAccuracy = cp=>{ const ps = perms(Object.keys(cp)); return ps.reduce((t,p)=>t+rankAccuracy(p,cp),0)/ps.length; };

// Seeded random, so the same run gives the same rotation choices.
let seed = [...R.VERSION].reduce((h,c)=>(h*31 + c.charCodeAt(0))>>>0, 7);
const rand = ()=>((seed = (seed*1664525 + 1013904223)>>>0) / 4294967296);
const posKey = fen=>fen.split(' ').slice(0,4).join(' ');


// ---------- Choosing each exercise's positions ----------
// items: [{ game, ply, key, options:Set('analysis'|'candidates'|'final'), anchor, ... }]. A position
// goes into EVERY exercise it qualifies for (no exclusivity between exercises). Within one
// exercise: Board analysis anchors (middlegame and endgame starts) first, then each game in move
// order, keeping that exercise's spacing (half-moves from its other positions of the same game);
// a position reached in several games is kept once. spacing: { analysis:7, candidates:3, final:0 }.
function choosePools(items, spacing){
  const pools = { analysis:[], candidates:[], final:[] };
  const byOrder = (a,b)=>String(a.game).localeCompare(String(b.game), undefined, {numeric:true}) || a.ply - b.ply;
  for(const a of Object.keys(pools)){
    const plies = {}, keys = new Set();
    const near = it=>(plies[it.game] || []).some(p=>Math.abs(p-it.ply) < (spacing[a]||0));
    const take = it=>{ if(keys.has(it.key) || near(it)) return; (plies[it.game] = plies[it.game] || []).push(it.ply); keys.add(it.key); pools[a].push({ ...it, act:a }); };
    const mine = items.filter(it=>it.options.has(a)).sort(byOrder);
    if(a==='analysis') mine.filter(it=>it.anchor).forEach(take);
    mine.forEach(take);
    pools[a].sort(byOrder);
  }
  return pools;
}

module.exports = { fs, path, Chess, R, splitGames, header, mainline, send, until, winPct, moverScore, analyse, lines,
  stats: ()=>({ searched, reused }), pieces, materialDiff, divide, gradeOf, rankAccuracy, randomAccuracy, rand, posKey, choosePools };
