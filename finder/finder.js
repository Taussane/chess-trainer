// Position finder: library games (PGN) -> training positions for each exercise, by rules.js.
// Usage: node finder/finder.js <games.pgn> <out-dir> [filter-regex on "White - Black"]
// Engine: engine/stockfish (scripts/setup-stockfish.sh), or set STOCKFISH=/path/to/stockfish.
// Output: pools.json (copied into the app by inject.py) and stats.json.
//
// 1. Every position is checked against each exercise's rules and keeps every exercise it
//    qualifies for, in ONE pass over the game's half-moves (each position analysed once, early
//    exits on the general rules). Board analysis then marks two anchors per game: the middlegame
//    start and the endgame start (or the next half-move that qualifies, up to 3).
// 2. Each exercise keeps every position it qualifies for (lib.choosePools), keeping its spacing
//    within a game: Board analysis 7 half-moves (anchors first), Candidate moves 7, Final choice none. A position
//    can be in several exercises.
const L = require('./lib.js');
const { fs, path, Chess, R, header, mainline, analyse, lines, winPct, moverScore, gradeOf, randomAccuracy, posKey } = L;

(async()=>{
  const [pgnFile, outDir, filter] = process.argv.slice(2);
  await L.start();

  let games = L.splitGames(fs.readFileSync(pgnFile,'utf8'));
  if(filter) games = games.filter(g=>new RegExp(filter).test(header(g,'White')+' - '+header(g,'Black')));
  const stats = { version:R.VERSION, engine:R.ENGINE, games:[], positions:0, reasons:{}, eligible:{ analysis:0, candidates:0, final:0, anchors:0 }, analysis:{}, candidates:{}, final:{} };
  const why = r=>{ stats.reasons[r] = (stats.reasons[r]||0) + 1; };
  const tally = (o,k)=>{ o[k] = (o[k]||0) + 1; };
  const items = [];

  for(const [gi, g] of games.entries()){
    const toks = mainline(g), ch = new Chess(), hist = [];
    for(const t of toks){ const m = ch.move(t) || ch.move(t,{sloppy:true}); if(!m) break; hist.push(m); }
    const fens = [new Chess().fen()]; { const r = new Chess(); hist.forEach(m=>{ r.move(m.san); fens.push(r.fen()); }); }
    const surname = s=>s.split(',')[0].trim();
    const game = { id:'g'+gi, white:header(g,'White'), black:header(g,'Black'), event:header(g,'Event'), year:header(g,'Date').slice(0,4), result:header(g,'Result') };
    game.title = surname(game.white)+' – '+surname(game.black);
    const decisive = !R.ANALYSIS.decisiveGamesOnly || game.result==='1-0' || game.result==='0-1';
    const div = L.divide(fens);
    const gs = { ...game, sans:hist.map(m=>m.san), plies:hist.length, middlegame:div.mid, endgame:div.end, checked:0, passedGeneral:0, analysis:0, candidates:0, final:0 };
    stats.games.push(gs);
    process.stderr.write(`[${gi+1}/${games.length}] ${game.title}: ${hist.length} plies, middlegame ply ${div.mid}, endgame ply ${div.end}\n`);

    const base = ply=>{
      const fen = fens[ply], m = hist[ply], prev = hist[ply-1];
      return { key:posKey(fen), fen, game:game.id, title:game.title, event:game.event, year:game.year, ply,
               moveNo:+fen.split(' ')[5], side:fen.split(' ')[1],
               last: prev ? [prev.from, prev.to] : null,
               hist:{ uci:m.from+m.to+(m.promotion||''), san:m.san, from:m.from, to:m.to } };
    };
    // Board analysis range: decisive games, middlegame start to endgame start (a few half-moves
    // more at the endgame start, for its anchor).
    // (When the middlegame and endgame start together, the range starts at the endgame start.)
    const baFrom = decisive ? (div.mid>=0 ? div.mid : div.end) : -1, baLast = div.end>=0 ? div.end : hist.length-1;
    const baTo = baFrom<0 ? -2 : (div.end>=0 ? div.end + R.ANALYSIS.retryPlies : baLast);
    if(!decisive) tally(stats.analysis, 'games skipped: draw');

    // ----- One pass: every half-move is checked once against every exercise, with early exits.
    const elig = {};   // ply -> { options:Set, metrics, final }
    for(let ply=0; ply<hist.length; ply++){
      const fen = fens[ply], c = new Chess(fen), moveNo = +fen.split(' ')[5];
      // General rules (all exercises).
      if(moveNo < R.GENERAL.minMove || moveNo > R.GENERAL.maxMove) continue;
      gs.checked++; stats.positions++;
      const moves = c.moves({verbose:true}), prev = hist[ply-1];
      if(moves.length < R.GENERAL.minLegalMoves){ why('fewer than 4 legal moves'); continue; }
      if(prev && prev.captured && moves.some(m=>m.to===prev.to && m.captured)){ why('mid-exchange'); continue; }
      const ls = await lines(fen);   // the one analysis of this position: top 5
      if(ls[0].mate!=null && ls[0].mate>0){
        const before = await lines(fens[ply-1]);
        if(before[0].mate!=null && before[0].mate<0){ why('mate already under way'); continue; }
      }
      gs.passedGeneral++;
      const e = { options:new Set(), metrics:{}, final:null };
      const best = winPct(ls[0].cp, ls[0].mate), drop = l=>best - winPct(l.cp, l.mate), top5 = ls.slice(0, R.CANDIDATES.trapTopN);

      // Board analysis.
      if(ply>=baFrom && ply<=baTo && baFrom>=0){
        if(R.ANALYSIS.notInCheck && c.in_check()) tally(stats.analysis,'rejected: in check');
        else if(Math.abs(L.materialDiff(c)) > R.ANALYSIS.maxMaterialDiff) tally(stats.analysis,'rejected: material');
        else if(div.mid>=0 && ply < div.mid + R.ANALYSIS.earlyBalanced.plies && ls[0].mate==null && Math.abs(ls[0].cp) < R.ANALYSIS.earlyBalanced.maxEval) tally(stats.analysis,'rejected: balanced, early in the middlegame');
        else { e.options.add('analysis'); e.metrics.evalWhite = (fen.split(' ')[1]==='w' ? 1 : -1) * moverScore(ls[0]); e.metrics.mate = ls[0].mate ?? null; }
      }
      // Candidate moves: a trap (Dubious or worse) among the top 5.
      if(top5.some(l=>drop(l) >= R.CANDIDATES.trapMinDrop)){ e.options.add('candidates'); e.metrics.decentMoves = top5.filter(l=>drop(l) < R.CANDIDATES.trapMinDrop).length; }
      else tally(stats.candidates, 'rejected: no trap in top 5');
      // Final choice (the only check needing more searches, so it comes last).
      const f = await finalCheck(ply, top5);
      if(f){ e.options.add('final'); e.final = f.final; Object.assign(e.metrics, f.metrics); }

      if(e.options.size){ elig[ply] = e; e.options.forEach(a=>stats.eligible[a]++); }
    }
    // Board analysis anchors: the middlegame and endgame starts, or the next half-move that
    // qualifies (up to 3). Past the endgame start, only the anchor stays in Board analysis.
    const anchors = new Set();
    if(baFrom>=0) for(const start of [div.mid, div.end]){
      if(start<0) continue;
      for(let ply=start; ply<=start+R.ANALYSIS.retryPlies; ply++) if(elig[ply] && elig[ply].options.has('analysis')){ anchors.add(ply); stats.eligible.anchors++; break; }
    }
    for(const [ply, e] of Object.entries(elig)) if(+ply > baLast && !anchors.has(+ply) && e.options.delete('analysis')){ stats.eligible.analysis--; if(!e.options.size) delete elig[ply]; }

    // Final choice rules for one position; null (with the reason tallied) if it doesn't qualify.
    async function finalCheck(ply, top5){
      const gm = hist[ply], gmUci = gm.from+gm.to+(gm.promotion||'');
      // The game move is judged inside ONE search with the top 5.
      const cand = top5.some(l=>l.uci===gmUci) ? top5
                 : (await analyse(fens[ply], [...top5.map(l=>l.uci), gmUci])).slice().sort((a,b)=>winPct(b.cp,b.mate)-winPct(a.cp,a.mate));
      const gmLine = cand.find(l=>l.uci===gmUci);
      if(!gmLine){ tally(stats.final, 'rejected: search lost the game move'); return null; }
      const cBest = winPct(cand[0].cp, cand[0].mate), cDrop = l=>cBest - winPct(l.cp, l.mate);
      if(new Set(cand.map(l=>gradeOf(cDrop(l)))).size < R.FINAL.minGrades){ tally(stats.final, 'rejected: fewer than 3 grades'); return null; }
      const picks = [cand[0]]; if(gmLine!==cand[0]) picks.push(gmLine);
      const have = ()=>picks.map(l=>gradeOf(cDrop(l)));
      for(const l of cand){ if(picks.length>=4) break; if(!picks.includes(l) && !have().includes(gradeOf(cDrop(l)))) picks.push(l); }
      const BAD = R.FINAL.uniqueGrades;
      while(picks.length<4){
        const rest = cand.filter(l=>!picks.includes(l) && !(BAD.includes(gradeOf(cDrop(l))) && have().includes(gradeOf(cDrop(l))))); if(!rest.length) break;
        const count = g=>have().filter(x=>x===g).length;
        rest.sort((a,b)=>count(gradeOf(cDrop(a))) - count(gradeOf(cDrop(b))));
        picks.push(rest[0]);
      }
      if(picks.length<4){ tally(stats.final, 'rejected: fewer than 4 moves'); return null; }
      const four = await analyse(fens[ply], picks.map(l=>l.uci));
      const cp = {}; four.forEach(l=>{ cp[l.uci] = moverScore(l); });
      if(Object.keys(cp).length<4){ tally(stats.final, 'rejected: search lost a move'); return null; }
      const b4 = winPct(four[0].cp, four[0].mate), g4 = four.map(l=>gradeOf(b4 - winPct(l.cp, l.mate)));
      if(new Set(g4).size < R.FINAL.minGrades){ tally(stats.final, 'rejected: fewer than 3 grades among the 4 shown'); return null; }
      if(BAD.some(g=>g4.filter(x=>x===g).length > 1)){ tally(stats.final, 'rejected: two moves of the same bad grade'); return null; }
      const rnd = randomAccuracy(cp);
      if(rnd > R.FINAL.maxRandomAccuracy){ tally(stats.final, 'rejected: random order scores > 60%'); return null; }
      return { final:{ moves: picks.map(l=>l.uci) }, metrics:{ randomAccuracy: Math.round(rnd), grades: g4, gameMoveGrade: gradeOf(cDrop(gmLine)) } };
    }
    for(const [ply, e] of Object.entries(elig)) items.push({ ...base(+ply), options:e.options, anchor:anchors.has(+ply), metrics:e.metrics, final:e.final });
  }

  // ----- Each exercise keeps every position it qualifies for (within its spacing).
  const chosen = L.choosePools(items, { analysis:R.ANALYSIS.spacingPlies, candidates:R.CANDIDATES.spacingPlies, final:0 });
  const pools = { analysis:[], candidates:[], final:[] };
  for(const act of Object.keys(chosen)) for(const it of chosen[act]){
    const { options, anchor, act:_, metrics, final, ...entry } = it;
    const keep = { analysis:['evalWhite','mate'], candidates:['decentMoves'], final:['randomAccuracy','grades','gameMoveGrade'] }[act];
    const e = { ...entry, anchor: act==='analysis' ? anchor : undefined, metrics: Object.fromEntries(keep.filter(k=>k in metrics).map(k=>[k, metrics[k]])) };
    if(act==='final') e.final = final;
    pools[act].push(e);
    stats.games.find(gm=>gm.id===entry.game)[act]++;
  }
  Object.values(pools).forEach(list=>list.sort((a,b)=>a.game.localeCompare(b.game, undefined, {numeric:true}) || a.ply-b.ply));
  stats.multi = items.filter(it=>it.options.size>1).length;
  const out = { version:R.VERSION, engine:'Stockfish 16.1, depth '+R.ENGINE.depth, generated:new Date().toISOString(), pools };
  fs.mkdirSync(outDir, {recursive:true});
  fs.writeFileSync(path.join(outDir,'pools.json'), JSON.stringify(out, null, 1));
  fs.writeFileSync(path.join(outDir,'stats.json'), JSON.stringify(stats, null, 1));
  const st = L.stats(); process.stderr.write(`searches: ${st.searched} new, ${st.reused} reused from the cache\n`);
  console.log(JSON.stringify({ counts: Object.fromEntries(Object.entries(pools).map(([k,v])=>[k,v.length])), eligible: stats.eligible }, null, 1));
  L.send('quit');
})();
