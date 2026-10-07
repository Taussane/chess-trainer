// Position finder for a player's own games (a Lichess PGN export).
// Usage: node finder/own.js <games.pgn> <player> <out-dir>
//
// Own games are about the player's errors and the games' key moments:
//  - Candidate moves and Final choice: EVERY move of the player that was Dubious or worse
//    (10+ points of winning chances below the best move), at any move number, with no spacing.
//    Only rules that would break an exercise apply: Final choice needs at least 4 legal moves,
//    Candidate moves at least 2. A mistake goes into both exercises.
//  - Board analysis: the middlegame and endgame starts (anchors), plus positions in between at
//    least 7 half-moves from the game's other Board analysis positions; never a mistake position;
//    draws included; general rules (moves 5-40, 4+ legal moves, not mid-exchange), not in check,
//    material within 3 points.
// Every position where the player is to move is analysed (top 5 at the rules' depth), with the
// game move judged in the same search as the top 5.
const L = require('./lib.js');
const { fs, path, Chess, R, header, analyse, winPct, gradeOf, posKey } = L;
const OWN = { candidatesMinLegal:2, finalMinLegal:4, mistakeDrop:10 };

(async()=>{
  const [pgnFile, player, outDir] = process.argv.slice(2);
  const me = (player||'').toLowerCase();
  await L.start();
  const games = L.splitGames(fs.readFileSync(pgnFile,'utf8'));
  const stats = { player, games:[], mistakes:{ total:0, byGrade:{}, finalEligible:0 }, analysis:{ anchors:0, eligible:0 }, skipped:{} };
  const items = [];
  for(const [gi, g] of games.entries()){
    const h = k=>header(g,k);
    if((h('Variant') && h('Variant')!=='Standard') || h('FEN')){ stats.skipped.variant = (stats.skipped.variant||0)+1; continue; }
    const side = h('White').toLowerCase()===me ? 'w' : h('Black').toLowerCase()===me ? 'b' : null;
    if(!side){ stats.skipped.notMine = (stats.skipped.notMine||0)+1; continue; }
    // Moves (Lichess comments and clocks are skipped by mainline).
    const toks = L.mainline(g), ch = new Chess(), hist = [];
    for(const t of toks){ const m = ch.move(t) || ch.move(t,{sloppy:true}); if(!m) break; hist.push(m); }
    const fens = [new Chess().fen()]; { const r = new Chess(); hist.forEach(m=>{ r.move(m.san); fens.push(r.fen()); }); }
    const site = h('Site').match(/lichess\.org\/(\w{8})/), id = site ? site[1] : 'g'+gi;
    const speed = (w=>w==='ultrabullet' ? 'ultraBullet' : w)((h('Event').match(/(ultraBullet|bullet|blitz|rapid|classical|correspondence)/i)||[,''])[1].toLowerCase());   // as the app names them
    const game = { id, white:h('White'), black:h('Black'), me:side, year:(h('UTCDate')||h('Date')).slice(0,4), speed, result:h('Result') };
    game.title = `${game.white} – ${game.black}`;
    const div = L.divide(fens);
    const gs = { ...game, plies:hist.length, middlegame:div.mid, endgame:div.end, mistakes:0, analysis:0, candidates:0, final:0 };
    stats.games.push(gs);
    process.stderr.write(`[${gi+1}/${games.length}] ${game.title}: ${hist.length} plies\n`);
    const base = ply=>{
      const fen = fens[ply], m = hist[ply], prev = hist[ply-1];
      return { key:posKey(fen), fen, game:id, title:game.title, year:[game.year, speed && speed[0].toUpperCase()+speed.slice(1)].filter(Boolean).join(' · '), ply,
               moveNo:+fen.split(' ')[5], side:fen.split(' ')[1], last: prev ? [prev.from, prev.to] : null,
               hist:{ uci:m.from+m.to+(m.promotion||''), san:m.san, from:m.from, to:m.to } };
    };
    const baFrom = div.mid>=0 ? div.mid : div.end, baLast = div.end>=0 ? div.end : hist.length-1, baTo = div.end>=0 ? div.end + R.ANALYSIS.retryPlies : baLast;
    // ----- One pass: every half-move is checked once, with early exits. The player's moves are
    // checked for a mistake (one analysis each); any position that isn't a mistake can be a Board
    // analysis position (no analysis needed to qualify).
    const ba = [];
    for(let ply=0; ply<hist.length; ply++){
      const fen = fens[ply], c = new Chess(fen), moves = c.moves({verbose:true}), moveNo = +fen.split(' ')[5];
      if(fen.split(' ')[1]===side && moves.length >= OWN.candidatesMinLegal){
        const top5 = (await analyse(fen)).slice(0, 5);
        const gm = hist[ply], gmUci = gm.from+gm.to+(gm.promotion||'');
        const cand = top5.some(l=>l.uci===gmUci) ? top5
                   : (await analyse(fen, [...top5.map(l=>l.uci), gmUci])).slice().sort((a,b)=>winPct(b.cp,b.mate)-winPct(a.cp,a.mate));
        const gmLine = cand.find(l=>l.uci===gmUci);
        const drop = gmLine ? winPct(cand[0].cp, cand[0].mate) - winPct(gmLine.cp, gmLine.mate) : 0;
        if(drop >= OWN.mistakeDrop){
          const grade = gradeOf(drop), options = new Set(['candidates']);
          if(moves.length >= OWN.finalMinLegal){ options.add('final'); stats.mistakes.finalEligible++; }
          items.push({ ...base(ply), options, anchor:false, metrics:{ grade, drop:Math.round(drop) } });
          gs.mistakes++; stats.mistakes.total++; stats.mistakes.byGrade[grade] = (stats.mistakes.byGrade[grade]||0)+1;
          continue;   // a mistake position is never a Board analysis position
        }
      }
      // Board analysis rules.
      if(baFrom<0 || ply<baFrom || ply>baTo) continue;
      if(moveNo < R.GENERAL.minMove || moveNo > R.GENERAL.maxMove || moves.length < R.GENERAL.minLegalMoves) continue;
      const prev = hist[ply-1]; if(prev && prev.captured && moves.some(m=>m.to===prev.to && m.captured)) continue;
      if(c.in_check() || Math.abs(L.materialDiff(c)) > R.ANALYSIS.maxMaterialDiff) continue;
      if(div.mid>=0 && ply < div.mid + R.ANALYSIS.earlyBalanced.plies){   // balanced, early in the middlegame: skipped
        const l0 = (await analyse(fen))[0];
        if(l0.mate==null && Math.abs(l0.cp) < R.ANALYSIS.earlyBalanced.maxEval) continue;
      }
      ba.push(ply);
    }
    // Board analysis anchors (middlegame and endgame starts, or up to 3 half-moves later); past
    // the endgame start only the anchor stays.
    const anchors = new Set();
    for(const start of [div.mid, div.end]){ if(start<0) continue; const a = ba.find(p=>p>=start && p<=start+R.ANALYSIS.retryPlies); if(a!=null){ anchors.add(a); stats.analysis.anchors++; } }
    for(const ply of ba){
      if(ply > baLast && !anchors.has(ply)) continue;
      items.push({ ...base(ply), options:new Set(['analysis']), anchor:anchors.has(ply), metrics:{} });
      stats.analysis.eligible++;
    }
  }
  // ----- Each exercise keeps every position it qualifies for: all mistakes in both Candidate
  // moves and Final choice (no spacing); Board analysis anchors, then 7 half-moves apart.
  const chosen = L.choosePools(items, { analysis:R.ANALYSIS.spacingPlies, candidates:0, final:0 });
  const pools = { analysis:[], candidates:[], final:[] }, counts = {};
  for(const act of Object.keys(chosen)){ for(const it of chosen[act]){ const { options, act:_, ...e } = it; pools[act].push(e); stats.games.find(x=>x.id===e.game)[act]++; } counts[act] = pools[act].length; }
  Object.values(pools).forEach(list=>list.sort((a,b)=>a.game.localeCompare(b.game) || a.ply-b.ply));
  fs.mkdirSync(outDir, {recursive:true});
  fs.writeFileSync(path.join(outDir,'pools.json'), JSON.stringify({ version:R.VERSION, player, generated:new Date().toISOString(), pools }, null, 1));
  fs.writeFileSync(path.join(outDir,'stats.json'), JSON.stringify(stats, null, 1));
  const st = L.stats(); process.stderr.write(`searches: ${st.searched} new, ${st.reused} reused from the cache\n`);
  console.log(JSON.stringify({ counts, mistakes: stats.mistakes, analysis: stats.analysis, skipped: stats.skipped }, null, 1));
  L.send('quit');
})();
