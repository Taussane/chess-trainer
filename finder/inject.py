# Copies the pools from a finder run into the app (the /*POOLS*/ ... /*END POOLS*/ block of app/index.html).
# Usage: python3 finder/inject.py data/pools.json
import json, re, sys, pathlib
src = sys.argv[1]
app = pathlib.Path(__file__).resolve().parent.parent / 'app' / 'index.html'
d = json.load(open(src))
def slim(e):
    o = {k: e[k] for k in ('key','fen','side','moveNo','title','year','last','hist')}
    if 'final' in e: o['final'] = e['final']['moves']
    return o
pools = {k: [slim(e) for e in v] for k, v in d['pools'].items()}
s = app.read_text()
assert '/*POOLS*/' in s and '/*END POOLS*/' in s, 'POOLS markers not found in app/index.html'
s = re.sub(r'/\*POOLS\*/.*?/\*END POOLS\*/', lambda m: '/*POOLS*/' + json.dumps(pools, ensure_ascii=False, separators=(',',':')) + '/*END POOLS*/', s, flags=re.S)
app.write_text(s)
print({k: len(v) for k, v in pools.items()}, 'rules', d.get('version'))
