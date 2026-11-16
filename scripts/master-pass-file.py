# Writes master-pass.json (published with the site): each master game's pass, as the game review reads it. For every
# position, its best move and evaluation for the side to play (the pass's up to move 40, the review's search after it):
# { "g0": "  g8f6:-23 c2c4:28 …" } (one entry per half-move from the start, space-separated, empty when not searched;
# "m3" for a mate in 3). Loaded by the explorer when a master game is opened, so its review starts where the pass
# stopped instead of searching the whole game again.
# Usage: python3 scripts/master-pass-file.py   (after STEP=pass and STEP=review of scripts/masters-pass.js: finder/.cache/pass/, rv/)
import json, os, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
d = root / 'finder' / '.cache' / 'pass'
out = {}
for f in sorted(os.listdir(d), key=lambda f: int(f[1:-5])):
    p = json.load(open(d / f, encoding='utf-8'))
    l = p.get('l', {})
    n = max(map(int, l)) + 1 if l else 0
    rf = root / 'finder' / '.cache' / 'rv' / f
    rv = json.load(open(rf, encoding='utf-8')) if rf.exists() else {}
    n = max([n] + [int(k) + 1 for k in rv])
    out[f[:-5]] = ' '.join((l.get(str(i)) or '').split(',')[0] or rv.get(str(i), '') for i in range(n))
(root / 'master-pass.json').write_text(json.dumps(out, separators=(',', ':')), encoding='utf-8')
print(len(out), 'games,', sum(len([x for x in v.split(' ') if x]) for v in out.values()), 'positions')
