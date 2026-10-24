# Writes master-evals.json (published with the site): for every master position in the app, the top 3
# moves and the best one's evaluation the position finder found (the app's own engine, 1.2 s, from finder/.cache).
# The app loads it in the background and uses it when a position's own search hasn't had time yet
# (Candidate moves' review: see candidatesEval, which compares your picks with up to 3 moves). Small on purpose.
# Usage: python3 scripts/master-evals.py   (after the finder; needs finder/.cache/searches.jsonl)
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
pools = json.loads((ROOT / 'data' / 'pools.json').read_text())['pools']
want = {}
for v in pools.values():
    for e in v: want[e['fen']] = e['key']
best = {}
with open(ROOT / 'finder' / '.cache' / 'searches.jsonl') as f:
    for line in f:
        try: k, v = json.loads(line)
        except Exception: continue
        parts = k.split('|')
        if len(parts) != 5 or parts[0] != 'Stockfish 19 lite (app)' or parts[1] != 'mt1200' or parts[2] != '5' or parts[4]: continue
        if parts[3] in want and v:
            l = v[0]
            best[want[parts[3]]] = [[x['uci'] for x in v[:3]], l['cp'] if l.get('mate') is None else None, l.get('mate')]
out = ROOT / 'master-evals.json'
out.write_text(json.dumps(best, separators=(',', ':')))
print(len(best), 'of', len(want), 'positions,', out.stat().st_size // 1024, 'KB')
