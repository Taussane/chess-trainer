// Builds the app owner's built-in games (OWNER_SEED in app/index.html) from a Lichess export,
// with the evaluations the app needs taken from the finder's saved analysis (finder/own.js must
// have run on the same file): for each move of the player, the position before it (best move)
// and after it (the move played, judged in the same search as the top 5).
// Usage: node scripts/make-owner-seed.js <games.pgn> <player> <out.json>
const L = require('../finder/lib.js');
const { fs, Chess, header, analyse, winPct } = L;
const [pgnFile, player, out] = process.argv.slice(2);
(async()=>{
  L.send('uci'); await L.until('uciok'); L.send('isready'); await L.until('readyok');
  const me = player.toLowerCase(), games = [];
  for(const g of L.splitGames(fs.readFileSync(pgnFile,'utf8'))){
    const h = k=>header(g,k);
    const side = h('White').toLowerCase()===me ? 'w' : h('Black').toLowerCase()===me ? 'b' : null;
    if(!side || (h('Variant') && h('Variant')!=='Standard')) continue;
    const c = new Chess(), sans = [], fens = [c.fen()];
    for(const t of L.mainline(g)){ const m = c.move(t) || c.move(t,{sloppy:true}); if(!m) break; sans.push(m.san); fens.push(c.fen()); }
    const evals = new Array(sans.length).fill(null);
    for(let ply=0; ply<sans.length; ply++){
      if(fens[ply].split(' ')[1]!==side || new Chess(fens[ply]).moves().length < 2) continue;
      const top5 = (await analyse(fens[ply])).slice(0, 5);
      const mv = new Chess(fens[ply]).move(sans[ply]), u = mv.from+mv.to+(mv.promotion||'');
      const cand = top5.some(l=>l.uci===u) ? top5 : (await analyse(fens[ply], [...top5.map(l=>l.uci), u])).slice().sort((a,b)=>winPct(b.cp,b.mate)-winPct(a.cp,a.mate));
      const best = cand[0], gm = cand.find(l=>l.uci===u); if(!gm) continue;
      const s = side==='w' ? 1 : -1, toWhite = l=>l.mate!=null ? { mate:s*l.mate } : { cp:s*l.cp };
      if(ply>0) evals[ply-1] = toWhite(best);   // the position before your move, as its best move leaves it
      evals[ply] = toWhite(gm);                 // after your move
    }
    const site = h('Site').match(/lichess\.org\/(\w{8})/);
    const speed = (h('Event').match(/(ultraBullet|bullet|blitz|rapid|classical|correspondence)/i)||[,''])[1].toLowerCase();
    games.push({ id: site ? site[1] : 'g'+games.length, white:h('White'), black:h('Black'), me:side, year:(h('UTCDate')||h('Date')).slice(0,4),
                 speed, result:h('Result'), sans, evals, status:'evaluated', positions:[] });
  }
  fs.writeFileSync(out, JSON.stringify(games));
  const st = L.stats(); console.log(games.length, 'games;', st.searched, 'new searches,', st.reused, 'reused');
  L.send('quit');
})();
