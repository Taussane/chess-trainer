# Builds the guides (learn/: one page per exercise, and their index) and the sitemap, for search engines and
# for anyone who wants to know what an exercise trains before trying it. Plain pages, no script.
# Run by scripts/build-site.py (so `build-site.py --check` covers them too); the text lives here.
# The pictures (learn/img/) are the app's own screens on master positions, as a new visitor gets them.
import pathlib, json, html, re
root = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://chessstrategy.org/'

# Each guide: its address (learn/<slug>/), the exercise it opens (?play=), and its text (HTML).
GUIDES = [
  dict(slug='chess-imbalances', play='imbalances', name='Imbalance reading', img='imbalance-reading',
    title='Chess imbalances: learn to read a position',
    desc='What chess imbalances are (material, pawns, space, activity, king safety, threats), how to weigh them, and a free exercise to practise reading them on master games and your own games.',
    lead="Every position is a set of differences between the two sides: an extra pawn, a weak square, a safer king. Strong players don't weigh them all. They spot the few that decide the game, and they plan around those.",
    alt='Imbalance reading review on a 1929 World Championship position: Activity and Pawns to White, Space to Black, all three answers right',
    caption='Bogoljubow – Alekhine, World Championship match 1929, Black to play. Three answers, all right: White has the more active pieces and the better pawns, Black has more space.',
    body="""
<h2>What an imbalance is</h2>
<p>An imbalance is any lasting or temporary difference between White's and Black's position. The idea was popularised by Jeremy Silman: instead of looking for a move straight away, first list what is different, then choose the plan that makes the most of your edges.</p>
<p>The exercise uses six of them, each counted on the board the same way every time:</p>
<ul>
  <li><strong>Material</strong>: pawn 1, knight 3, bishop 3, rook 5, queen 9; the bishop pair adds half a pawn.</li>
  <li><strong>Pawns</strong>: passed and connected pawns count more the further they've come; isolated, doubled and backward pawns count against.</li>
  <li><strong>Space</strong>: pawns and safe squares behind them in the centre of the board (not counted once few pieces are left).</li>
  <li><strong>Activity</strong>: the safe squares your knights, bishops, rooks and queen reach, plus outposts and open files. Early in the game, <strong>Development</strong> takes its place.</li>
  <li><strong>King safety</strong>: pawns sheltering the king against enemy pieces aiming at it. Once queens are off, <strong>King activity</strong> takes its place: in the endgame the king becomes a fighter.</li>
  <li><strong>Other threats</strong>: material you can win right now.</li>
</ul>
<p>Material, Pawns and Space are <em>static</em>: they last. Activity, King safety and threats are <em>dynamic</em>: they can disappear in a few moves, so they call for action.</p>

<h2>How the exercise works</h2>
<p>You get a position from a master game, or from one of your own games. Choose the <strong>3 imbalances that decide it</strong>, and for each one say who has the edge, White or Black.</p>
<p>Then the review shows every imbalance with its real size. Each of your choices counts for a third of the score: one of the three biggest edges on the right side gets full points, a smaller edge on the right side gets half, a balanced one or the wrong side gets nothing. Tap any imbalance to see on the board how it was counted.</p>

<h2>Tips</h2>
<ul>
  <li>Look for the big edges first, then the clearest small ones.</li>
  <li>Don't choose an imbalance that's balanced: it scores nothing.</li>
  <li>Grades don't simply add up. One big imbalance can outweigh several small ones, and tactics beat them all.</li>
</ul>

<h2>Why it helps</h2>
<p>Reading imbalances is the step before every plan. It tells you whether to trade pieces, where to attack, which pawn to target, and when to hurry. Done on hundreds of positions, it becomes a habit you bring to your own games. The <a href="../chess-plans/">Plan finder</a> takes the next step: from the imbalances to a plan.</p>
"""),
  dict(slug='chess-plans', play='planq', name='Plan finder', img='plan-finder',
    title='How to find a plan in chess',
    desc="How to make a plan in chess: check what's urgent, judge who is better, then decide whether to trade and whether to attack or improve. A free exercise on master positions and your own games.",
    lead="\"What do I do now?\" is the question behind most bad moves. A plan doesn't need to be long. It comes from a few clear decisions, made in the right order.",
    alt='Plan finder, first question on a 1935 World Championship position: anything urgent for White, and who is better',
    caption='Alekhine – Euwe, World Championship match 1935, White to play. First question: is anything urgent, and who is better?',
    body="""
<h2>Four decisions, in order</h2>
<p>The Plan finder splits planning into four questions, answered in two steps, the way a strong player thinks through a position.</p>
<h3>1. Anything urgent?</h3>
<p>Before any plan, what can't wait: checks, captures and threats, for both sides. The position is <strong>quiet</strong> (nothing to win or to parry right now), or the side to play <strong>can win</strong> something, or <strong>must defend</strong>. When a piece or more is at stake, that decides the move, and the plan comes later.</p>
<h3>2. Who's better?</h3>
<p>Judge the position as a whole: <strong>balanced</strong> (the engine within half a pawn), or one side <strong>better</strong>. Start with material, then what lasts (pawns, space), then what can change fast (pieces, kings).</p>
<h3>3. Trade, or keep pieces?</h3>
<p>Trades help the side that is up material, has the better pawns, is cramped, or has worse pieces. The other side wants to keep pieces: down material, more space, better pieces, or a weak enemy king. Sometimes the reasons cancel out, and either is fine.</p>
<h3>4. Attack, or improve?</h3>
<p>An edge that fades (better pieces, a lead in development, a weak enemy king) has to be used now: open the position and attack. An edge that lasts (material, pawns, space) gives you time: keep the position closed and improve your pieces first.</p>

<h2>How the exercise works</h2>
<p>You answer the first two questions, check, then the last two. Each answer counts for a quarter of the score. The review gives the main reason under each answer; tap it to see it on the board. The answers come from the position's imbalances (see <a href="../chess-imbalances/">Imbalance reading</a>) and from Stockfish, so they're the same rules every time, not someone's opinion.</p>

<h2>Tips</h2>
<ul>
  <li>Look at every check, capture and threat, yours and theirs, before judging anything else.</li>
  <li>A pawn that looks free may be poisoned: look at what follows.</li>
  <li>When unsure between attacking and improving, ask whether your edge will still be there in ten moves.</li>
</ul>
"""),
  dict(slug='candidate-moves', play='candidates', name='Candidate moves', img='candidate-moves',
    title='Candidate moves in chess: find more than one good move',
    desc='What candidate moves are, how to find them (checks, captures, threats, then the plan), and a free exercise grading your picks with Stockfish on master games and your own games.',
    lead="Most mistakes come from playing the first move that looks good. Candidate moves are the habit of finding a few serious options first, then choosing between them.",
    alt='Candidate moves review on a 1954 World Championship position: three picks, graded Best, Good and Good, beside the engine\'s top 3',
    caption='Smyslov – Botvinnik, World Championship match 1954, Black to play. Three picks, graded against the engine\'s best: Rxg5 (Best), Nf4 and Nc7 (Good).',
    body="""
<h2>What a candidate move is</h2>
<p>A candidate move is a move worth a serious look. The idea, made famous by Alexander Kotov, is to list them before calculating any of them, so you don't spend all your time on the first idea and miss a better one. In most positions, several moves are about equally good: finding them is the skill.</p>

<h2>How to find them</h2>
<ul>
  <li><strong>Forcing moves first</strong>: checks, captures and threats, for both sides. Even when you don't play them, they tell you what the opponent wants.</li>
  <li><strong>Then moves that follow the plan</strong>. In the opening: develop and castle. In the middlegame: play on the imbalances (see <a href="../chess-imbalances/">Imbalance reading</a>). In the endgame: activate the king, push passed pawns.</li>
  <li><strong>Check what each move allows</strong> before keeping it.</li>
</ul>

<h2>How the exercise works</h2>
<p>Pick 1 to 3 strong moves for the side to play, by playing them on the board. Stockfish then grades each one against its best move: <strong>Best</strong>, <strong>Good</strong>, <strong>Ok</strong>, <strong>Dubious</strong>, <strong>Mistake</strong> or <strong>Blunder</strong>, depending on how much winning chance the move gives up. Dubious or worse scores zero, so picking fewer, better moves pays. The review shows the engine's own top 3 beside yours.</p>

<h2>Tips</h2>
<ul>
  <li>Unsure about a move? Leave it out. Two good moves beat two good and one bad.</li>
  <li>Count the forcing moves even when the position looks quiet: that's where the surprises are.</li>
  <li>When you've found one good move, look for a second. That's the habit this trains.</li>
</ul>
<p>Next step: <a href="../move-selection/">Move selection</a>, choosing the best among several.</p>
"""),
  dict(slug='move-selection', play='final', name='Move selection', img='move-selection',
    title='How to choose the best move in chess',
    desc='How to choose between good-looking moves in chess: find the best one, then check what each move allows. A free exercise ranking four moves from master games and your own mistakes.',
    lead="Finding good moves is half the job. The other half is choosing: several moves look fine, and only one is best. Move selection trains that last decision.",
    alt='Move selection review on a 1963 World Championship position: four moves ranked, the game move Nxe4 best, two dubious ones',
    caption='Botvinnik – Petrosian, World Championship match 1963, White to play. Four moves to rank: the game move Nxe4 is best, Qh2 is good, Rh2 and Qg2 are dubious.',
    body="""
<h2>How the exercise works</h2>
<p>You get four moves for the side to play: <strong>rank them, best first</strong>. One of them was played in the game. In master games, the master's move is often the best, but not always. In your own games, it's your move, and it's always a mistake: the exercise gives you another shot at a decision you got wrong.</p>
<p>The score rewards the top of the ranking most: 1st place counts for 50%, 2nd for 30%, 3rd for 20%. Each place is compared with the best move left, so a good second choice still scores even if the first one was wrong. The review shows Stockfish's grade and evaluation for each move.</p>

<h2>How to choose</h2>
<ul>
  <li><strong>Find the best move first</strong>: it's half the score, and in a game it's the whole point.</li>
  <li><strong>Check what each move allows</strong>: a move that drops material or exposes the king goes last, however active it looks.</li>
  <li><strong>Compare against the plan</strong>: with the imbalances in mind (see <a href="../chess-imbalances/">Imbalance reading</a>), the move that serves your edge usually beats the one that looks busy.</li>
</ul>

<h2>Your own games</h2>
<p>Connect Lichess, or add your Chess.com username, and the app goes through your recent games, finds the moments you went wrong, and turns them into exercises. You meet your real decisions again, with the better moves beside yours.</p>
"""),
]


# The FAQ (it used to be a screen in the app): what the guides don't already say, at the bottom of the guides' index.
# Answers are HTML; the structured data (FAQPage) gets them as plain text.
FAQ = [
  ('About the app', [
    ('What does it train?', "Strategy: what to do in a quiet position, when there's no tactic to find. Puzzle apps train tactics very well, but most games are decided in positions where the question isn't \"what wins?\" but \"what's going on, and what should I aim for?\"."),
    ('Who is it for?', "Club players who already know their tactics and feel stuck when the position is quiet: no plan, or a plan that doesn't fit the position."),
    ('How does it teach?', "By practice on real positions, with a review after each answer. Every idea is made concrete: an imbalance is a count of things on the board, drawn when you tap it, and every answer is checked by an engine or by a counted rule. The exercises follow the order of questions strong players ask."),
    ('Where do the ideas come from?', "From the classic books on strategy (Steinitz, Nimzowitsch, Capablanca, Kotov, Silman, Dvoretsky, Aagaard, Shereshevsky) and from Stockfish's former evaluation, which counts the same things in its own way."),
  ]),
  ('The thinking process', [
    ('Is there an order to thinking about a position?', "Yes. The books agree on one, and each exercise trains one step of it:<ol><li><b>Is anything urgent?</b> Checks, captures and threats, for both sides (Plan finder, phase 1).</li><li><b>What's different between the two sides?</b> The imbalances (Imbalance reading).</li><li><b>Who's better?</b> The imbalances weighed together decide your attitude: the side with the edge plays to use it, the other defends (Plan finder, phase 1).</li><li><b>What's the plan?</b> Trade or keep pieces; open and attack, or keep it closed and improve (Plan finder, phase 2).</li><li><b>Which moves?</b> Candidate moves that serve the plan, then the choice, checking each for a blunder (Candidate moves, Move selection).</li></ol>"),
    ('Why separate exercises, not one position from start to finish?', "Each step gets its own review right away. On a single position, the review of one step would give away the next, and a long chain makes each round slow. The daily routine runs the steps in order, each on its own position."),
    ("What about the opponent's plan?", "Checking the opponent's checks, captures and threats (step 1) is the first part of prophylaxis. The full question, \"what does my opponent want?\", may become an exercise of its own later."),
  ]),
  ('The exercises', [
    ('What do =, + and ++ mean in an Imbalance reading review?', "The size of the difference between the two sides, white for White, black for Black. You don't grade sizes, but the review shows them: the ++ ones are the big edges, the ones to find first. Each imbalance has its own thresholds: across the master positions, about half are \"=\", a third \"+\" and one in six \"++\"."),
    ('How does the Plan finder know something is urgent?', "Two checks must agree. The count of threats (Other threats, drawn on the board) says what each side could win. Stockfish then plays the position for the side to move, and again as if the other side were to move, to see what each would really win. Positions where they disagree are left out, so every answer can be shown on the board. A pawn that looks free but that Stockfish doesn't take is poisoned, or there's better: the answer is \"quiet\", and the review says what Stockfish prefers."),
    ("How is the Plan finder's answer decided?", "Each imbalance votes for the side to play (+ counts 1, ++ counts 2). A row goes to a side when its votes add up to 2 or more; otherwise the answer is Either. One vote short gives half the points for that side."),
    ("Are the Plan finder's answers always right?", "They're the books' principles applied to the position, not a calculated line: a plan is a direction, not the next move. Checked on master games, they hold when the imbalances agree: when nothing argues against a trade, masters tried to trade (took or offered) 56 to 67% of the time, against about 45% on average; and Stockfish finds forcing play good twice as often where the plan says \"attack\" as where it says \"improve\". When imbalances pull both ways, concrete reasons decide, and the answer is less certain."),
  ]),
  ('Scores and progress', [
    ("What's my average?", "Your accuracy in an exercise, smoothed over recent positions: at first a plain average, then each new position moves it 15% of the way toward its score. One bad position costs a little; a run of good ones lifts it steadily."),
    ("What's the daily routine?", "Three positions of each exercise in the day, in as many sittings as you like, in the thinking order."),
    ('What are missed positions?', "Positions you scored below your average at the time. Replay plays them again; scoring at or above your average takes one off the list. A position played today waits until tomorrow."),
    ('Where is my progress kept?', "In your browser, and in your account when you're logged in, so it follows you on every device."),
  ]),
  ('Positions and the engine', [
    ('Where do the positions come from?', "From World Championship games and, once connected, from your own Lichess and Chess.com games. In your games, the app looks for your mistakes: the position just before a move that lost a lot."),
    ('How are the positions picked?', "By rules, checked with Stockfish: quiet positions where strategy matters, spread across the game, not too close to each other, and for each exercise a reason to ask. Drawn games only give their unbalanced positions."),
    ('Which engine?', "Stockfish 19 (its \"lite\" version), running in your browser, so nothing is sent anywhere: each position is searched to depth 20, a few seconds at most. Master positions also come with their evaluation computed in advance."),
  ]),
  ('Credits and further reading', [
    ('Where do the sounds come from?', "The move and capture sounds are two sounds cut from <a href=\"https://freesound.org/s/792572/\">\"chess piece\" by imrius</a> (freesound.org), licensed under <a href=\"https://creativecommons.org/licenses/by/4.0/\">CC BY 4.0</a>. Changes: cut, background noise reduced, volume evened out."),
    ('Which books are behind the app?', "<ul><li><b>Jeremy Silman, <i>How to Reassess Your Chess</i>:</b> imbalances, and how they lead to a plan.</li><li><b>Aron Nimzowitsch, <i>My System</i>:</b> open files, outposts, pawn chains, blockade, prophylaxis.</li><li><b>José Raúl Capablanca, <i>Chess Fundamentals</i>:</b> the basics of every phase.</li><li><b>Alexander Kotov, <i>Think Like a Grandmaster</i>:</b> candidate moves and the order of thinking.</li><li><b>Mark Dvoretsky and Artur Yusupov, <i>Positional Play</i>:</b> prophylactic thinking.</li><li><b>Jacob Aagaard, <i>Grandmaster Preparation: Positional Play</i>:</b> three questions for any quiet position.</li><li><b>Mikhail Shereshevsky, <i>Endgame Strategy</i>:</b> the king, two weaknesses, and not hurrying.</li></ul>"),
  ]),
]

STYLE = """
  :root{ color-scheme: dark; --bg:#12161B; --panel:#1B2027; --line:#2A313A; --text:#EDE7DC; --mute:#9A9488; --accent:#C9A227; }
  *{ box-sizing:border-box; }
  body{ background:var(--bg); color:var(--text); margin:0; font:16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
  header, main, footer{ max-width:760px; margin:0 auto; padding:0 16px; }
  header{ display:flex; align-items:center; justify-content:space-between; padding-top:16px; padding-bottom:8px; }
  header a{ color:var(--text); text-decoration:none; } .brand{ display:flex; align-items:center; gap:10px; font-weight:600; }
  .brand img{ width:28px; height:28px; border-radius:7px; } header nav a{ color:var(--mute); font-size:.95rem; }
  h1{ font-size:1.9rem; line-height:1.2; margin:20px 0 10px; font-family:Georgia, "Times New Roman", serif; }
  h2{ font-size:1.25rem; margin:32px 0 8px; } h3{ font-size:1.05rem; margin:20px 0 4px; }
  .lead{ font-size:1.08rem; color:var(--text); } p, li{ color:var(--text); } .mute{ color:var(--mute); } a{ color:var(--accent); }
  ul{ padding-left:22px; } li{ margin:4px 0; }
  .cta{ display:inline-block; background:var(--accent); color:#12161B; font-weight:700; text-decoration:none; padding:12px 22px; border-radius:10px; margin:8px 0 4px; }
  figure{ margin:24px 0; text-align:center; } figure img{ width:100%; max-width:360px; height:auto; border-radius:14px; border:1px solid var(--line); }
  figcaption{ color:var(--mute); font-size:.92rem; max-width:520px; margin:8px auto 0; }
  .cards{ display:grid; gap:12px; grid-template-columns:1fr; margin:20px 0; } @media (min-width:640px){ .cards{ grid-template-columns:1fr 1fr; } }
  .card{ display:block; background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px 16px; text-decoration:none; }
  .card strong{ color:var(--text); display:block; margin-bottom:2px; } .card span{ color:var(--mute); font-size:.95rem; }
  .faq-h{ font-size:1rem; color:var(--mute); text-transform:uppercase; letter-spacing:.06em; margin:28px 0 6px; }
  details{ border-bottom:1px solid var(--line); } details summary{ cursor:pointer; padding:12px 0; font-weight:600; list-style:none; display:flex; justify-content:space-between; gap:12px; }
  details summary::-webkit-details-marker{ display:none; } details summary::after{ content:'+'; color:var(--mute); font-weight:400; } details[open] summary::after{ content:'−'; }
  details .a{ padding:0 0 12px; color:var(--mute); } details .a b{ color:var(--text); } details .a ol, details .a ul{ margin:6px 0 0; }
  footer{ border-top:1px solid var(--line); margin-top:40px; padding-top:16px; padding-bottom:40px; color:var(--mute); font-size:.92rem; }
  footer a{ color:var(--mute); }
"""

def page(path, title, desc, body, ld):
  depth = path.count('/')   # learn/x/index.html: 2 levels down from the site's root
  up = '../' * depth
  others = ' · '.join(f'<a href="{up}learn/{g["slug"]}/">{g["name"]}</a>' for g in GUIDES)
  return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · ChessStrategy.org</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{SITE}{path.removesuffix('index.html')}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ChessStrategy.org">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{SITE}{path.removesuffix('index.html')}">
<meta property="og:image" content="{SITE}icons/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#12161B">
<link rel="icon" type="image/svg+xml" href="{up}icons/icon.svg">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{STYLE}</style>
<!-- Built by scripts/build-learn.py: edit the script, not this file. -->
</head>
<body>
<header><a class="brand" href="{up}"><img src="{up}icons/icon.svg" alt="">ChessStrategy.org</a><nav><a href="{up}learn/">Guides</a> · <a href="{up}learn/#faq">FAQ</a></nav></header>
<main>
{body}
</main>
<footer>
  <p>Guides: {others}</p>
  <p><a href="{up}">ChessStrategy.org</a>: free, open-source chess strategy training, no ads. · <a href="{up}privacy.html">Privacy</a> · <a href="{up}terms.html">Terms</a> · <a href="https://github.com/Taussane/chess-trainer">Source code</a></p>
</footer>
</body>
</html>
"""

def crumbs(*items):
  return { '@type': 'BreadcrumbList', 'itemListElement': [{ '@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u } for i, (n, u) in enumerate(items)] }

def build():
  out = {}
  for g in GUIDES:
    path = f'learn/{g["slug"]}/index.html'
    body = f"""<p class="mute">Guide · {g['name']}</p>
<h1>{html.escape(g['title'])}</h1>
<p class="lead">{g['lead']}</p>
<p><a class="cta" href="../../?play={g['play']}">Try {g['name']}, free</a></p>
<figure><img src="../img/{g['img']}.webp" width="390" height="844" alt="{html.escape(g['alt'])}" loading="lazy"><figcaption>{g['caption']}</figcaption></figure>
{g['body'].strip()}
<h2>Try it</h2>
<p>{g['name']} is one of four exercises on ChessStrategy.org, free and without ads. Positions come from master games, such as World Championship matches, and from your own Lichess and Chess.com games. Answers are checked with fixed counting rules and Stockfish, which runs in your browser.</p>
<p><a class="cta" href="../../?play={g['play']}">Play {g['name']}</a></p>"""
    ld = [{ '@context': 'https://schema.org', '@type': 'Article', 'headline': g['title'], 'description': g['desc'],
            'image': SITE + f'learn/img/{g["img"]}.webp', 'url': SITE + f'learn/{g["slug"]}/',
            'publisher': { '@type': 'Organization', 'name': 'ChessStrategy.org', 'url': SITE } },
          { '@context': 'https://schema.org', **crumbs(('Guides', 'learn/'), (g['name'], f'learn/{g["slug"]}/')) }]
    out[path] = page(path, g['title'], g['desc'], body, ld)
  cards = ''.join(f'<a class="card" href="{g["slug"]}/"><strong>{g["name"]}</strong><span>{html.escape(g["title"])}</span></a>' for g in GUIDES)
  hub = f"""<h1>Chess strategy training: the exercises</h1>
<p class="lead">Tactics puzzles always have one right answer. Real games don't. ChessStrategy.org trains what comes before the move: reading the position, choosing a plan, finding good moves, and picking the best one.</p>
<div class="cards">{cards}</div>
<p>Every exercise uses positions from master games, and from your own games once you connect Lichess or add your Chess.com username. Answers are checked with fixed counting rules and Stockfish, which runs in your browser. It's free, open source and has no ads.</p>
<p><a class="cta" href="../">Start training</a></p>
<h2 id="faq">Questions</h2>
""" + ''.join(f'<h3 class="faq-h">{html.escape(sec)}</h3>' + ''.join(f'<details><summary>{html.escape(q)}</summary><div class="a">{a}</div></details>' for q, a in qs) for sec, qs in FAQ)
  plain = lambda h: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()
  ld = [{ '@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Chess strategy training: the exercises', 'url': SITE + 'learn/',
          'hasPart': [{ '@type': 'Article', 'headline': g['title'], 'url': SITE + f'learn/{g["slug"]}/' } for g in GUIDES] },
        { '@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{ '@type': 'Question', 'name': q, 'acceptedAnswer': { '@type': 'Answer', 'text': plain(a) } } for _, qs in FAQ for q, a in qs] }]
  out['learn/index.html'] = page('learn/index.html', 'Chess strategy training: guides and FAQ',
    'Four free chess strategy exercises: imbalances, plans, candidate moves and move selection, on master games and your own Lichess and Chess.com games.', hub, ld)
  urls = ['', 'learn/'] + [f'learn/{g["slug"]}/' for g in GUIDES] + ['privacy.html', 'privacy-fr.html', 'terms.html', 'terms-fr.html']
  out['sitemap.xml'] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                        + ''.join(f'  <url><loc>{SITE}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
  return { root / k: v for k, v in out.items() }

if __name__ == '__main__':
  for f, t in build().items():
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(t, encoding='utf-8')
  print('guides built')
