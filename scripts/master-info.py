# Writes each master game's players ("Botvinnik – Tal"), the day it joined the library (Added), its date ("1981-05-12", or "1981" when only the year is known) and short event
# name (the library's EventShort header, written by hand: "USSR Championship", "Leipzig Olympiad"…)
# into the app (the /*GAME_INFO*/ ... /*END GAME_INFO*/ block of app/index.html), shown above the board.
# Game ids are the finder's: g0, g1, … in the order of library/gm-classics.pgn (checked against data/stats.json).
# Usage: python3 scripts/master-info.py   (inject.py runs it too)
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
    info = {}
    if y.isdigit(): info['date'] = y + ('-' + m + ('-' + d if d.isdigit() else '') if m.isdigit() else '')
    if h.get('EventShort'): info['event'] = h['EventShort']
    info['title'] = h.get('White', '').split(',')[0].strip() + ' – ' + h.get('Black', '').split(',')[0].strip()
    ad = re.match(r'^(\d{4})\.(\d{2})\.(\d{2})$', h.get('Added', ''))
    if ad:
        import calendar
        info['added'] = calendar.timegm((int(ad[1]), int(ad[2]), int(ad[3]), 0, 0, 0)) * 1000
    dates[s['id']] = info
app = root/'app'/'index.html'; s = app.read_text(encoding='utf-8')
assert '/*GAME_INFO*/' in s
s = re.sub(r'/\*GAME_INFO\*/.*?/\*END GAME_INFO\*/', lambda m: '/*GAME_INFO*/' + json.dumps(dates, ensure_ascii=False, separators=(',',':')) + '/*END GAME_INFO*/', s, flags=re.S)
app.write_text(s, encoding='utf-8')
print(len(dates), 'games,', sum(1 for v in dates.values() if 'event' in v), 'with an event')
