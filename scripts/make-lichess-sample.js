// Builds a Lichess-style PGN export for testing "My games": games from library/gm-classics.pgn
// re-labelled as a fictional player's online games, in Lichess's export format. Half carry
// [%eval] comments (as Lichess adds for analysed games), computed here with Stockfish; the rest
// have none. One bullet game and one Chess960 game are included; the app should skip both.
// Usage: STOCKFISH=/path/to/stockfish node scripts/make-lichess-sample.js out.pgn [games=10]
const fs = require('fs'), path = require('path');
const { spawn } = require('child_process');
const { Chess } = require('../vendor/chess.js/chess.js');
const SF = process.env.STOCKFISH || path.join(__dirname, '../engine/stockfish');
const [out, nArg] = process.argv.slice(2);
const N = +(nArg || 10);
const lib = fs.readFileSync(path.join(__dirname, '../library/gm-classics.pgn'), 'utf8').split(/(?=\[Event )/).filter(g=>g.includes('[White'));
const header = (g,k)=>{ const m = g.match(new RegExp('\\['+k+' "([^"]*)"\\]')); return m ? m[1] : ''; };
const sf = spawn(SF); let buf = '', wait = null;
sf.stdout.on('data', d=>{ buf += d; if(wait && buf.includes('bestmove')){ const o = buf; buf = ''; const w = wait; wait = null; w(o); } });
const evalFen = fen=>new Promise(r=>{ wait = r; sf.stdin.write(`position fen ${fen}\ngo depth 10\n`); }).then(o=>{
  const ls = o.split('\n').filter(l=>/^info .* score /.test(l)); const l = ls[ls.length-1] || '';
  const m = l.match(/score (cp|mate) (-?\d+)/); if(!m) return '0.00';
  const s = fen.split(' ')[1]==='w' ? 1 : -1, v = s*(+m[2]);
  return m[1]==='mate' ? '#'+v : (v/100).toFixed(2);
});
const ids = 'AbCdEfGh JkLmNpQr StUvWxYz aBcDeFgH jKlMnPqR sTuVwXyZ HgFeDcBa RqPnMlKj ZyXwVuTs HgFeDcBz XyZaBcDe QwErTyUi'.split(' ');
(async()=>{
  const games = [];
  for(let i=0; i<N; i++){
    const g = lib[i*3 % lib.length], me = i%2 ? 'b' : 'w';
    const c = new Chess(); const body = g.replace(/^\[.*\]\s*$/mg,'').replace(/\{[^}]*\}/g,'').replace(/\d+\.(\.\.)?/g,' ').split(/\s+/).filter(t=>t && !/^(1-0|0-1|1\/2-1\/2|\*)$/.test(t));
    const sans = []; for(const t of body){ const m = c.move(t, {sloppy:true}); if(!m) break; sans.push(m.san); }
    const withEvals = i < N/2, speed = i===N-1 ? 'Bullet' : ['Blitz','Rapid','Classical'][i%3];
    const tc = { Bullet:'60+0', Blitz:'180+2', Rapid:'600+5', Classical:'1800+20' }[speed];
    const opp = ['knightowl','pawnstorm42','rookie_rook','fianchetto_fan','zugzwanger'][i%5];
    const W = me==='w' ? 'TestPlayer' : opp, B = me==='w' ? opp : 'TestPlayer';
    let txt = `[Event "Rated ${speed} game"]\n[Site "https://lichess.org/${ids[i]}"]\n[Date "2026.09.${String(10+i).padStart(2,'0')}"]\n[White "${W}"]\n[Black "${B}"]\n[Result "${header(g,'Result')}"]\n[UTCDate "2026.09.${String(10+i).padStart(2,'0')}"]\n[WhiteElo "1650"]\n[BlackElo "1640"]\n[Variant "Standard"]\n[TimeControl "${tc}"]\n[Termination "Normal"]\n\n`;
    const r = new Chess(); const parts = [];
    for(let k=0; k<sans.length; k++){
      const mv = r.move(sans[k]); const num = k%2===0 ? `${k/2+1}. ` : (withEvals ? `${(k-1)/2+1}... ` : '');
      let comment = '';
      if(withEvals) comment = ` { [%eval ${await evalFen(r.fen())}] }`;
      parts.push(num + mv.san + comment);
    }
    txt += parts.join(' ') + ' ' + header(g,'Result') + '\n\n';
    games.push(txt);
    process.stderr.write(`${i+1}/${N} ${W} – ${B} ${speed}${withEvals ? ' with evals' : ''}\n`);
  }
  games.push(`[Event "Rated Blitz game"]\n[Site "https://lichess.org/Chess960x"]\n[Date "2026.09.30"]\n[White "TestPlayer"]\n[Black "knightowl"]\n[Result "1-0"]\n[Variant "Chess960"]\n[TimeControl "180+2"]\n[FEN "bbqnnrkr/pppppppp/8/8/8/8/PPPPPPPP/BBQNNRKR w HFhf - 0 1"]\n[SetUp "1"]\n\n1. e4 e5 2. Nd3 Nd6 1-0\n\n`);
  fs.writeFileSync(out, games.join(''));
  sf.kill();
})();
