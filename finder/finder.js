// Position finder: games (PGN) -> training positions for each activity, by the rules in rules.js.
// Usage: node finder/finder.js <games.pgn> <out-dir> [filter-regex on "White - Black"]
// Engine: engine/stockfish (scripts/setup-stockfish.sh), or set STOCKFISH=/path/to/stockfish.
// Output: pools.json (what the app reads) and stats.json + a printed report.
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
async function analyse(fen, searchmoves){
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
const cache = {};
async function lines(fen){ return cache[fen] || (cache[fen] = await analyse(fen)); }

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

(async()=>{
  const [pgnFile, outDir, filter] = process.argv.slice(2);
  send('uci'); await until('uciok');
  send('setoption name Threads value '+R.ENGINE.threads); send('setoption name Hash value '+R.ENGINE.hash);
  send('isready'); await until('readyok');

  let games = splitGames(fs.readFileSync(pgnFile,'utf8'));
  if(filter) games = games.filter(g=>new RegExp(filter).test(header(g,'White')+' - '+header(g,'Black')));
  const pools = { analysis:new Map(), candidates:new Map(), final:new Map() };
  const stats = { version:R.VERSION, engine:R.ENGINE, games:[], positions:0, reasons:{}, analysis:{}, candidates:{}, final:{} };
  const why = r=>{ stats.reasons[r] = (stats.reasons[r]||0) + 1; };
  const tally = (o,k)=>{ o[k] = (o[k]||0) + 1; };
  const add = (pool, entry)=>{
    const ex = pool.get(entry.key);
    if(!ex){ pool.set(entry.key, { ...entry, occurrences:1 }); return; }
    ex.occurrences++;
    if(rand() < 1/ex.occurrences) pool.set(entry.key, { ...entry, occurrences:ex.occurrences });   // fair rotation
  };

  for(const [gi, g] of games.entries()){
    const toks = mainline(g), ch = new Chess(), hist = [];
    for(const t of toks){ const m = ch.move(t) || ch.move(t,{sloppy:true}); if(!m) break; hist.push(m); }
    const fens = [new Chess().fen()]; { const r = new Chess(); hist.forEach(m=>{ r.move(m.san); fens.push(r.fen()); }); }
    const surname = s=>s.split(',')[0].trim();
    const game = { id:'g'+gi, white:header(g,'White'), black:header(g,'Black'), event:header(g,'Event'), year:header(g,'Date').slice(0,4), result:header(g,'Result') };
    game.title = surname(game.white)+' – '+surname(game.black);
    const decisive = game.result==='1-0' || game.result==='0-1';
    const div = divide(fens);
    const gs = { ...game, plies:hist.length, middlegame:div.mid, endgame:div.end, checked:0, passedGeneral:0, analysis:0, candidates:0, final:0 };
    stats.games.push(gs);
    process.stderr.write(`${game.title}: ${hist.length} plies, middlegame ply ${div.mid}, endgame ply ${div.end}\n`);

    // General rules, per ply (position before hist[ply] is played).
    const general = {};   // ply -> { ok, ls, reason }
    for(let ply=0; ply<hist.length; ply++){
      const fen = fens[ply], c = new Chess(fen), moveNo = +fen.split(' ')[5];
      if(moveNo < R.GENERAL.minMove || moveNo > R.GENERAL.maxMove) continue;
      gs.checked++; stats.positions++;
      let reason = null;
      const prev = hist[ply-1];
      if(c.moves().length < R.GENERAL.minLegalMoves) reason = 'fewer than 4 legal moves';
      else if(prev && prev.captured && c.moves({verbose:true}).some(m=>m.to===prev.to && m.captured)) reason = 'mid-exchange';
      let ls = null;
      if(!reason){
        ls = await lines(fen);
        if(ls[0].mate!=null && ls[0].mate>0){
          const before = await lines(fens[ply-1]);   // the opponent, one half-move earlier
          if(before[0].mate!=null && before[0].mate<0) reason = 'mate already under way';
        }
      }
      if(reason){ why(reason); general[ply] = { ok:false, reason }; continue; }
      gs.passedGeneral++;
      general[ply] = { ok:true, ls };
    }
    const base = ply=>{
      const fen = fens[ply], m = hist[ply], prev = hist[ply-1];
      return { key:posKey(fen), fen, game:game.id, title:game.title, event:game.event, year:game.year, ply,
               moveNo:+fen.split(' ')[5], side:fen.split(' ')[1],
               last: prev ? [prev.from, prev.to] : null,
               hist:{ uci:m.from+m.to+(m.promotion||''), san:m.san, from:m.from, to:m.to } };
    };

    // ----- Board analysis: middlegame start, then every 4 full moves, up to the endgame start.
    if(decisive && div.mid>=0){
      const last = div.end>=0 ? div.end : hist.length-1;
      let target = div.mid;
      while(target <= last){
        let kept = -1;
        for(let ply=target; ply<=Math.min(target+R.ANALYSIS.retryPlies, last); ply++){
          const gen = general[ply]; if(!gen || !gen.ok) continue;
          const c = new Chess(fens[ply]);
          if(R.ANALYSIS.notInCheck && c.in_check()){ tally(stats.analysis,'rejected: in check'); continue; }
          if(Math.abs(materialDiff(c)) > R.ANALYSIS.maxMaterialDiff){ tally(stats.analysis,'rejected: material'); continue; }
          const top = gen.ls[0], whiteCp = (fens[ply].split(" ")[1]==="w" ? 1 : -1) * moverScore(top);
          add(pools.analysis, { ...base(ply), metrics:{ evalWhite: whiteCp, mate: top.mate ?? null } });
          gs.analysis++; kept = ply; break;
        }
        target = (kept>=0 ? kept : target) + R.ANALYSIS.spacingPlies;
      }
    } else if(!decisive) tally(stats.analysis, 'games skipped: draw');

    // ----- Candidate moves and Final choice, ply by ply.
    let lastCand = -99, lastFinal = -99;
    for(let ply=0; ply<hist.length; ply++){
      const gen = general[ply]; if(!gen || !gen.ok) continue;
      const ls = gen.ls, best = winPct(ls[0].cp, ls[0].mate);
      const drop = l=>best - winPct(l.cp, l.mate);
      const top5 = ls.slice(0, R.CANDIDATES.trapTopN);

      // Candidate moves
      if(top5.some(l=>drop(l) >= R.CANDIDATES.trapMinDrop)){
        if(ply - lastCand >= R.CANDIDATES.spacingPlies){
          const decent = top5.filter(l=>drop(l) < 10).length;
          add(pools.candidates, { ...base(ply), metrics:{ decentMoves: decent } });
          gs.candidates++; lastCand = ply;
        } else tally(stats.candidates, 'rejected: spacing');
      } else tally(stats.candidates, 'rejected: no trap in top 5');

      // Final choice
      // The game move is always judged inside ONE search with the top 5: the discovery search when
      // it is already among them, otherwise one combined search over the top 5 + the game move.
      const gm = hist[ply], gmUci = gm.from+gm.to+(gm.promotion||'');
      const cand = top5.some(l=>l.uci===gmUci) ? top5
                 : (await analyse(fens[ply], [...top5.map(l=>l.uci), gmUci])).slice().sort((a,b)=>winPct(b.cp,b.mate)-winPct(a.cp,a.mate));
      const gmLine = cand.find(l=>l.uci===gmUci);
      if(!gmLine){ tally(stats.final, 'rejected: search lost the game move'); continue; }
      const cBest = winPct(cand[0].cp, cand[0].mate), cDrop = l=>cBest - winPct(l.cp, l.mate);
      const grades = new Set(cand.map(l=>gradeOf(cDrop(l))));
      if(grades.size < R.FINAL.minGrades){ tally(stats.final, 'rejected: fewer than 3 grades'); continue; }
      // Pick: best, game move, then new grades best to worst, then least-represented grades.
      const picks = [cand[0]]; if(gmLine!==cand[0]) picks.push(gmLine);
      const have = ()=>picks.map(l=>gradeOf(cDrop(l)));
      for(const l of cand){ if(picks.length>=4) break; if(!picks.includes(l) && !have().includes(gradeOf(cDrop(l)))) picks.push(l); }
      while(picks.length<4){
        const rest = cand.filter(l=>!picks.includes(l)); if(!rest.length) break;
        const count = g=>have().filter(x=>x===g).length;
        rest.sort((a,b)=>count(gradeOf(cDrop(a))) - count(gradeOf(cDrop(b))));   // stable: best first on ties
        picks.push(rest[0]);
      }
      if(picks.length<4){ tally(stats.final, 'rejected: fewer than 4 moves'); continue; }
      // One combined search over exactly those 4 moves (as the app does), then the random-order check.
      const four = await analyse(fens[ply], picks.map(l=>l.uci));
      const cp = {}; four.forEach(l=>{ cp[l.uci] = moverScore(l); });
      if(Object.keys(cp).length<4){ tally(stats.final, 'rejected: search lost a move'); continue; }
      // Re-check the grade rule on the four moves as they will be shown (after the combined search).
      const b4 = winPct(four[0].cp, four[0].mate), g4 = four.map(l=>gradeOf(b4 - winPct(l.cp, l.mate)));
      if(new Set(g4).size < R.FINAL.minGrades){ tally(stats.final, 'rejected: fewer than 3 grades among the 4 shown'); continue; }
      const rnd = randomAccuracy(cp);
      if(rnd > R.FINAL.maxRandomAccuracy){ tally(stats.final, 'rejected: random order scores > 60%'); continue; }
      tally(stats.final, 'eligible before spacing');
      if(ply - lastFinal < R.FINAL.spacingPlies){ tally(stats.final, 'rejected: spacing'); continue; }
      lastFinal = ply;
      add(pools.final, { ...base(ply), final:{ moves: picks.map(l=>l.uci) },
        metrics:{ randomAccuracy: Math.round(rnd), grades: g4, gameMoveGrade: gradeOf(cDrop(gmLine)) } });
      gs.final++;
    }
  }

  const out = { version:R.VERSION, engine:'Stockfish 16.1, depth '+R.ENGINE.depth, generated:new Date().toISOString(),
    pools: Object.fromEntries(Object.entries(pools).map(([k,m])=>[k, [...m.values()]])) };
  fs.mkdirSync(outDir, {recursive:true});
  fs.writeFileSync(path.join(outDir,'pools.json'), JSON.stringify(out, null, 1));
  fs.writeFileSync(path.join(outDir,'stats.json'), JSON.stringify(stats, null, 1));
  console.log(JSON.stringify({ counts: Object.fromEntries(Object.entries(out.pools).map(([k,v])=>[k,v.length])), stats }, null, 1));
  send('quit');
})();
