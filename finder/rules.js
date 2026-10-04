// Position finder rules — every threshold the finder uses, and nothing else.
// Mirrors the "Position finder rules" doc. Change a rule here (and in the doc), bump VERSION.
module.exports = {
  VERSION: '2026-10-04.2',

  ENGINE: { depth: 18, multipv: 5, threads: 2, hash: 256 },

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
    maxMaterialDiff: 3,            // pawn 1, knight/bishop 3, rook 5, queen 9
    // phases: Lichess Divider (middlegame start .. endgame start)
  },

  CANDIDATES: {
    trapTopN: 5,                   // at least 1 Dubious-or-worse move among the top 5
    trapMinDrop: 10,
    spacingPlies: 7,               // 7 half-moves between kept positions from the same game
  },

  FINAL: {
    topN: 5,                       // moves are picked from the top 5 (+ the game move); the app re-picks them at runtime by the same rule
    minGrades: 3,                  // at least 3 different grades among top 5 + game move
    uniqueGrades: ['Dubious', 'Mistake', 'Blunder'],   // at most one of the four moves per bad grade
    maxRandomAccuracy: 60,         // average accuracy of all 24 orders must be at most this
    weights: [0.5, 0.3, 0.2],      // the app's scoring rule (best remaining move, Dubious cap)
  },
};
