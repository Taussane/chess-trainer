// Stockfish 10's evaluation (the classical, hand-written one), ported to JavaScript.
//
// A one-to-one port of the chess part of the Stockfish.js 10 build the app loads (the multi-variant
// fork by Niklas Fiekas, itself Stockfish 10 with a few later fixes), so that the app can see not
// only each term's total but every item behind it: which piece is hanging, which pawn is isolated,
// which square a safe check lands on. Values are Stockfish's internal units (a pawn in the endgame
// is 208); the trace terms match the engine's `eval` command.
//
// Stockfish is free software under the GNU General Public License v3 (see THIRD_PARTY.md).
// Copyright (C) 2004-2008 Tord Romstad, 2008-2015 Marco Costalba, Joona Kiiski, Tord Romstad,
// 2015-2019 Marco Costalba, Joona Kiiski, Gary Linscott, Tord Romstad.
(function(root){
'use strict';

// ---------------------------------------------------------------- bitboards (BigInt, a1 = bit 0)
const ALL = 0xFFFFFFFFFFFFFFFFn;
const SQ = []; for(let s=0; s<64; s++) SQ.push(1n << BigInt(s));
const fileOf = s=>s & 7, rankOf = s=>s >> 3;
const FILE_BB = []; for(let f=0; f<8; f++) FILE_BB.push(0x0101010101010101n << BigInt(f));
const RANK_BB = []; for(let r=0; r<8; r++) RANK_BB.push(0xFFn << BigInt(8*r));
const FileA = FILE_BB[0], FileH = FILE_BB[7];
const DarkSquares = 0xAA55AA55AA55AA55n;
const QueenSide = FILE_BB[0] | FILE_BB[1] | FILE_BB[2] | FILE_BB[3];
const CenterFiles = FILE_BB[2] | FILE_BB[3] | FILE_BB[4] | FILE_BB[5];
const KingSide = FILE_BB[4] | FILE_BB[5] | FILE_BB[6] | FILE_BB[7];
const Center = (FILE_BB[3] | FILE_BB[4]) & (RANK_BB[3] | RANK_BB[4]);
const KingFlank = [QueenSide ^ FILE_BB[3], QueenSide, QueenSide, CenterFiles, CenterFiles, KingSide, KingSide, KingSide ^ FILE_BB[4]];

function popcount(b){ let n = 0; while(b){ b &= b - 1n; n++; } return n; }
const moreThanOne = b=>(b & (b - 1n)) !== 0n;
function lsb(b){ let s = 0; while(!(b & SQ[s])) s++; return s; }
function msb(b){ let s = 63; while(!(b & SQ[s])) s--; return s; }
function squares(b){ const out = []; for(let s=0; b; s++, b >>= 1n) if(b & 1n) out.push(s); return out; }
const N = 8, S_ = -8, E = 1, W = -1, NE = 9, NW = 7, SE = -7, SW = -9;
function shift(b, d){
  switch(d){
    case N:  return (b << 8n) & ALL;
    case S_: return b >> 8n;
    case E:  return ((b & ~FileH) << 1n) & ALL;
    case W:  return (b & ~FileA) >> 1n;
    case NE: return ((b & ~FileH) << 9n) & ALL;
    case NW: return ((b & ~FileA) << 7n) & ALL;
    case SE: return (b & ~FileH) >> 7n;
    case SW: return (b & ~FileA) >> 9n;
  }
}
const WHITE = 0, BLACK = 1;
const PAWN = 1, KNIGHT = 2, BISHOP = 3, ROOK = 4, QUEEN = 5, KING = 6, ALL_PIECES = 0;
const up = c=>c===WHITE ? N : S_, down = c=>c===WHITE ? S_ : N;
const relRank = (c, s)=>c===WHITE ? rankOf(s) : 7 - rankOf(s);
const pawnAttacksBB = (c, b)=>c===WHITE ? shift(b, NW) | shift(b, NE) : shift(b, SW) | shift(b, SE);
const doublePawnAttacksBB = (c, b)=>c===WHITE ? shift(b, NW) & shift(b, NE) : shift(b, SW) & shift(b, SE);

const dist = (a, b)=>Math.max(Math.abs(fileOf(a) - fileOf(b)), Math.abs(rankOf(a) - rankOf(b)));
const DistanceRingBB = [];
const PawnAttacks = [[], []], KnightAttacks = [], KingAttacks = [];
const ForwardRanksBB = [[], []], ForwardFileBB = [[], []], PawnAttackSpan = [[], []], PassedPawnMask = [[], []];
const AdjacentFilesBB = [];
const LineBB = [], BetweenBB = [];
const ROOK_DIRS = [[1,0],[-1,0],[0,1],[0,-1]], BISHOP_DIRS = [[1,1],[1,-1],[-1,1],[-1,-1]];
function slide(s, dirs, occ){
  let b = 0n; const f0 = fileOf(s), r0 = rankOf(s);
  for(const [df, dr] of dirs){ let f = f0 + df, r = r0 + dr;
    while(f>=0 && f<8 && r>=0 && r<8){ const t = r*8 + f; b |= SQ[t]; if(occ & SQ[t]) break; f += df; r += dr; } }
  return b;
}
const bishopAttacks = (s, occ)=>slide(s, BISHOP_DIRS, occ), rookAttacks = (s, occ)=>slide(s, ROOK_DIRS, occ);
const PseudoBishop = [], PseudoRook = [];
for(let f=0; f<8; f++) AdjacentFilesBB.push((f > 0 ? FILE_BB[f-1] : 0n) | (f < 7 ? FILE_BB[f+1] : 0n));
for(let r=0; r<8; r++){
  let w = 0n, bl = 0n;
  for(let rr=r+1; rr<8; rr++) w |= RANK_BB[rr];
  for(let rr=0; rr<r; rr++) bl |= RANK_BB[rr];
  ForwardRanksBB[WHITE][r] = w; ForwardRanksBB[BLACK][r] = bl;
}
for(let s=0; s<64; s++){
  DistanceRingBB.push(Array(8).fill(0n));
  for(let t=0; t<64; t++) DistanceRingBB[s][dist(s, t)] |= SQ[t];
  const add = (arr, df, dr)=>{ const f = fileOf(s) + df, r = rankOf(s) + dr; return (f>=0 && f<8 && r>=0 && r<8) ? SQ[r*8 + f] : 0n; };
  PawnAttacks[WHITE][s] = add(0, -1, 1) | add(0, 1, 1);
  PawnAttacks[BLACK][s] = add(0, -1, -1) | add(0, 1, -1);
  KnightAttacks[s] = [[1,2],[2,1],[2,-1],[1,-2],[-1,-2],[-2,-1],[-2,1],[-1,2]].reduce((b, [a, c])=>b | add(0, a, c), 0n);
  KingAttacks[s] = [[1,1],[1,0],[1,-1],[0,1],[0,-1],[-1,1],[-1,0],[-1,-1]].reduce((b, [a, c])=>b | add(0, a, c), 0n);
  PseudoBishop[s] = bishopAttacks(s, 0n); PseudoRook[s] = rookAttacks(s, 0n);
  for(const c of [WHITE, BLACK]){
    ForwardFileBB[c][s] = ForwardRanksBB[c][rankOf(s)] & FILE_BB[fileOf(s)];
    PawnAttackSpan[c][s] = ForwardRanksBB[c][rankOf(s)] & AdjacentFilesBB[fileOf(s)];
    PassedPawnMask[c][s] = PawnAttackSpan[c][s] | ForwardFileBB[c][s];
  }
}
for(let a=0; a<64; a++){ LineBB.push([]); BetweenBB.push([]);
  for(let b=0; b<64; b++){
    let line = 0n, between = 0n;
    for(const [P, at] of [[PseudoBishop, bishopAttacks], [PseudoRook, rookAttacks]])
      if(P[a] & SQ[b]){ line = (P[a] & P[b]) | SQ[a] | SQ[b]; between = at(a, SQ[b]) & at(b, SQ[a]); }
    LineBB[a].push(line); BetweenBB[a].push(between);
  }
}

// ---------------------------------------------------------------- values and tables
const S = (mg, eg)=>[mg, eg];
const add2 = (a, b)=>[a[0] + b[0], a[1] + b[1]], sub2 = (a, b)=>[a[0] - b[0], a[1] - b[1]];
const mul2 = (a, k)=>[a[0] * k, a[1] * k], div2 = (a, k)=>[Math.trunc(a[0] / k), Math.trunc(a[1] / k)];
const ZERO = [0, 0];
const VALUE_MG = [0, 136, 782, 830, 1289, 2529, 0], VALUE_EG = [0, 208, 865, 918, 1378, 2687, 0];
const PawnValueEg = 208, RookValueMg = 1289, KnightValueMg = 782, BishopValueMg = 830, QueenValueMg = 2529;
const MidgameLimit = 15258, EndgameLimit = 3915, PHASE_MIDGAME = 128;
const LazyThreshold = 1500, SpaceThreshold = 12222, Tempo = 20;

const PSQ_BONUS = [ null,
  [ [S(0,0),S(0,0),S(0,0),S(0,0)], [S(-11,-3),S(7,-1),S(7,7),S(17,2)], [S(-16,-2),S(-3,2),S(23,6),S(23,-1)], [S(-14,7),S(-7,-4),S(20,-8),S(24,2)],
    [S(-5,13),S(-2,10),S(-1,-1),S(12,-8)], [S(-11,16),S(-12,6),S(-2,1),S(4,16)], [S(-2,1),S(20,-12),S(-10,6),S(-2,25)], [S(0,0),S(0,0),S(0,0),S(0,0)] ],
  [ [S(-169,-105),S(-96,-74),S(-80,-46),S(-79,-18)], [S(-79,-70),S(-39,-56),S(-24,-15),S(-9,6)], [S(-64,-38),S(-20,-33),S(4,-5),S(19,27)], [S(-28,-36),S(5,0),S(41,13),S(47,34)],
    [S(-29,-41),S(13,-20),S(42,4),S(52,35)], [S(-11,-51),S(28,-38),S(63,-17),S(55,19)], [S(-67,-64),S(-21,-45),S(6,-37),S(37,16)], [S(-200,-98),S(-80,-89),S(-53,-53),S(-32,-16)] ],
  [ [S(-49,-58),S(-7,-31),S(-10,-37),S(-34,-19)], [S(-24,-34),S(9,-9),S(15,-14),S(1,4)], [S(-9,-23),S(22,0),S(-3,-3),S(12,16)], [S(4,-26),S(9,-3),S(18,-5),S(40,16)],
    [S(-8,-26),S(27,-4),S(13,-7),S(30,14)], [S(-17,-24),S(14,-2),S(-6,0),S(6,13)], [S(-19,-34),S(-13,-10),S(7,-12),S(-11,6)], [S(-47,-55),S(-7,-32),S(-17,-36),S(-29,-17)] ],
  [ [S(-24,0),S(-15,3),S(-8,0),S(0,3)], [S(-18,-7),S(-5,-5),S(-1,-5),S(1,-1)], [S(-19,6),S(-10,-7),S(1,3),S(0,3)], [S(-21,0),S(-7,4),S(-4,-2),S(-4,1)],
    [S(-21,-7),S(-12,5),S(-1,-5),S(4,-7)], [S(-23,3),S(-10,2),S(1,-1),S(6,3)], [S(-11,-1),S(8,7),S(9,11),S(12,-1)], [S(-25,6),S(-18,4),S(-11,6),S(2,2)] ],
  [ [S(3,-69),S(-5,-57),S(-5,-47),S(4,-26)], [S(-3,-55),S(5,-31),S(8,-22),S(12,-4)], [S(-3,-39),S(6,-18),S(13,-9),S(7,3)], [S(4,-23),S(5,-3),S(9,13),S(8,24)],
    [S(0,-29),S(14,-6),S(12,9),S(5,21)], [S(-4,-38),S(10,-18),S(6,-12),S(8,1)], [S(-5,-50),S(6,-27),S(10,-24),S(8,-8)], [S(-2,-75),S(-2,-52),S(1,-43),S(-2,-36)] ],
  [ [S(272,0),S(325,41),S(273,80),S(190,93)], [S(277,57),S(305,98),S(241,138),S(183,131)], [S(198,86),S(253,138),S(168,165),S(120,173)], [S(169,103),S(191,152),S(136,168),S(108,169)],
    [S(145,98),S(176,166),S(112,197),S(69,194)], [S(122,87),S(159,164),S(85,174),S(36,189)], [S(87,40),S(120,99),S(64,128),S(25,141)], [S(64,5),S(87,60),S(49,75),S(0,75)] ] ];
// a piece's value plus its square bonus, from White's point of view (Black: mirrored and negated)
function psq(c, t, s){
  const ws = c===WHITE ? s : s ^ 56, f = Math.min(fileOf(ws), 7 - fileOf(ws)), b = PSQ_BONUS[t][rankOf(ws)][f];
  const v = [VALUE_MG[t] + b[0], VALUE_EG[t] + b[1]];
  return c===WHITE ? v : [-v[0], -v[1]];
}

const QuadraticOurs = [ [1438], [40, 38], [32, 255, -62], [0, 104, 4, 0], [-26, -2, 47, 105, -208], [-189, 24, 117, 133, -134, -6] ];
const QuadraticTheirs = [ [0], [36, 0], [9, 63, 0], [59, 65, 42, 0], [46, 39, 24, -24, 0], [97, 100, -42, 137, 268, 0] ];

const Backward = S(9, 24), Doubled = S(11, 56), Isolated = S(5, 15);
const Seed = [0, 13, 24, 18, 65, 100, 175, 330];
function connected(opposed, phalanx, support, r){
  const v = 17*support + ((Seed[r] + (phalanx ? Math.trunc((Seed[r+1] - Seed[r]) / 2) : 0)) >> (opposed ? 1 : 0));
  return [v, Math.trunc(v * (r - 2) / 4)];
}
const ShelterStrength = [
  [-6, 81, 93, 58, 39, 18, 25], [-43, 61, 35, -49, -29, -11, -63], [-10, 75, 23, -2, 32, 3, -45], [-39, -13, -29, -52, -48, -67, -166] ];
const UnblockedStorm = [
  [89, 107, 123, 93, 57, 45, 51], [44, -18, 123, 46, 39, -7, 23], [4, 52, 162, 37, 7, -14, -2], [-10, -14, 90, 15, 2, -7, -16] ];

const KingAttackWeights = [0, 0, 77, 55, 44, 10];
const QueenSafeCheck = 780, RookSafeCheck = 880, BishopSafeCheck = 435, KnightSafeCheck = 790;
const MobilityBonus = [ null, null,
  [S(-62,-81),S(-53,-56),S(-12,-30),S(-4,-14),S(3,8),S(13,15),S(22,23),S(28,27),S(33,33)],
  [S(-48,-59),S(-20,-23),S(16,-3),S(26,13),S(38,24),S(51,42),S(55,54),S(63,57),S(63,65),S(68,73),S(81,78),S(81,86),S(91,88),S(98,97)],
  [S(-58,-76),S(-27,-18),S(-15,28),S(-10,55),S(-5,69),S(-2,82),S(9,112),S(16,118),S(30,132),S(29,142),S(32,155),S(38,165),S(46,166),S(48,169),S(58,171)],
  [S(-39,-36),S(-21,-15),S(3,8),S(3,18),S(14,34),S(22,54),S(28,61),S(41,73),S(43,79),S(48,92),S(56,94),S(60,104),S(60,113),S(66,120),S(67,123),S(70,126),
   S(71,133),S(73,136),S(79,140),S(88,143),S(88,148),S(99,166),S(102,170),S(102,175),S(106,184),S(109,191),S(113,206),S(116,212)] ];
const Outpost = [ [S(22,6), S(36,12)], [S(9,2), S(15,5)] ];
const RookOnFile = [S(18,7), S(44,20)];
const ThreatByMinor = [S(0,0), S(0,31), S(39,42), S(57,44), S(68,112), S(62,120), S(0,0)];
const ThreatByRook = [S(0,0), S(0,24), S(38,71), S(38,61), S(0,38), S(51,38), S(0,0)];
const PassedRank = [S(0,0), S(5,18), S(12,23), S(10,31), S(57,62), S(163,167), S(271,250)];
const PassedFile = [S(-1,7), S(0,9), S(-9,-8), S(-30,-14), S(-30,-14), S(-9,-8), S(0,9), S(-1,7)];
const BishopPawns = S(3,8), CloseEnemies = S(7,0), Hanging = S(62,34), KingProtector = S(6,7), KnightOnQueen = S(20,12);
const LongDiagonalBishop = S(44,0), MinorBehindPawn = S(16,0), PawnlessFlank = S(18,94), RestrictedPiece = S(7,6);
const RookOnPawn = S(10,28), SliderOnQueen = S(49,21), ThreatByKing = S(21,84), ThreatByPawnPush = S(48,42);
const ThreatByRank = S(14,3), ThreatBySafePawn = S(169,99), TrappedRook = S(98,5), WeakQueen = S(51,10), WeakUnopposedPawn = S(14,20);

// ---------------------------------------------------------------- position
function parseFen(fen){
  const [board, stm, castling] = fen.trim().split(/\s+/);
  const P = { byType: [[0n,0n,0n,0n,0n,0n,0n],[0n,0n,0n,0n,0n,0n,0n]], byColor: [0n, 0n], all: 0n, board: Array(64).fill(null),
              stm: stm==='b' ? BLACK : WHITE, castling: castling || '-' };
  let r = 7, f = 0;
  for(const ch of board){
    if(ch==='/'){ r--; f = 0; continue; }
    if(/\d/.test(ch)){ f += +ch; continue; }
    const c = ch===ch.toUpperCase() ? WHITE : BLACK, t = ' pnbrqk'.indexOf(ch.toLowerCase()), s = r*8 + f;
    P.board[s] = { c, t }; P.byType[c][t] |= SQ[s]; P.byType[c][ALL_PIECES] |= SQ[s]; P.byColor[c] |= SQ[s]; P.all |= SQ[s]; f++;
  }
  P.pieces = (c, ...ts)=>ts.reduce((b, t)=>b | P.byType[c][t], 0n);
  P.both = (...ts)=>P.pieces(WHITE, ...ts) | P.pieces(BLACK, ...ts);
  P.count = (c, t)=>popcount(P.byType[c][t]);
  P.ksq = c=>lsb(P.byType[c][KING]);
  P.npm = c=>KNIGHT_VALUES(P, c);
  P.canCastle = c=>(c===WHITE ? /[KQ]/ : /[kq]/).test(P.castling);
  P.canCastleSide = (c, king)=>P.castling.includes(c===WHITE ? (king ? 'K' : 'Q') : (king ? 'k' : 'q'));
  // pieces blocking a slider's line to each king (pinned pieces and discovered-check candidates)
  P.sliderBlockers = (sliders, s)=>{
    let blockers = 0n;
    const snipers = ((PseudoRook[s] & P.both(QUEEN, ROOK)) | (PseudoBishop[s] & P.both(QUEEN, BISHOP))) & sliders;
    for(const sn of squares(snipers)){ const b = BetweenBB[s][sn] & P.all; if(b && !moreThanOne(b)) blockers |= b; }
    return blockers;
  };
  P.blockersForKing = [P.sliderBlockers(P.byColor[BLACK], P.ksq(WHITE)), P.sliderBlockers(P.byColor[WHITE], P.ksq(BLACK))];
  return P;
}
function KNIGHT_VALUES(P, c){ return P.count(c, KNIGHT)*KnightValueMg + P.count(c, BISHOP)*BishopValueMg + P.count(c, ROOK)*RookValueMg + P.count(c, QUEEN)*QueenValueMg; }

// ---------------------------------------------------------------- material
function imbalance(P){
  const pc = c=>[P.count(c, BISHOP) > 1 ? 1 : 0, P.count(c, PAWN), P.count(c, KNIGHT), P.count(c, BISHOP), P.count(c, ROOK), P.count(c, QUEEN)];
  const cnt = [pc(WHITE), pc(BLACK)];
  const one = us=>{ const them = 1 - us; let bonus = 0;
    for(let p1=0; p1<=5; p1++){ if(!cnt[us][p1]) continue; let v = 0;
      for(let p2=0; p2<=p1; p2++) v += QuadraticOurs[p1][p2] * cnt[us][p2] + QuadraticTheirs[p1][p2] * cnt[them][p2];
      bonus += cnt[us][p1] * v; }
    return bonus; };
  return Math.trunc((one(WHITE) - one(BLACK)) / 16);
}
// endings Stockfish evaluates with a dedicated function (its trace is then all zero)
const materialSig = P=>{ const sig = c=>'K' + 'QRBNP'.split('').map(x=>x.repeat(P.count(c, ' pnbrqk'.indexOf(x.toLowerCase())))).join('');
  return [sig(WHITE) + 'v' + sig(BLACK), sig(BLACK) + 'v' + sig(WHITE)]; };
// endings with a dedicated scaling function: Stockfish skips the imbalance there (left at zero)
const SCALING_CODES = ['KNPvK', 'KNPvKB', 'KRPvKR', 'KRPvKB', 'KBPvKB', 'KBPvKN', 'KBPPvKB', 'KRPPvKRP'];
function specializedEval(P){
  const CODES = ['KPvK', 'KNNvK', 'KBNvK', 'KRvKP', 'KRvKB', 'KRvKN', 'KQvKP', 'KQvKR'];
  if(materialSig(P).some(x=>CODES.includes(x))) return true;
  for(const c of [WHITE, BLACK]) if(!moreThanOne(P.byColor[1 - c]) && P.npm(c) >= RookValueMg) return true;   // KXK
  return false;
}

// ---------------------------------------------------------------- pawns
function pawnsEval(P, Us, e, F){
  const Them = 1 - Us, Up = up(Us);
  let score = ZERO;
  const ourPawns = P.pieces(Us, PAWN), theirPawns = P.pieces(Them, PAWN);
  e.passedPawns[Us] = e.pawnAttacksSpan[Us] = 0n; e.weakUnopposed[Us] = 0;
  e.semiopenFiles[Us] = 0xFF;
  e.pawnAttacks[Us] = pawnAttacksBB(Us, ourPawns);
  e.pawnsOnSquares[Us] = [0, 0];
  e.pawnsOnSquares[Us][BLACK] = popcount(ourPawns & DarkSquares);
  e.pawnsOnSquares[Us][WHITE] = P.count(Us, PAWN) - e.pawnsOnSquares[Us][BLACK];
  for(const s of squares(ourPawns)){
    const f = fileOf(s), su = s + Up;
    e.semiopenFiles[Us] &= ~(1 << f);
    e.pawnAttacksSpan[Us] |= PawnAttackSpan[Us][s];
    const opposed = (theirPawns & ForwardFileBB[Us][s]) !== 0n;
    const stoppers = theirPawns & PassedPawnMask[Us][s];
    const lever = theirPawns & PawnAttacks[Us][s];
    const leverPush = theirPawns & PawnAttacks[Us][su];
    const doubled = (ourPawns & SQ[s - Up]) !== 0n;
    const neighbours = ourPawns & AdjacentFilesBB[f];
    const phalanx = neighbours & RANK_BB[rankOf(s)];
    const supported = neighbours & RANK_BB[rankOf(s - Up)];
    const backward = !(ourPawns & PawnAttackSpan[Them][su]) && !!(stoppers & (leverPush | SQ[su]));
    if(!(stoppers ^ lever ^ leverPush) && popcount(supported) >= popcount(lever) - 1 && popcount(phalanx) >= popcount(leverPush))
      e.passedPawns[Us] |= SQ[s];
    else if(stoppers === SQ[su] && relRank(Us, s) >= 4){
      for(const t of squares(shift(supported, Up) & ~theirPawns))
        if(!moreThanOne(theirPawns & PawnAttacks[Us][t])) e.passedPawns[Us] |= SQ[s];
    }
    if(supported | phalanx){ const v = connected(opposed, !!phalanx, popcount(supported), relRank(Us, s)); score = add2(score, v);
      F.push({ term:'pawns', c:Us, kind:'connected', sq:s, v, phalanx: !!phalanx, support: popcount(supported), opposed }); }
    else if(!neighbours){ score = sub2(score, Isolated); e.weakUnopposed[Us] += !opposed ? 1 : 0;
      F.push({ term:'pawns', c:Us, kind:'isolated', sq:s, v: mul2(Isolated, -1), opposed }); }
    else if(backward){ score = sub2(score, Backward); e.weakUnopposed[Us] += !opposed ? 1 : 0;
      F.push({ term:'pawns', c:Us, kind:'backward', sq:s, v: mul2(Backward, -1), opposed }); }
    if(doubled && !supported){ score = sub2(score, Doubled); F.push({ term:'pawns', c:Us, kind:'doubled', sq:s, v: mul2(Doubled, -1) }); }
  }
  return score;
}
function evaluateShelter(P, Us, ksq){
  const Them = 1 - Us, Down = down(Us);
  const BlockRanks = Us===WHITE ? RANK_BB[0] | RANK_BB[1] : RANK_BB[7] | RANK_BB[6];
  let b = P.both(PAWN) & ~ForwardRanksBB[Them][rankOf(ksq)];
  const ourPawns = b & P.byColor[Us], theirPawns = b & P.byColor[Them];
  let safety = (shift(theirPawns, Down) & (FileA | FileH) & BlockRanks & SQ[ksq]) ? 374 : 5;
  const center = Math.max(1, Math.min(6, fileOf(ksq)));
  const files = [];
  for(let f=center-1; f<=center+1; f++){
    b = ourPawns & FILE_BB[f];
    const ourRank = b ? relRank(Us, Us===WHITE ? lsb(b) : msb(b)) : 0;
    b = theirPawns & FILE_BB[f];
    const theirRank = b ? relRank(Us, Them===WHITE ? msb(b) : lsb(b)) : 0;
    const d = Math.min(f, 7 - f);
    const shelter = ShelterStrength[d][ourRank];
    const storm = (ourRank && ourRank===theirRank - 1) ? 66 * (theirRank===2 ? 1 : 0) : UnblockedStorm[d][theirRank];
    safety += shelter - storm;
    files.push({ f, ourRank, theirRank, shelter, storm, blocked: !!(ourRank && ourRank===theirRank - 1) });
  }
  return { safety, files };
}
function kingSafetyPawns(P, Us, F){
  const ksq = P.ksq(Us);
  let minKingPawnDistance = 0;
  const pawns = P.pieces(Us, PAWN);
  if(pawns) while(!(DistanceRingBB[ksq][++minKingPawnDistance] & pawns)){}
  let best = evaluateShelter(P, Us, ksq), from = ksq;
  if(P.canCastleSide(Us, true)){ const o = evaluateShelter(P, Us, Us===WHITE ? 6 : 62); if(o.safety > best.safety){ best = o; from = Us===WHITE ? 6 : 62; } }
  if(P.canCastleSide(Us, false)){ const o = evaluateShelter(P, Us, Us===WHITE ? 2 : 58); if(o.safety > best.safety){ best = o; from = Us===WHITE ? 2 : 58; } }
  F.push({ term:'king', c:Us, kind:'shelter', sq:from, v:[best.safety, 0], files: best.files });
  F.push({ term:'king', c:Us, kind:'pawnDistance', sq:ksq, v:[0, -16 * minKingPawnDistance], n: minKingPawnDistance });
  return [best.safety, -16 * minKingPawnDistance];
}

// ---------------------------------------------------------------- the evaluation
function evaluate(fen){
  const P = parseFen(fen);
  const F = [];   // every item scored: { term, c, kind, sq, v:[mg,eg], ... }
  const T = {};   // trace: term -> [white [mg,eg], black [mg,eg]] or total
  const out = { trace: T, features: F, special: null };
  const npmW = P.npm(WHITE), npmB = P.npm(BLACK);
  const npm = Math.max(EndgameLimit, Math.min(npmW + npmB, MidgameLimit));
  out.phase = Math.trunc(((npm - EndgameLimit) * PHASE_MIDGAME) / (MidgameLimit - EndgameLimit));
  if(specializedEval(P)){ out.special = 'ending'; return out; }

  let psqScore = ZERO;
  for(let s=0; s<64; s++){ const p = P.board[s]; if(p) psqScore = add2(psqScore, psq(p.c, p.t, s)); }
  const imb = materialSig(P).some(x=>SCALING_CODES.includes(x)) ? 0 : imbalance(P);
  let score = add2(psqScore, [imb, imb]);
  const e = { passedPawns: [0n,0n], pawnAttacksSpan: [0n,0n], weakUnopposed: [0,0], semiopenFiles: [0,0], pawnAttacks: [0n,0n], pawnsOnSquares: [[0,0],[0,0]] };
  const pawnScore = [pawnsEval(P, WHITE, e, F), pawnsEval(P, BLACK, e, F)];
  e.openFiles = popcount(BigInt(e.semiopenFiles[WHITE] & e.semiopenFiles[BLACK]));
  e.asymmetry = popcount((e.passedPawns[WHITE] | e.passedPawns[BLACK]) | BigInt(e.semiopenFiles[WHITE] ^ e.semiopenFiles[BLACK]));
  score = add2(score, sub2(pawnScore[WHITE], pawnScore[BLACK]));
  T.material = psqScore; T.imbalance = [imb, imb]; T.pawns = pawnScore;
  const lazy = Math.trunc((score[0] + score[1]) / 2);
  if(Math.abs(lazy) > LazyThreshold){ out.special = 'lazy'; out.lazy = lazy; return out; }

  const attackedBy = [Array(7).fill(0n), Array(7).fill(0n)], attackedBy2 = [0n, 0n];
  const mobilityArea = [0n, 0n], mobility = [ZERO, ZERO], kingRing = [0n, 0n];
  const kingAttackersCount = [0, 0], kingAttackersWeight = [0, 0], kingAttacksCount = [0, 0];
  const semiopen = (c, f)=>(e.semiopenFiles[c] & (1 << f)) !== 0;

  // initialize
  for(const Us of [WHITE, BLACK]){
    const Them = 1 - Us, Up = up(Us), Down = down(Us);
    const LowRanks = Us===WHITE ? RANK_BB[1] | RANK_BB[2] : RANK_BB[6] | RANK_BB[5];
    const b = P.pieces(Us, PAWN) & (shift(P.all, Down) | LowRanks);
    mobilityArea[Us] = ~(b | P.pieces(Us, KING, QUEEN) | e.pawnAttacks[Them]) & ALL;
    attackedBy[Us][KING] = KingAttacks[P.ksq(Us)];
    attackedBy[Us][PAWN] = e.pawnAttacks[Us];
    attackedBy[Us][ALL_PIECES] = attackedBy[Us][KING] | attackedBy[Us][PAWN];
    attackedBy2[Us] = attackedBy[Us][KING] & attackedBy[Us][PAWN];
    kingRing[Us] = 0n; kingAttackersCount[Them] = 0;
    if(P.npm(Them) >= RookValueMg + KnightValueMg){
      kingRing[Us] = attackedBy[Us][KING];
      if(relRank(Us, P.ksq(Us))===0) kingRing[Us] |= shift(kingRing[Us], Up);
      if(fileOf(P.ksq(Us))===7) kingRing[Us] |= shift(kingRing[Us], W);
      else if(fileOf(P.ksq(Us))===0) kingRing[Us] |= shift(kingRing[Us], E);
      kingAttackersCount[Them] = popcount(kingRing[Us] & e.pawnAttacks[Them]);
      kingAttacksCount[Them] = kingAttackersWeight[Them] = 0;
    }
  }
  out.kingRing = kingRing;

  // pieces
  const pieceScore = { [KNIGHT]: [ZERO, ZERO], [BISHOP]: [ZERO, ZERO], [ROOK]: [ZERO, ZERO], [QUEEN]: [ZERO, ZERO] };
  const pieceAttacks = {};   // square -> attacked bitboard (as Stockfish counts it)
  const NAMES = { [KNIGHT]:'knights', [BISHOP]:'bishops', [ROOK]:'rooks', [QUEEN]:'queens' };
  for(const Pt of [KNIGHT, BISHOP, ROOK, QUEEN]) for(const Us of [WHITE, BLACK]){
    const Them = 1 - Us, Down = down(Us), term = NAMES[Pt];
    const OutpostRanks = Us===WHITE ? RANK_BB[3] | RANK_BB[4] | RANK_BB[5] : RANK_BB[4] | RANK_BB[3] | RANK_BB[2];
    let score = ZERO;
    const note = (kind, s, v, extra)=>{ score = add2(score, v); F.push(Object.assign({ term, c:Us, kind, sq:s, v }, extra || {})); };
    attackedBy[Us][Pt] = 0n;
    for(const s of squares(P.pieces(Us, Pt))){
      let b = Pt===BISHOP ? bishopAttacks(s, P.all ^ P.both(QUEEN))
            : Pt===ROOK ? rookAttacks(s, P.all ^ P.both(QUEEN) ^ P.pieces(Us, ROOK))
            : Pt===KNIGHT ? KnightAttacks[s] : bishopAttacks(s, P.all) | rookAttacks(s, P.all);
      if(P.blockersForKing[Us] & SQ[s]) b &= LineBB[P.ksq(Us)][s];
      pieceAttacks[s] = b;
      attackedBy2[Us] |= attackedBy[Us][ALL_PIECES] & b;
      attackedBy[Us][Pt] |= b;
      attackedBy[Us][ALL_PIECES] |= b;
      if(b & kingRing[Them] & ~doublePawnAttacksBB(Them, P.pieces(Them, PAWN))){
        kingAttackersCount[Us]++;
        kingAttackersWeight[Us] += KingAttackWeights[Pt];
        kingAttacksCount[Us] += popcount(b & attackedBy[Them][KING]);
        F.push({ term:'king', c:Us, kind:'attacker', sq:s, v:ZERO, target: 1 - Us, hits: b & kingRing[Them] });
      }
      const mob = popcount(b & mobilityArea[Us]);
      mobility[Us] = add2(mobility[Us], MobilityBonus[Pt][mob]);
      F.push({ term:'mobility', c:Us, kind:'mobility', sq:s, v: MobilityBonus[Pt][mob], n: mob, squares: b & mobilityArea[Us] });
      if(Pt===BISHOP || Pt===KNIGHT){
        let bb = OutpostRanks & ~e.pawnAttacksSpan[Them];
        if(bb & SQ[s]) note('outpost', s, mul2(Outpost[Pt===BISHOP ? 1 : 0][(attackedBy[Us][PAWN] & SQ[s]) ? 1 : 0], 2), { supported: !!(attackedBy[Us][PAWN] & SQ[s]) });
        else if((bb &= b & ~P.byColor[Us])) note('reachableOutpost', s, Outpost[Pt===BISHOP ? 1 : 0][(attackedBy[Us][PAWN] & bb) ? 1 : 0], { squares: bb });
        if(shift(P.both(PAWN), Down) & SQ[s]) note('minorBehindPawn', s, MinorBehindPawn);
        const d = dist(s, P.ksq(Us)); if(d) note('kingProtector', s, mul2(KingProtector, -d), { n: d });
        if(Pt===BISHOP){
          const blocked = P.pieces(Us, PAWN) & shift(P.all, Down);
          const same = e.pawnsOnSquares[Us][(DarkSquares & SQ[s]) ? BLACK : WHITE], k = 1 + popcount(blocked & CenterFiles);
          if(same) note('bishopPawns', s, mul2(BishopPawns, -same * k), { n: same, blocked: k - 1 });
          if(moreThanOne(bishopAttacks(s, P.both(PAWN)) & Center)) note('longDiagonal', s, LongDiagonalBishop);
        }
      }
      if(Pt===ROOK){
        if(relRank(Us, s) >= 4){ const n = popcount(P.pieces(Them, PAWN) & PseudoRook[s]); if(n) note('rookOnPawn', s, mul2(RookOnPawn, n), { n }); }
        if(semiopen(Us, fileOf(s))) note(semiopen(Them, fileOf(s)) ? 'openFile' : 'semiOpenFile', s, RookOnFile[semiopen(Them, fileOf(s)) ? 1 : 0]);
        else if(mob <= 3){
          const kf = fileOf(P.ksq(Us));
          if((kf < 4)===(fileOf(s) < kf)) note('trappedRook', s, mul2(sub2(TrappedRook, [mob * 22, 0]), -(1 + (P.canCastle(Us) ? 0 : 1))));
        }
      }
      if(Pt===QUEEN){
        if(P.sliderBlockers(P.pieces(Them, ROOK, BISHOP), s)) note('weakQueen', s, mul2(WeakQueen, -1));
      }
    }
    pieceScore[Pt][Us] = score;
  }
  for(const Pt of [KNIGHT, BISHOP, ROOK, QUEEN]) score = add2(score, sub2(pieceScore[Pt][WHITE], pieceScore[Pt][BLACK]));
  score = add2(score, sub2(mobility[WHITE], mobility[BLACK]));
  T.knights = pieceScore[KNIGHT]; T.bishops = pieceScore[BISHOP]; T.rooks = pieceScore[ROOK]; T.queens = pieceScore[QUEEN];
  T.mobility = mobility;

  // king
  const kingScore = [ZERO, ZERO];
  for(const Us of [WHITE, BLACK]){
    const Them = 1 - Us;
    const Camp = Us===WHITE ? ALL ^ RANK_BB[5] ^ RANK_BB[6] ^ RANK_BB[7] : ALL ^ RANK_BB[0] ^ RANK_BB[1] ^ RANK_BB[2];
    const ksq = P.ksq(Us);
    let score = kingSafetyPawns(P, Us, F);
    const kingFlank = KingFlank[fileOf(ksq)];
    let b1 = attackedBy[Them][ALL_PIECES] & kingFlank & Camp;
    let b2 = b1 & attackedBy2[Them];
    const tropism = popcount(b1) + popcount(b2);
    if(kingAttackersCount[Them] > 1 - P.count(Them, QUEEN)){
      let kingDanger = 0, unsafeChecks = 0n;
      const weak = attackedBy[Them][ALL_PIECES] & ~attackedBy2[Us] & (~attackedBy[Us][ALL_PIECES] | attackedBy[Us][KING] | attackedBy[Us][QUEEN]);
      let safe = ~P.byColor[Them] & ALL;
      safe &= ~attackedBy[Us][ALL_PIECES] | (weak & attackedBy2[Them]);
      b1 = rookAttacks(ksq, P.all ^ P.pieces(Us, QUEEN));
      b2 = bishopAttacks(ksq, P.all ^ P.pieces(Us, QUEEN));
      const checks = [];
      const qc = (b1 | b2) & attackedBy[Them][QUEEN] & safe & ~attackedBy[Us][QUEEN];
      if(qc){ kingDanger += QueenSafeCheck; checks.push({ piece: QUEEN, squares: qc }); }
      if(b1 & attackedBy[Them][ROOK] & safe){ kingDanger += RookSafeCheck; checks.push({ piece: ROOK, squares: b1 & attackedBy[Them][ROOK] & safe }); }
      else unsafeChecks |= b1 & attackedBy[Them][ROOK];
      if(b2 & attackedBy[Them][BISHOP] & safe){ kingDanger += BishopSafeCheck; checks.push({ piece: BISHOP, squares: b2 & attackedBy[Them][BISHOP] & safe }); }
      else unsafeChecks |= b2 & attackedBy[Them][BISHOP];
      const b = KnightAttacks[ksq];
      if(b & attackedBy[Them][KNIGHT] & safe){ kingDanger += KnightSafeCheck; checks.push({ piece: KNIGHT, squares: b & attackedBy[Them][KNIGHT] & safe }); }
      else unsafeChecks |= b & attackedBy[Them][KNIGHT];
      unsafeChecks &= mobilityArea[Them];
      const parts = {
        attackers: kingAttackersCount[Them] * kingAttackersWeight[Them],
        attacks: 69 * kingAttacksCount[Them],
        weakRing: 185 * popcount(kingRing[Us] & weak),
        pinsAndUnsafeChecks: 150 * popcount(P.blockersForKing[Us] | unsafeChecks),
        tropism: Math.trunc(tropism * tropism / 4),
        noQueen: -873 * (P.count(Them, QUEEN) ? 0 : 1),
        shelter: Math.trunc(-6 * score[0] / 8),
        mobility: mobility[Them][0] - mobility[Us][0],
        base: -30 };
      kingDanger += Object.values(parts).reduce((a, x)=>a + x, 0);
      const v = kingDanger > 0 ? [Math.trunc(kingDanger * kingDanger / 4096), Math.trunc(kingDanger / 16)] : ZERO;
      score = sub2(score, v);
      F.push({ term:'king', c:Us, kind:'danger', sq:ksq, v: mul2(v, -1), danger: kingDanger, parts, checks, weakRing: kingRing[Us] & weak,
               blockers: P.blockersForKing[Us], unsafeChecks });
    }
    if(!(P.both(PAWN) & kingFlank)){ score = sub2(score, PawnlessFlank); F.push({ term:'king', c:Us, kind:'pawnlessFlank', sq:ksq, v: mul2(PawnlessFlank, -1) }); }
    if(tropism){ score = sub2(score, mul2(CloseEnemies, tropism)); F.push({ term:'king', c:Us, kind:'tropism', sq:ksq, v: mul2(CloseEnemies, -tropism), n: tropism, squares: attackedBy[Them][ALL_PIECES] & kingFlank & Camp }); }
    kingScore[Us] = score;
  }
  T.king = kingScore;

  // threats
  const threatScore = [ZERO, ZERO];
  for(const Us of [WHITE, BLACK]){
    const Them = 1 - Us, Up = up(Us), TRank3BB = Us===WHITE ? RANK_BB[2] : RANK_BB[5];
    let score = ZERO;
    const note = (kind, s, v, extra)=>{ score = add2(score, v); F.push(Object.assign({ term:'threats', c:Us, kind, sq:s, v }, extra || {})); };
    const nonPawnEnemies = P.byColor[Them] ^ P.pieces(Them, PAWN);
    const stronglyProtected = attackedBy[Them][PAWN] | (attackedBy2[Them] & ~attackedBy2[Us]);
    const defended = nonPawnEnemies & stronglyProtected;
    const weak = P.byColor[Them] & ~stronglyProtected & attackedBy[Us][ALL_PIECES];
    let safe = (~attackedBy[Them][ALL_PIECES] & ALL) | attackedBy[Us][ALL_PIECES];
    if(defended | weak){
      for(const s of squares((defended | weak) & (attackedBy[Us][KNIGHT] | attackedBy[Us][BISHOP]))){
        const t = P.board[s].t;
        note('byMinor', s, ThreatByMinor[t], { target: t, weak: !!(weak & SQ[s]) });
        if(t!==PAWN) note('byRank', s, mul2(ThreatByRank, relRank(Them, s)));
      }
      for(const s of squares(weak & attackedBy[Us][ROOK])){
        const t = P.board[s].t;
        note('byRook', s, ThreatByRook[t], { target: t });
        if(t!==PAWN) note('byRank', s, mul2(ThreatByRank, relRank(Them, s)));
      }
      if(weak & attackedBy[Us][KING]) note('byKing', null, ThreatByKing, { squares: weak & attackedBy[Us][KING] });
      const b = (~attackedBy[Them][ALL_PIECES] & ALL) | (nonPawnEnemies & attackedBy2[Us]);
      for(const s of squares(weak & b)) note('hanging', s, Hanging, { target: P.board[s].t });
    }
    const restricted = attackedBy[Them][ALL_PIECES] & ~attackedBy[Them][PAWN] & ~attackedBy2[Them] & attackedBy[Us][ALL_PIECES];
    if(restricted) note('restricted', null, mul2(RestrictedPiece, popcount(restricted)), { squares: restricted, n: popcount(restricted) });
    if(P.pieces(Us, ROOK, QUEEN) && e.weakUnopposed[Them]) note('weakUnopposed', null, mul2(WeakUnopposedPawn, e.weakUnopposed[Them]), { n: e.weakUnopposed[Them] });
    let b = shift(P.pieces(Us, PAWN), Up) & ~P.all;
    b |= shift(b & TRank3BB, Up) & ~P.all;
    b &= ~attackedBy[Them][PAWN] & safe;
    const pushTargets = pawnAttacksBB(Us, b) & P.byColor[Them];
    for(const s of squares(pushTargets)) note('pawnPush', s, ThreatByPawnPush, { target: P.board[s].t, from: b & pawnAttacksBB(Them, SQ[s]) });
    b = P.pieces(Us, PAWN) & safe;
    for(const s of squares(pawnAttacksBB(Us, b) & nonPawnEnemies)) note('safePawn', s, ThreatBySafePawn, { target: P.board[s].t, from: b & pawnAttacksBB(Them, SQ[s]) });
    if(P.count(Them, QUEEN)===1){
      const s = lsb(P.pieces(Them, QUEEN));
      const safe2 = mobilityArea[Us] & ~stronglyProtected;
      const kn = attackedBy[Us][KNIGHT] & KnightAttacks[s] & safe2;
      if(kn) note('knightOnQueen', s, mul2(KnightOnQueen, popcount(kn)), { squares: kn });
      const sl = ((attackedBy[Us][BISHOP] & bishopAttacks(s, P.all)) | (attackedBy[Us][ROOK] & rookAttacks(s, P.all))) & safe2 & attackedBy2[Us];
      if(sl) note('sliderOnQueen', s, mul2(SliderOnQueen, popcount(sl)), { squares: sl });
    }
    threatScore[Us] = score;
  }
  T.threats = threatScore;

  // passed pawns
  const passedScore = [ZERO, ZERO];
  for(const Us of [WHITE, BLACK]){
    const Them = 1 - Us, Up = up(Us);
    const kp = (c, s)=>Math.min(dist(P.ksq(c), s), 5);
    let score = ZERO;
    for(const s of squares(e.passedPawns[Us])){
      const r = relRank(Us, s);
      let bonus = PassedRank[r];
      if(r > 2){
        const w = (r - 2) * (r - 2) + 2, blockSq = s + Up;
        bonus = add2(bonus, [0, (kp(Them, blockSq) * 5 - kp(Us, blockSq) * 2) * w]);
        if(r !== 6) bonus = sub2(bonus, [0, kp(Us, blockSq + Up) * w]);
        if(!(P.all & SQ[blockSq])){
          let defendedSquares, unsafeSquares, squaresToQueen;
          defendedSquares = unsafeSquares = squaresToQueen = ForwardFileBB[Us][s];
          const bb = ForwardFileBB[Them][s] & P.both(ROOK, QUEEN) & rookAttacks(s, P.all);
          if(!(P.byColor[Us] & bb)) defendedSquares &= attackedBy[Us][ALL_PIECES];
          if(!(P.byColor[Them] & bb)) unsafeSquares &= attackedBy[Them][ALL_PIECES] | P.byColor[Them];
          let k = !unsafeSquares ? 20 : !(unsafeSquares & SQ[blockSq]) ? 9 : 0;
          if(defendedSquares===squaresToQueen) k += 6;
          else if(defendedSquares & SQ[blockSq]) k += 4;
          bonus = add2(bonus, [k * w, k * w]);
        }
      }
      const candidate = !!(P.pieces(Them, PAWN) & PassedPawnMask[Us][s + Up]) || !!(P.both(PAWN) & ForwardFileBB[Us][s]);
      if(candidate) bonus = div2(bonus, 2);
      const v = add2(bonus, PassedFile[fileOf(s)]);
      score = add2(score, v);
      F.push({ term:'passed', c:Us, kind: candidate ? 'candidate' : 'passed', sq:s, v });
    }
    passedScore[Us] = score;
  }
  T.passed = passedScore;

  // space
  const spaceScore = [ZERO, ZERO];
  if(npmW + npmB >= SpaceThreshold) for(const Us of [WHITE, BLACK]){
    const Them = 1 - Us;
    const SpaceMask = Us===WHITE ? CenterFiles & (RANK_BB[1] | RANK_BB[2] | RANK_BB[3]) : CenterFiles & (RANK_BB[6] | RANK_BB[5] | RANK_BB[4]);
    const safe = SpaceMask & ~P.pieces(Us, PAWN) & ~attackedBy[Them][PAWN];
    let behind = P.pieces(Us, PAWN);
    behind |= Us===WHITE ? behind >> 8n : (behind << 8n) & ALL;
    behind |= Us===WHITE ? behind >> 16n : (behind << 16n) & ALL;
    const bonus = popcount(safe) + popcount(behind & safe);
    const weight = P.count(Us, ALL_PIECES) - 2 * e.openFiles;
    spaceScore[Us] = [Math.trunc(bonus * weight * weight / 16), 0];
    F.push({ term:'space', c:Us, kind:'space', sq:null, v: spaceScore[Us], safe, behind: behind & safe, weight });
  }
  T.space = spaceScore;
  for(const t of ['king', 'threats', 'passed', 'space']) score = add2(score, sub2(T[t][WHITE], T[t][BLACK]));

  // initiative
  const wk = P.ksq(WHITE), bk = P.ksq(BLACK);
  const outflanking = Math.abs(fileOf(wk) - fileOf(bk)) - Math.abs(rankOf(wk) - rankOf(bk));
  const pawnsOnBothFlanks = !!(P.both(PAWN) & QueenSide) && !!(P.both(PAWN) & KingSide);
  const complexity = 8 * e.asymmetry + 12 * (P.count(WHITE, PAWN) + P.count(BLACK, PAWN)) + 12 * outflanking
                   + 16 * (pawnsOnBothFlanks ? 1 : 0) + 48 * ((npmW + npmB) ? 0 : 1) - 118;
  const eg = score[1];
  const iv = Math.sign(eg) * Math.max(complexity, -Math.abs(eg));
  T.initiative = [0, iv];
  score = add2(score, [0, iv]);
  F.push({ term:'initiative', c: iv >= 0 ? WHITE : BLACK, kind:'initiative', sq:null, v:[0, iv], complexity, asymmetry: e.asymmetry, outflanking, pawnsOnBothFlanks });
  T.total = score;
  out.attackedBy = attackedBy; out.attackedBy2 = attackedBy2; out.mobilityArea = mobilityArea; out.pieceAttacks = pieceAttacks;
  out.pawnEntry = e; out.blockersForKing = P.blockersForKing;
  return out;
}

// The trace as Stockfish prints it (pawns, two decimals), for comparison with the engine.
function traceRows(fen){
  const r = evaluate(fen), T = r.trace;
  // two decimals as C++ prints them (exact halves round to even)
  const f = v=>{ const a = Math.abs(v) * 100; let q = Math.floor(a / PawnValueEg); const rem = a - q * PawnValueEg;
    if(rem * 2 > PawnValueEg || (rem * 2===PawnValueEg && q % 2)) q++;
    return (v < 0 && q ? '-' : '') + (q / 100).toFixed(2); };
  if(r.special) return { special: r.special };
  const row = (wb)=>({ w:[f(wb[0][0]), f(wb[0][1])], b:[f(wb[1][0]), f(wb[1][1])], t:[f(wb[0][0] - wb[1][0]), f(wb[0][1] - wb[1][1])] });
  const tot = v=>({ t:[f(v[0]), f(v[1])] });
  return { Material: tot(T.material), Imbalance: tot(T.imbalance), Initiative: tot(T.initiative), Pawns: row(T.pawns), Knights: row(T.knights),
    Bishops: row(T.bishops), Rooks: row(T.rooks), Queens: row(T.queens), Mobility: row(T.mobility), 'King safety': row(T.king),
    Threats: row(T.threats), Passed: row(T.passed), Space: row(T.space), Total: tot(T.total) };
}

const api = { evaluate, traceRows, PawnValueEg, WHITE, BLACK, PIECE: { PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING }, squares, popcount };
if(typeof module!=='undefined' && module.exports) module.exports = api; else root.SFEval = api;
})(typeof self!=='undefined' ? self : this);
