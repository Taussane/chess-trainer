# Writes each master game's date ("1981-05-12", or "1981" when only the year is known) into the app
# (the /*GAME_DATES*/ ... /*END GAME_DATES*/ block of app/index.html), shown under the board.
# Game ids are the finder's: g0, g1, … in the order of library/gm-classics.pgn (checked against data/stats.json).
# Usage: python3 scripts/master-dates.py   (inject.py runs it too)
import json, re, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
pgn = (root/'library'/'gm-classics.pgn').read_text(encoding='utf-8')
games = [g for g in re.split(r'\n\s*\n(?=\[Event )', pgn) if g.strip().startswith('[Event ')]
stats = json.load(open(root/'data'/'stats.json', encoding='utf-8'))['games']
assert len(games) == len(stats), (len(games), len(stats))
dates = {}
for i, (g, s) in enumerate(zip(games, stats)):
    h = dict(re.findall(r'^\[(\w+)\s+"([^"]*)"\]', g, re.M))
    assert s['id'] == 'g%d' % i and h.get('White') == s['white'], (i, h.get('White'), s['white'])
    y, m, d = (h.get('Date', '????.??.??') + '.??.??').split('.')[:3]
    if y.isdigit(): dates[s['id']] = y + ('-' + m + ('-' + d if d.isdigit() else '') if m.isdigit() else '')
app = root/'app'/'index.html'; s = app.read_text(encoding='utf-8')
assert '/*GAME_DATES*/' in s
s = re.sub(r'/\*GAME_DATES\*/.*?/\*END GAME_DATES\*/', lambda m: '/*GAME_DATES*/' + json.dumps(dates, separators=(',',':')) + '/*END GAME_DATES*/', s, flags=re.S)
app.write_text(s, encoding='utf-8')
print(len(dates), 'dates,', sum(1 for v in dates.values() if len(v) == 10), 'with month and day')
