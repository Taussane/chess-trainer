// Position finder rules — every threshold the finder uses, and nothing else.
// Mirrors the "Position finder rules" doc. Change a rule here (and in the doc), bump VERSION.
module.exports = {
  VERSION: '2026-10-22.1',

  // The app's own engine (Stockfish 19 lite in the page), 1.2 s per search, as for a player's own games:
  // one calibration for both (2026-10-22: 1.2 s matches depth 18 as well as 2 s does; safety margins below).
  ENGINE: { movetime: 1200, multipv: 5 },

  // Grades: points of winning chances (Lichess win% curve) below the best move.
  GRADES: [ ['Good', 0], ['Ok', 3], ['Dubious', 10], ['Mistake', 20], ['Blunder', 30] ],

  GENERAL: {
    minMove: 5,            // full-move number of the position
    maxMove: 40,
    minLegalMoves: 4,
    // also: previous move not a capture that can simply be taken back;
    // not in a mate already under way (its start is allowed).
  },

  ANALYSIS: {
    decisiveGamesOnly: true,       // 1-0 or 0-1
    notInCheck: true,
    spacingPlies: 7,               // 7 half-moves between kept positions (alternates the side to move)
    retryPlies: 3,                 // if a sampled position fails, try up to 3 more half-moves
    maxMaterialDiff: 3,            // pawn 1, knight/bishop 3, rook 5, queen 9: beyond it, only when not decided:
    bigMaterialMaxWin: 85,         // the side ahead in material has less than 85% winning chances (about +4.7),
                                   // so a big material gap never gives the answer away (it can be compensated, or not)
    earlyBalanced: { plies: 14, maxEval: 100 },   // in the first 14 half-moves after the middlegame starts,
                                   // a position within ±1.00 of equal is skipped (masters and own games)
    // phases: Lichess Divider (middlegame start .. endgame start)
  },

  CANDIDATES: {
    trapTopN: 5,                   // a trap among the top 5: a move losing 12+ points of winning chances
    trapMinDrop: 12,               // (10 = Dubious, plus a 2-point margin: the live search can differ a little)
    spacingPlies: 7,               // 7 half-moves between kept positions from the same game
  },

  FINAL: {
    topN: 5,                       // moves are picked from the top 5 (+ the game move); the app re-picks them at runtime by the same rule
    // The four moves must be spread: the worst loses 18+ points (15, plus a 3-point margin) and ranking
    // them at random scores 57% or less on average (60, minus a 3-point margin). The grades themselves
    // no longer decide (exact grade lines flip too easily between two searches).
    worstMinDrop: 18,
    maxRandomAccuracy: 57,         // average accuracy of all 24 orders must be at most this
    spacingPlies: 2,               // 2 half-moves between kept positions from the same game
    weights: [0.5, 0.3, 0.2],      // the app's scoring rule (best remaining move, Dubious cap)
  },
};
