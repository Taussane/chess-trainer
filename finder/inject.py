# Copies the pools from a finder run (positions only; the app picks and evaluates moves itself) into the app (the /*POOLS*/ ... /*END POOLS*/ block of app/index.html).
# Usage: python3 finder/inject.py data/pools.json
import json, re, sys, pathlib
src = sys.argv[1]
app = pathlib.Path(__file__).resolve().parent.parent / 'app' / 'index.html'
d = json.load(open(src, encoding='utf-8'))
assert 'player' not in d, 'this is a player\'s own games (finder/own.js output); only master pools go into POOLS'
def slim(e):
    o = {k: e[k] for k in ('key','fen','side','moveNo','title','year','last','hist')}
    return o
pools = {k: [slim(e) for e in v] for k, v in d['pools'].items()}
s = app.read_text(encoding='utf-8')
assert '/*POOLS*/' in s and '/*END POOLS*/' in s, 'POOLS markers not found in app/index.html'
s = re.sub(r'/\*POOLS\*/.*?/\*END POOLS\*/', lambda m: '/*POOLS*/' + json.dumps(pools, ensure_ascii=False, separators=(',',':')) + '/*END POOLS*/', s, flags=re.S)
stats = pathlib.Path(src).with_name('stats.json')
if stats.exists():
    n = len(json.load(open(stats, encoding='utf-8'))['games'])
    s = re.sub(r'/\*POOLS_GAMES\*/.*?/\*END POOLS_GAMES\*/', '/*POOLS_GAMES*/%d/*END POOLS_GAMES*/' % n, s)
app.write_text(s, encoding='utf-8')
print({k: len(v) for k, v in pools.items()}, 'rules', d.get('version'))
