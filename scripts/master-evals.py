# Writes master-evals.json (published with the site): for every master position in the app, what the
# position finder found with the app's own engine (1.2 s, from finder/.cache): its top 3 moves and the
# best one's evaluation, and for a Move selection position its four moves, best first (from their one search).
# The app loads it in the background and uses it when a position's own search hasn't had time yet:
# Candidate moves' review compares your picks with the top 3 (candidatesEval); Move selection shows the
# four moves at once and searches only them (finalMoves). Small on purpose.
# Usage: python3 scripts/master-evals.py   (after the finder; needs finder/.cache/searches.jsonl)
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
pools = json.loads((ROOT / 'data' / 'pools.json').read_text())['pools']
want, four = {}, {}
for v in pools.values():
    for e in v: want[e['fen']] = e['key']
for e in pools['final']:
    if e.get('final') and len(e['final']['moves']) == 4: four[e['fen']] = e['final']['moves']
wp = lambda l: 100.0 if l.get('mate') is not None and l['mate'] > 0 else 0.0 if l.get('mate') is not None else 50 + 50 * (2 / (1 + 2.718281828459045 ** (-0.00368208 * l['cp'])) - 1)
fours = {}
best = {}
with open(ROOT / 'finder' / '.cache' / 'searches.jsonl') as f:
    for line in f:
        try: k, v = json.loads(line)
        except Exception: continue
        parts = k.split('|')
        if len(parts) != 5 or parts[0] != 'Stockfish 19 lite (app)' or parts[1] != 'mt1200': continue
        if parts[2] == '4' and parts[3] in four and parts[4] == ' '.join(four[parts[3]]) and len(v) == 4:
            fours[parts[3]] = [x['uci'] for x in sorted(v, key=lambda x: -wp(x))]
            continue
        if parts[2] != '5' or parts[4]: continue
        if parts[3] in want and v:
            l = v[0]
            best[want[parts[3]]] = [[x['uci'] for x in v[:3]], l['cp'] if l.get('mate') is None else None, l.get('mate')]
for fen, f in fours.items():
    if want[fen] in best: best[want[fen]].append(f)
out = ROOT / 'master-evals.json'
out.write_text(json.dumps(best, separators=(',', ':')))
print(len(best), 'of', len(want), 'positions,', len(fours), 'of', len(four), 'with their four moves,', out.stat().st_size // 1024, 'KB')
