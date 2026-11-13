# Builds the site's plain pages, in English and French: the guides (one page per exercise, and their index with the
# FAQ), privacy and terms (their text in scripts/pages/), all in one frame, and the sitemap. For search engines, and
# for anyone who wants to know what an exercise trains before trying it. Plain pages, no script.
# Run by scripts/build-site.py (so `build-site.py --check` covers them too); the text lives here.
# The pictures (learn/img/) are the app's own screens on master positions, as a new visitor gets them (-fr: in French).
import pathlib, json, html, re
root = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://chessstrategy.org/'
HUB = { 'en': 'learn/', 'fr': 'fr/guides/' }   # each language's guides

# ---------------------------------------------------------------- the guides
# Each: the exercise it opens (?play=), its picture, and per language its address (HUB + slug), name and text (HTML).
GUIDES = [
  dict(play='imbalances', img='imbalance-reading',
    en=dict(slug='chess-imbalances', name='Imbalance reading', sub='Learn to read a position',
      title='Chess imbalances: learn to read a position',
      desc='What chess imbalances are (material, pawns, space, activity, king safety, threats), how to weigh them, and a free exercise to practise reading them on master games and your own games.',
      lead="Every position is a set of differences between the two sides. Strong players spot the few that decide the game, and plan around them: an idea made famous by Jeremy Silman.",
      alt='Imbalance reading review on a 1929 World Championship position: Activity and Pawns to White right, Material given to Black while balanced, Space to Black missed',
      caption="Activity and Pawns to White: right. Material was given to Black, but it's balanced: Space was the one to pick.",
      body="""
<h2>The six imbalances</h2>
<ul>
  <li><strong>Material</strong>: pawn 1, knight and bishop 3, rook 5, queen 9; the bishop pair adds half a pawn.</li>
  <li><strong>Pawns</strong>: passed and connected pawns, more as they advance; isolated, doubled and backward pawns count against.</li>
  <li><strong>Space</strong>: pawns and the safe squares behind them in the centre.</li>
  <li><strong>Activity</strong>: the safe squares your pieces reach, outposts, open files. Early on, <strong>Development</strong> instead.</li>
  <li><strong>King safety</strong>: the pawn shelter against attacking pieces. Without queens, <strong>King activity</strong> instead.</li>
  <li><strong>Other threats</strong>: material you can win right now, and threats for the next move, like a pawn push that attacks a piece.</li>
</ul>
<p>Material, Pawns and Space are <em>static</em>: they tend to last. The others are <em>dynamic</em>: use them before they fade.</p>

<h2>The exercise</h2>
<p>Choose 3 of the imbalances that decide the position (there can be more than 3), and who has the edge. The review shows each one's size: <strong>=</strong> balanced; <strong>+</strong> or <strong>++</strong> a small or big edge for White, <strong>−</strong> or <strong>−−</strong> for Black. A choice among the 3 biggest edges, on the right side, scores full points; a smaller edge, half; a balanced one or the wrong side, nothing.</p>
<p>Find the ++ first. One big imbalance can outweigh several small ones, and tactics beat them all.</p>
"""),
    fr=dict(slug='desequilibres-aux-echecs', name='Lecture des déséquilibres', sub='Apprendre à lire une position',
      title='Les déséquilibres aux échecs : apprendre à lire une position',
      desc="Ce que sont les déséquilibres aux échecs (matériel, pions, espace, activité, sécurité du roi, menaces), comment les peser, et un exercice gratuit pour s'entraîner à les lire sur des parties de maîtres et vos propres parties.",
      lead="Chaque position est un ensemble de différences entre les deux camps. Les joueurs forts repèrent les quelques-unes qui décident de la partie, et bâtissent leur plan autour : une idée rendue célèbre par Jeremy Silman.",
      alt="Correction de Lecture des déséquilibres sur une position du championnat du monde 1929 : Activité et Pions aux Blancs, justes ; Matériel donné aux Noirs alors qu'il est équilibré ; Espace aux Noirs manqué",
      caption="Activité et Pions aux Blancs : juste. Le Matériel a été donné aux Noirs, mais il est équilibré : c'est l'Espace qu'il fallait choisir.",
      body="""
<h2>Les six déséquilibres</h2>
<ul>
  <li><strong>Matériel</strong> : pion 1, cavalier et fou 3, tour 5, dame 9 ; la paire de fous ajoute un demi-pion.</li>
  <li><strong>Pions</strong> : pions passés et liés, d'autant plus qu'ils sont avancés ; les pions isolés, doublés et arriérés comptent contre.</li>
  <li><strong>Espace</strong> : les pions et les cases sûres derrière eux au centre.</li>
  <li><strong>Activité</strong> : les cases sûres qu'atteignent vos pièces, les avant-postes, les colonnes ouvertes. En début de partie, le <strong>Développement</strong> à la place.</li>
  <li><strong>Sécurité du roi</strong> : l'abri de pions face aux pièces qui attaquent. Sans les dames, l'<strong>Activité du roi</strong> à la place.</li>
  <li><strong>Menaces</strong> : le matériel que vous pouvez gagner tout de suite, et les menaces pour le coup suivant, comme une poussée de pion qui attaque une pièce.</li>
</ul>
<p>Matériel, Pions et Espace sont <em>statiques</em> : ils ont tendance à durer. Les autres sont <em>dynamiques</em> : servez-vous-en avant qu'ils ne s'effacent.</p>

<h2>L'exercice</h2>
<p>Choisissez 3 des déséquilibres qui décident de la position (il peut y en avoir plus de 3), et qui a l'avantage. La correction montre la taille de chacun : <strong>=</strong> équilibré ; <strong>+</strong> ou <strong>++</strong> un petit ou un gros avantage pour les Blancs, <strong>−</strong> ou <strong>−−</strong> pour les Noirs. Un choix parmi les 3 plus gros avantages, du bon côté, rapporte tous les points ; un avantage plus petit, la moitié ; un déséquilibre équilibré ou du mauvais côté, rien.</p>
<p>Cherchez d'abord les ++. Un gros déséquilibre peut l'emporter sur plusieurs petits, et la tactique prime sur tout.</p>
""")),

  dict(play='planq', img='plan-finder',
    en=dict(slug='chess-plans', name='Plan finder', sub='How to find a general plan in chess',
      title='How to find a plan in chess',
      desc="How to make a plan in chess: check what's urgent, judge who is better, then decide whether to trade and whether to attack or improve. A free exercise on master positions and your own games.",
      lead="\"A bad plan is better than no plan at all\", as the old saying goes (often credited to Chigorin). A plan gives you a direction to search for good moves, and helps you take better decisions. Four questions, in order, can lead to one.",
      alt="Plan finder review on a 1963 World Championship position: Keep pieces right, Either instead of Open / Attack, 75%",
      caption="Black's king is stuck in the centre, with White's queen already on g6. That weak king decides the plan.",
      body="""
<h2>Four questions</h2>
<ol>
  <li><strong>Anything urgent?</strong> Checks, captures and threats, for both sides: something to win, or to defend, like a pawn or the exchange. (Positions where a piece or more is at stake are left out: there, the threat decides the move.)</li>
  <li><strong>Who's better?</strong> Weighing the imbalances is a good way to gauge it, and the most decisive ones should shape the core aspects of your plan. Balanced means the engine within half a pawn.</li>
  <li><strong>Trade, or keep pieces?</strong> Trades help the side up material, with better pawns, or short of space. Keep pieces with better pieces, more space, or against a weak king.</li>
  <li><strong>Attack, or improve?</strong> An edge that fades (active pieces, a development lead, a weak king) calls for opening up and attacking. One that lasts (material, pawns, space) leaves time to improve.</li>
</ol>

<h2>The exercise</h2>
<p>Answer the first two questions, check, then the last two. Each answer is a quarter of the score.</p>
<p>The plan follows the imbalances. When they pull both ways, either answer counts.</p>
"""),
    fr=dict(slug='trouver-un-plan-aux-echecs', name='Recherche du plan', sub='Comment trouver un plan général aux échecs',
      title='Comment trouver un plan aux échecs',
      desc="Comment faire un plan aux échecs : voir ce qui est urgent, juger qui est mieux, puis décider s'il faut échanger, attaquer ou améliorer. Un exercice gratuit sur des positions de maîtres et vos propres parties.",
      lead="« Un mauvais plan vaut mieux que pas de plan du tout », dit le vieil adage (souvent attribué à Tchigorine). Un plan vous donne une direction pour chercher de bons coups, et vous aide à prendre de meilleures décisions. Quatre questions, dans l'ordre, peuvent y mener.",
      alt="Correction de Recherche du plan sur une position du championnat du monde 1963 : Gardez les pièces juste, Au choix au lieu de Ouvrir / Attaquer, 75 %",
      caption="Le roi noir est resté au centre, et la dame blanche est déjà en g6. Ce roi faible décide du plan.",
      body="""
<h2>Quatre questions</h2>
<ol>
  <li><strong>Une urgence ?</strong> Échecs, prises et menaces, des deux côtés : quelque chose à gagner, ou à défendre, comme un pion ou la qualité. (Les positions où une pièce ou plus est en jeu sont écartées : là, c'est la menace qui décide du coup.)</li>
  <li><strong>Qui est mieux ?</strong> Peser les déséquilibres est un bon moyen d'en juger, et les plus décisifs devraient façonner les grandes lignes de votre plan. Équilibré veut dire le moteur à moins d'un demi-pion.</li>
  <li><strong>Échanger, ou garder les pièces ?</strong> Les échanges aident le camp qui a plus de matériel, de meilleurs pions, ou qui manque d'espace. Gardez les pièces avec de meilleures pièces, plus d'espace, ou face à un roi faible.</li>
  <li><strong>Attaquer, ou améliorer ?</strong> Un avantage qui s'efface (pièces actives, avance de développement, roi faible) appelle à ouvrir et attaquer. Un avantage qui dure (matériel, pions, espace) laisse le temps d'améliorer.</li>
</ol>

<h2>L'exercice</h2>
<p>Répondez aux deux premières questions, vérifiez, puis aux deux dernières. Chaque réponse compte pour un quart du score.</p>
<p>Le plan suit les déséquilibres. Quand ils tirent dans les deux sens, les deux réponses comptent.</p>
""")),

  dict(play='candidates', img='candidate-moves',
    en=dict(slug='candidate-moves', name='Candidate moves', sub='Find one or more good moves',
      title='Candidate moves in chess: find more than one good move',
      desc='What candidate moves are, how to find them (checks, captures, threats, then the plan), and a free exercise grading your picks with Stockfish on master games and your own games.',
      lead="Most mistakes come from playing the first move that looks good. Alexander Kotov's advice: list a few serious options first, then choose.",
      alt="Candidate moves review on a 2024 World Championship position: bxa3 and Qa5, the engine's top two, then h5, dubious; the engine's own 3rd move is dubious too",
      caption="Only two moves hold here, bxa3 and Qa5, and both were found. The third pick should have been skipped though.",
      body="""
<h2>How to find them</h2>
<ul>
  <li><strong>Forcing moves first</strong>: checks, captures and threats, for both sides.</li>
  <li><strong>Then moves that follow the <a href="../chess-plans/">plan</a></strong>: they make the most of your most decisive imbalances, or reduce your opponent's.</li>
  <li><strong>Keep the game phase in mind</strong>, especially when the plan is to improve: in the opening, develop and get your king safe; in the middlegame, find better squares for your pieces and fix your weaknesses; in the endgame, bring your king in and push your passed pawns.</li>
</ul>

<h2>The exercise</h2>
<p>Pick 1 to 3 strong moves. Stockfish grades each against its best move: Best, Good, Ok, Dubious, Mistake or Blunder. Dubious or worse scores zero: when unsure, pick fewer.</p>
"""),
    fr=dict(slug='coups-candidats', name='Coups candidats', sub='Trouver un ou plusieurs bons coups',
      title="Les coups candidats aux échecs : trouver plus d'un bon coup",
      desc="Ce que sont les coups candidats, comment les trouver (échecs, prises, menaces, puis le plan), et un exercice gratuit qui note vos choix avec Stockfish sur des parties de maîtres et vos propres parties.",
      lead="La plupart des erreurs viennent du premier coup qui a l'air bon. Le conseil d'Alexandre Kotov : dresser d'abord la liste de quelques options sérieuses, puis choisir.",
      alt="Correction de Coups candidats sur une position du championnat du monde 2024 : bxa3 et Qa5, les deux meilleurs coups du moteur, puis h5, douteux ; le 3e coup du moteur lui-même est douteux",
      caption="Seuls deux coups tiennent ici, bxa3 et Qa5, et les deux ont été trouvés. Le troisième choix aurait pourtant dû être évité.",
      body="""
<h2>Comment les trouver</h2>
<ul>
  <li><strong>Les coups forcés d'abord</strong> : échecs, prises et menaces, des deux côtés.</li>
  <li><strong>Puis les coups qui suivent le <a href="../trouver-un-plan-aux-echecs/">plan</a></strong> : ils tirent le meilleur de vos déséquilibres les plus décisifs, ou réduisent ceux de l'adversaire.</li>
  <li><strong>Gardez en tête la phase de la partie</strong>, surtout quand le plan est d'améliorer : dans l'ouverture, développez et mettez votre roi à l'abri ; en milieu de partie, trouvez de meilleures cases pour vos pièces et corrigez vos faiblesses ; en finale, activez votre roi et poussez vos pions passés.</li>
</ul>

<h2>L'exercice</h2>
<p>Choisissez 1 à 3 bons coups. Stockfish note chacun par rapport à son meilleur coup : Meilleur, Bon, Correct, Douteux, Erreur ou Gaffe. Douteux ou pire ne rapporte rien : dans le doute, choisissez-en moins.</p>
""")),

  dict(play='final', img='move-selection',
    en=dict(slug='move-selection', name='Move selection', sub='How to choose the best move',
      title='How to choose the best move in chess',
      desc='How to choose between good-looking moves in chess: find the best one, then check what each move allows. A free exercise ranking four moves from master games and your own mistakes.',
      lead="Several moves may look fine, but only one is best. Once exploring <a href=\"../candidate-moves/\">candidate moves</a> has given you a few serious options, the last step is choosing between them, and that's where many games are lost.",
      alt='Move selection review on a 1963 World Championship position: four moves ranked, the game move Nxe4 best, two dubious ones',
      caption='The game move Nxe4 is best and was found. Qh2, the only other good move, should have come 2nd.',
      body="""
<h2>Ranking your options</h2>
<ul>
  <li><strong>Check each move for a blunder</strong>: look at your opponent's checks, captures and threats after it. A move that drops material or exposes your king generally goes down, however menacing it looks.</li>
  <li><strong>Compare the positions you reach</strong>: prefer moves that make the most of your advantages, or reduce your opponent's, as your plan requires.</li>
  <li><strong>When two moves look equal</strong>, don't spend too long on them: if they really are close in strength, the choice won't change much.</li>
</ul>

<h2>The exercise</h2>
<p>Rank four moves, from best to worst. One was played in the game. In your own games, it's your move, and always a mistake: a second chance at a decision you got wrong.</p>
<p>Finding the best move is half the score: 1st place counts for 50%, 2nd for 30%, 3rd for 20%, each compared with the best move left.</p>
"""),
    fr=dict(slug='choisir-le-meilleur-coup', name='Choix du coup', sub='Comment choisir le meilleur coup',
      title='Comment choisir le meilleur coup aux échecs',
      desc="Comment choisir entre des coups qui ont l'air bons : trouver le meilleur, puis vérifier ce que chaque coup permet. Un exercice gratuit qui fait classer quatre coups, tirés de parties de maîtres et de vos propres erreurs.",
      lead="Plusieurs coups peuvent avoir l'air bien, mais un seul est le meilleur. Une fois que l'exploration des <a href=\"../coups-candidats/\">coups candidats</a> vous a donné quelques options sérieuses, reste à choisir entre elles, et c'est là que beaucoup de parties se perdent.",
      alt="Correction de Choix du coup sur une position du championnat du monde 1963 : quatre coups classés, le coup joué Nxe4 est le meilleur, deux coups douteux",
      caption="Le coup joué Nxe4 est le meilleur et a été trouvé. Qh2, le seul autre coup valable, aurait dû être 2e.",
      body="""
<h2>Classer vos options</h2>
<ul>
  <li><strong>Vérifiez que chaque coup n'est pas une gaffe</strong> : regardez les échecs, prises et menaces de l'adversaire après lui. Un coup qui perd du matériel ou expose votre roi descend généralement dans le classement, aussi menaçant qu'il paraisse.</li>
  <li><strong>Comparez les positions obtenues</strong> : préférez les coups qui tirent le meilleur de vos avantages, ou réduisent ceux de l'adversaire, comme le demande votre plan.</li>
  <li><strong>Quand deux coups se valent</strong>, n'y passez pas trop de temps : s'ils sont vraiment proches, le choix ne changera pas grand-chose.</li>
</ul>

<h2>L'exercice</h2>
<p>Classez quatre coups, du meilleur au pire. L'un d'eux a été joué dans la partie. Dans vos parties, c'est votre coup, et toujours une erreur : une deuxième chance sur une décision manquée.</p>
<p>Trouver le meilleur coup, c'est la moitié du score : la 1re place compte pour 50 %, la 2e pour 30 %, la 3e pour 20 %, chacune comparée au meilleur coup restant.</p>
""")),
]

# ---------------------------------------------------------------- the FAQ
# At the bottom of each language's guides index: what the guides don't already say. Answers are HTML; the
# structured data (FAQPage) gets them as plain text.
FAQ = {
'en': [
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
],
'fr': [
  ("À propos de l'application", [
    ("Qu'est-ce qu'elle entraîne ?", "La stratégie : que faire dans une position calme, quand il n'y a pas de tactique à trouver. Les applications de puzzles entraînent très bien la tactique, mais la plupart des parties se décident dans des positions où la question n'est pas « qu'est-ce qui gagne ? » mais « que se passe-t-il, et que dois-je viser ? »."),
    ("À qui s'adresse-t-elle ?", "Aux joueurs de club qui connaissent déjà leur tactique et se sentent perdus quand la position est calme : pas de plan, ou un plan qui ne colle pas à la position."),
    ("Comment enseigne-t-elle ?", "Par la pratique sur de vraies positions, avec une correction après chaque réponse. Chaque idée est rendue concrète : un déséquilibre est un compte de choses sur l'échiquier, dessiné quand vous le touchez, et chaque réponse est vérifiée par un moteur ou par une règle de calcul. Les exercices suivent l'ordre des questions que se posent les joueurs forts."),
    ("D'où viennent les idées ?", "Des livres classiques de stratégie (Steinitz, Nimzowitsch, Capablanca, Kotov, Silman, Dvoretsky, Aagaard, Shereshevsky) et de l'ancienne évaluation de Stockfish, qui compte les mêmes choses à sa façon."),
  ]),
  ("La démarche de réflexion", [
    ("Y a-t-il un ordre pour réfléchir à une position ?", "Oui. Les livres s'accordent sur un ordre, et chaque exercice en entraîne une étape :<ol><li><b>Une urgence ?</b> Échecs, prises et menaces, des deux côtés (Recherche du plan, phase 1).</li><li><b>Qu'est-ce qui diffère entre les deux camps ?</b> Les déséquilibres (Lecture des déséquilibres).</li><li><b>Qui est mieux ?</b> Les déséquilibres pesés ensemble décident de votre attitude : le camp qui a l'avantage joue pour s'en servir, l'autre se défend (Recherche du plan, phase 1).</li><li><b>Quel plan ?</b> Échanger ou garder les pièces ; ouvrir et attaquer, ou garder fermé et améliorer (Recherche du plan, phase 2).</li><li><b>Quels coups ?</b> Des coups candidats qui servent le plan, puis le choix, en vérifiant chacun contre la gaffe (Coups candidats, Choix du coup).</li></ol>"),
    ("Pourquoi des exercices séparés, et pas une position du début à la fin ?", "Chaque étape a sa correction tout de suite. Sur une seule position, la correction d'une étape trahirait la suivante, et une longue chaîne rend chaque tour lent. La routine quotidienne enchaîne les étapes dans l'ordre, chacune sur sa propre position."),
    ("Et le plan de l'adversaire ?", "Vérifier les échecs, prises et menaces de l'adversaire (étape 1) est la première partie de la prophylaxie. La question complète, « que veut mon adversaire ? », pourra devenir un exercice à part plus tard."),
  ]),
  ("Scores et progrès", [
    ("Qu'est-ce que ma moyenne ?", "Votre précision dans un exercice, lissée sur les positions récentes : d'abord une simple moyenne, puis chaque nouvelle position la déplace de 15 % vers son score. Une mauvaise position coûte peu ; une série de bonnes la fait monter régulièrement."),
    ("Qu'est-ce que la routine quotidienne ?", "Trois positions de chaque exercice dans la journée, en autant de fois que vous voulez, dans l'ordre de la réflexion."),
    ("Que sont les positions manquées ?", "Les positions où vous avez fait moins que votre moyenne du moment. Revoir les rejoue ; faire au moins votre moyenne en retire une de la liste. Une position jouée aujourd'hui attend demain."),
    ("Où sont gardés mes progrès ?", "Dans votre navigateur, et dans votre compte quand vous êtes connecté, pour qu'ils vous suivent sur tous vos appareils."),
  ]),
  ("Les positions et le moteur", [
    ("D'où viennent les positions ?", "Des parties de championnat du monde et, une fois connecté, de vos propres parties Lichess et Chess.com. Dans vos parties, l'application cherche vos erreurs : la position juste avant un coup qui a beaucoup perdu."),
    ("Comment les positions sont-elles choisies ?", "Par des règles, vérifiées avec Stockfish : des positions calmes où la stratégie compte, réparties sur la partie, pas trop proches les unes des autres, et pour chaque exercice une raison de poser la question. Les parties nulles ne donnent que leurs positions déséquilibrées."),
    ("Quel moteur ?", "Stockfish 19 (sa version « lite »), qui tourne dans votre navigateur, si bien que rien n'est envoyé nulle part : chaque position est analysée à la profondeur 20, en quelques secondes au plus. Les positions de maîtres viennent aussi avec leur évaluation calculée à l'avance."),
  ]),
  ("Crédits et lectures", [
    ("D'où viennent les sons ?", "Les sons de coup et de prise sont deux sons découpés dans <a href=\"https://freesound.org/s/792572/\">« chess piece » par imrius</a> (freesound.org), sous licence <a href=\"https://creativecommons.org/licenses/by/4.0/\">CC BY 4.0</a>. Modifications : découpe, bruit de fond réduit, volume égalisé."),
    ("Quels livres sont derrière l'application ?", "<ul><li><b>Jeremy Silman, <i>How to Reassess Your Chess</i> :</b> les déséquilibres, et comment ils mènent à un plan.</li><li><b>Aron Nimzowitsch, <i>Mon système</i> :</b> colonnes ouvertes, avant-postes, chaînes de pions, blocus, prophylaxie.</li><li><b>José Raúl Capablanca, <i>Principes fondamentaux des échecs</i> :</b> les bases de chaque phase.</li><li><b>Alexandre Kotov, <i>Pensez comme un grand maître</i> :</b> les coups candidats et l'ordre de la réflexion.</li><li><b>Mark Dvoretsky et Artur Youssoupov, <i>Positional Play</i> :</b> la pensée prophylactique.</li><li><b>Jacob Aagaard, <i>Grandmaster Preparation: Positional Play</i> :</b> trois questions pour toute position calme.</li><li><b>Mikhaïl Chérechevski, <i>Endgame Strategy</i> :</b> le roi, les deux faiblesses, et ne pas se presser.</li></ul>"),
  ]),
],
}

# ---------------------------------------------------------------- the words around the text
W = {
  'en': dict(other='Lire en français', faq='Frequently asked questions', exercises='Exercises',
    intro="Tactics puzzles always have one right answer. Real games don't. ChessStrategy.org trains what comes before the move: reading the position, choosing a plan, finding good moves, and picking the best one.",
    faq_desc='How ChessStrategy.org works: its four chess strategy exercises (imbalances, plans, candidate moves, move selection), scores, positions and the engine.'),
  'fr': dict(other='Read in English', faq='Questions fréquentes', exercises='Exercices',
    intro="Les puzzles de tactique ont toujours une seule bonne réponse. Les vraies parties, non. ChessStrategy.org entraîne ce qui vient avant le coup : lire la position, choisir un plan, trouver de bons coups, et choisir le meilleur.",
    faq_desc="Comment fonctionne ChessStrategy.org : ses quatre exercices de stratégie aux échecs (déséquilibres, plans, coups candidats, choix du coup), les scores, les positions et le moteur."),
}

def nbsp(t):
  # French typography: a non-breaking space before : ; ? ! and inside « », outside tags
  parts = re.split(r'(<[^>]+>)', t)
  for i, p in enumerate(parts):
    if not p.startswith('<'):
      p = re.sub(r' ([:;?!»])', '\u00a0\\1', p); p = p.replace('« ', '«\u00a0'); p = re.sub(r'(\d) %', '\\1\u00a0%', p)
      parts[i] = p
  return ''.join(parts)

STYLE = """
  :root{ color-scheme: dark; --bg:#12161B; --panel:#1B2129; --border:#2E3742; --line:#2A313A; --text:#EDE7DC; --mute:#9A9488; --accent:#C9A227; }
  *{ box-sizing:border-box; }
  body{ background:var(--bg); color:var(--text); margin:0; font:16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
  header, main{ max-width:760px; margin:0 auto; padding:0 16px; }
  header{ display:flex; align-items:center; justify-content:space-between; padding-top:16px; padding-bottom:8px; }
  .brand{ display:flex; align-items:center; gap:10px; font-weight:600; color:var(--text); text-decoration:none; } .brand img{ width:28px; height:28px; border-radius:7px; }
  /* the language, as the app's Settings show it: the current one in a chip, a tap for the other */
  .lang{ display:inline-flex; align-items:center; background:var(--panel); border:1px solid var(--border); color:var(--text); border-radius:999px; padding:6px 14px; font-size:.86rem; font-weight:600; text-decoration:none; white-space:nowrap; }
  main{ padding-bottom:56px; }
  h1{ font-size:1.9rem; line-height:1.2; margin:20px 0 10px; font-family:Georgia, "Times New Roman", serif; }
  .back{ margin:12px 0 0; font-size:.95rem; } .back a{ color:var(--mute); text-decoration:none; } h1 + .sub{ margin:-4px 0 14px; color:var(--mute); font-size:1.08rem; }
  h2{ font-size:1.25rem; margin:32px 0 8px; } h3{ font-size:1.05rem; margin:20px 0 4px; }
  .lead{ font-size:1.08rem; } p, li{ color:var(--text); } .mute{ color:var(--mute); } a{ color:var(--accent); }
  ul, ol{ padding-left:22px; } li{ margin:4px 0; }
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
"""

# Every page the same frame: the logo (back to the app) and the language chip (the same page in the other language).
def page(path, lang, title, desc, body, alt, ld=None, kind='article'):
  up = '../' * path.count('/')
  url = lambda p: SITE + p.removesuffix('index.html')
  other = 'fr' if lang=='en' else 'en'
  chip = f'<a class="lang" href="{up}{alt.removesuffix("index.html")}" hreflang="{other}" lang="{other}" aria-label="{W[lang]["other"]}" title="{W[lang]["other"]}">{lang.upper()}</a>'
  return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · ChessStrategy.org</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url(path)}">
<link rel="alternate" hreflang="{lang}" href="{url(path)}">
<link rel="alternate" hreflang="{other}" href="{url(alt)}">
<meta property="og:type" content="{kind}">
<meta property="og:site_name" content="ChessStrategy.org">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url(path)}">
<meta property="og:image" content="{SITE}icons/og-image.png">
<meta property="og:locale" content="{'fr_FR' if lang=='fr' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#12161B">
<link rel="icon" type="image/svg+xml" href="{up}icons/icon.svg">
{f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ''}
<style>{STYLE}</style>
<!-- Built by scripts/build-pages.py: edit the script (or scripts/pages/), not this file. -->
</head>
<body>
<header><a class="brand" href="{up}"><img src="{up}icons/icon.svg" alt="">ChessStrategy.org</a>{chip}</header>
<main>
{body}
</main>
</body>
</html>
"""

# Privacy and terms: their text in scripts/pages/, this frame around it.
LEGAL = [
  ('privacy.html', 'en', 'Privacy', 'What ChessStrategy.org keeps about you, where, and how to delete it.', 'privacy-fr.html'),
  ('privacy-fr.html', 'fr', 'Confidentialité', 'Ce que ChessStrategy.org conserve à votre sujet, où, et comment le supprimer.', 'privacy.html'),
  ('terms.html', 'en', 'Terms of use', 'The terms of use of ChessStrategy.org, free and open-source chess strategy training.', 'terms-fr.html'),
  ('terms-fr.html', 'fr', "Conditions d'utilisation", "Les conditions d'utilisation de ChessStrategy.org, entraînement à la stratégie aux échecs, gratuit et libre.", 'terms.html'),
]

def crumbs(*items):
  return { '@type': 'BreadcrumbList', 'itemListElement': [{ '@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u } for i, (n, u) in enumerate(items)] }

def build():
  out, urls = {}, ['']
  for lang in ('en', 'fr'):
    w, fix = W[lang], (nbsp if lang=='fr' else (lambda t: t))
    other = 'fr' if lang=='en' else 'en'
    for g in GUIDES:
      t = g[lang]; path = f'{HUB[lang]}{t["slug"]}/index.html'; alt = f'{HUB[other]}{g[other]["slug"]}/index.html'
      img = f'{g["img"]}{"-fr" if lang=="fr" else ""}.webp'
      # heading as on the FAQ's card (name, subtitle); the search-friendly title stays in <title>
      body = fix(f"""<p class="back"><a href="../">‹ FAQ</a></p>
<h1>{html.escape(t['name'])}</h1>
<p class="sub">{html.escape(t.get('sub', t['title']))}</p>
<p class="lead">{t['lead']}</p>
<figure><img src="{'../' * path.count('/')}learn/img/{img}" width="390" height="844" alt="{html.escape(t['alt'])}" loading="lazy"><figcaption>{t['caption']}</figcaption></figure>
{t['body'].strip()}""")
      ld = [{ '@context': 'https://schema.org', '@type': 'Article', 'headline': t['title'], 'description': t['desc'], 'inLanguage': lang,
              'image': SITE + f'learn/img/{img}', 'url': SITE + path.removesuffix('index.html'),
              'publisher': { '@type': 'Organization', 'name': 'ChessStrategy.org', 'url': SITE } },
            { '@context': 'https://schema.org', **crumbs((W[lang]['faq'], HUB[lang]), (t['name'], path.removesuffix('index.html'))) }]
      out[path] = page(path, lang, t['title'], t['desc'], body, alt, ld)
      urls.append(path.removesuffix('index.html'))
    # the index: the guides, then the FAQ
    path = HUB[lang] + 'index.html'
    cards = ''.join(f'<a class="card" href="{g[lang]["slug"]}/"><strong>{g[lang]["name"]}</strong><span>{html.escape(g[lang].get("sub", g[lang]["title"]))}</span></a>' for g in GUIDES)
    faq = ''.join(f'<h2 class="faq-h">{html.escape(sec)}</h2>' + ''.join(f'<details><summary>{html.escape(q)}</summary><div class="a">{a}</div></details>' for q, a in qs) for sec, qs in FAQ[lang])
    hub = fix(f"""<h1>{w['faq']}</h1>
<p class="mute">{w['intro']}</p>
<h2 class="faq-h">{w['exercises']}</h2>
<div class="cards">{cards}</div>
{faq}""")
    plain = lambda h: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fix(h)))).strip()
    ld = [{ '@context': 'https://schema.org', '@type': 'CollectionPage', 'name': w['faq'], 'url': SITE + HUB[lang], 'inLanguage': lang,
            'hasPart': [{ '@type': 'Article', 'headline': g[lang]['title'], 'url': SITE + HUB[lang] + g[lang]['slug'] + '/' } for g in GUIDES] },
          { '@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': lang,
            'mainEntity': [{ '@type': 'Question', 'name': plain(q), 'acceptedAnswer': { '@type': 'Answer', 'text': plain(a) } } for _, qs in FAQ[lang] for q, a in qs] }]
    out[path] = page(path, lang, w['faq'], w['faq_desc'], hub, HUB[other] + 'index.html', ld, kind='website')
    urls.append(HUB[lang])
  for f, lang, title, desc, alt in LEGAL:
    out[f] = page(f, lang, title, desc, (root / 'scripts' / 'pages' / f).read_text(encoding='utf-8').strip(), alt, kind='website')
    urls.append(f)
  out['sitemap.xml'] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                        + ''.join(f'  <url><loc>{SITE}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
  return { root / k: v for k, v in out.items() }

if __name__ == '__main__':
  for f, t in build().items():
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(t, encoding='utf-8')
  print('pages built')
