// Builds the app's test positions (edge cases) and prints Stockfish's top 5 for each.
// Usage: node scripts/make-test-positions.js out.json   (then paste into TEST_POSITIONS in app/index.html)
const {Chess} = require('../vendor/chess.js/chess.js');
const {spawn} = require('child_process');
const SF = process.env.STOCKFISH || require('path').join(__dirname, '../engine/stockfish');
const T = [
  ['White in check', {moves:'d4 Nf6 c4 e6 Nf3 Bb4+'}, 'Bd2'],
  ['Black in check', {moves:'e4 d6 Bb5+'}, 'c6'],
  ['En passant (White)', {moves:'e4 f5 e5 d5'}, 'exd6'],
  ['En passant (Black)', {moves:'Nc3 e5 Nf3 e4 d4'}, 'exd3'],
  ['Castling', {moves:'e4 e5 Nf3 Nc6 Bc4 Bc5'}, 'O-O'],
  ['Promotion: knight fork (White)', {fen:'8/4P1q1/3k4/8/8/2P5/1K6/8 w - - 0 50'}, 'e8=N+'],
  ['Promotion: knight fork (Black)', {fen:'8/1k6/2p5/8/8/3K4/4p1Q1/8 b - - 0 50'}, 'e1=N+'],
  ['Promotion with captures', {fen:'r5k1/1P3ppp/8/8/8/8/5PPP/6K1 w - - 0 30'}, 'bxa8=Q+'],
  ['Mate in one', {fen:'6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 30'}, 'Rd8#'],
  ['Stalemate trap (game move stalemates)', {fen:'7k/8/5K2/8/8/8/8/6Q1 w - - 0 60'}, 'Qg6'],
  // Material marks: an extra rook, bishop and two pawns (d5 passed first, then c3) for White; an extra queen and knight for Black; White's bishop pair labelled.
  ['Material marks', {fen:'3q1rk1/pp1b1ppp/5n2/3P4/2B5/2P1B3/PP3PPP/R3R1K1 w - - 0 20'}, 'Bd4'],
  // Pawn marks: White a4 isolated, c3 doubled, d5 connected, e5 passed, f3 doubled but protected by e2; Black c7 backward, h5 passed.
  ['Pawn marks', {fen:'2r3k1/2p3p1/1p6/3PP2p/P7/2P2P2/2P1PP2/3R2K1 w - - 0 30'}, 'Rd4'],
  // Space marks (King's Indian): White's squares c3 d3 e3 f3 and pawns c4 d5 e4; Black's f6 (c6 e6 taken by d5, f5 by e4) and pawns c5 d6 e5 (gaining c7 d7 e7, not drawn).
  ['Space marks', {fen:'r1bq1rk1/pp2npbp/3p1np1/2pPp3/2P1P3/2N2N2/PP2BPPP/R1BQ1RK1 w - - 0 9'}, 'Ne1'],
  // Activity marks: White Nd5 and Bd6 on outposts, Rf1 open file, Ke3 central (endgame); Black Re8 half-open.
  ['Activity marks', {fen:'4r1k1/3bb1p1/1p1B3p/2pNP3/2PP4/4K1P1/8/5R2 w - - 0 35'}, 'Rf2'],
  // King safety marks: opposite castling. White Shelter b2 c2, Black Shelter f7 g7 h6; Storm g6 and c3 (blocked, still counted heavily); attacks from Ng5, Be4, g6 (on Black's zone) and Qa5, Rc6, c3 (on White's); a safe check on d8 (Rd8+); both queens.
  ['King safety marks', {fen:'6k1/pb3pp1/1pr2nPp/q5N1/4B2P/2p1Q3/PPP2P2/2KR3R w - - 0 20'}, 'Rd8+'],
  // Threats marks: White Nf3 on the hanging Bh4 (ringed, Hanging), d4-d5 forking Nc6 and Ne6 (the move's arrow); Black a6 on Bb5 (a lesser piece); Bb5 on the guarded Nc6 not shown.
  ['Threats marks', {fen:'r4rk1/1ppq1ppp/p1npn3/1B6/2PP3b/2N1PN2/PP3PPP/R2QK2R w KQ - 0 10'}, 'Bxc6'],
  // King activity marks (endgame: no queens): White Ke4 central (Centre +3), attacking d4 and f4 (Target), beside its passed e5 (Escort); Black Kf7 Centre +1.
  ['King activity marks', {fen:'8/5k2/8/4P3/3pKp2/8/8/8 w - - 0 40'}, 'Kxd4'],
  // Development marks (beta; Ruy Lopez, Breyer-like): White's developed pieces Nf3 Ng3 Bc2 Re1 (+1 each; Bc1 Qd1 Ra1 never moved),
  // Black's Nd7 Nf6 Bb7 Re8 Bf8 (+1 each): Black + by 1. Bf8 went back to its square (Be7-f8): it has moved, so it counts (the game's moves are needed: sans).
  ['Development marks', {moves:'e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3 Nb8 d4 Nbd7 Nbd2 Bb7 Bc2 Re8 Nf1 Bf8 Ng3 g6'}, 'a4'],
];
const sf = spawn(SF); let buf = '', wait = null;
sf.stdout.on('data', d=>{ buf += d; if(wait && buf.includes('bestmove')){ const o = buf; buf = ''; const w = wait; wait = null; w(o); } });
const run = cmd=>new Promise(r=>{ wait = r; sf.stdin.write(cmd); });
(async()=>{
  const out = [];
  for(const [name, src, gm] of T){
    let g, last = null;
    if(src.moves){ g = new Chess(); let m; for(const s of src.moves.split(' ')) m = g.move(s); last = [m.from, m.to]; }
    else g = new Chess(src.fen);
    const fen = g.fen(), mv = g.move(gm); if(!mv) throw new Error(name+': bad game move '+gm); g.undo();
    const r = await run(`setoption name MultiPV value 5\nposition fen ${fen}\ngo depth 18\n`);
    const L = {};
    r.split('\n').filter(l=>/^info .* pv /.test(l)).forEach(l=>{
      const k = +l.match(/multipv (\d+)/)[1], sc = l.match(/score (cp|mate) (-?\d+)/), u = l.match(/ pv (\S+)/)[1];
      const h = new Chess(fen), x = h.move({from:u.slice(0,2), to:u.slice(2,4), promotion:u[4]});
      L[k] = (x ? x.san : u)+' '+(sc[1]==='mate' ? '#'+sc[2] : sc[2]);
    });
    console.log(name.padEnd(32), g.moves().length+' legal', '| top:', Object.values(L).join(', '));
    // noImbalances: one side so far ahead that Stockfish gives no breakdown (kept out of Imbalance reading)
    const noImb = /knight fork|Stalemate/.test(name);
    out.push({ key:'test-'+out.length, fen, side:fen.split(' ')[1], moveNo:+fen.split(' ')[5], title:name, year:'', last,
               hist:{ uci:mv.from+mv.to+(mv.promotion||''), san:mv.san, from:mv.from, to:mv.to }, ...(src.moves ? { sans:src.moves } : {}), ...(noImb ? { noImbalances:true } : {}) });
  }
  require('fs').writeFileSync(process.argv[2], JSON.stringify(out));
  sf.kill();
})();
