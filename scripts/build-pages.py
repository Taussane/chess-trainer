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
    en=dict(slug='chess-imbalances', name='Imbalance reading',
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
<p>Then the review shows every imbalance with its size: <strong>=</strong> balanced, <strong>+</strong> a small edge, <strong>++</strong> a big one, in white for White and in black for Black. You don't guess sizes, but the ++ ones are the edges to find first. Each imbalance has its own thresholds: across the master positions, about half are =, a third + and one in six ++.</p>
<p>Each of your choices counts for a third of the score: one of the three biggest edges on the right side gets full points, a smaller edge on the right side gets half, a balanced one or the wrong side gets nothing. Tap any imbalance to see on the board how it was counted.</p>

<h2>Tips</h2>
<ul>
  <li>Look for the big edges first, then the clearest small ones.</li>
  <li>Don't choose an imbalance that's balanced: it scores nothing.</li>
  <li>Grades don't simply add up. One big imbalance can outweigh several small ones, and tactics beat them all.</li>
</ul>

<h2>Why it helps</h2>
<p>Reading imbalances is the step before every plan. It tells you whether to trade pieces, where to attack, which pawn to target, and when to hurry. Done on hundreds of positions, it becomes a habit you bring to your own games. The <a href="../chess-plans/">Plan finder</a> takes the next step: from the imbalances to a plan.</p>
"""),
    fr=dict(slug='desequilibres-aux-echecs', name='Lecture des déséquilibres',
      title='Les déséquilibres aux échecs : apprendre à lire une position',
      desc="Ce que sont les déséquilibres aux échecs (matériel, pions, espace, activité, sécurité du roi, menaces), comment les peser, et un exercice gratuit pour s'entraîner à les lire sur des parties de maîtres et vos propres parties.",
      lead="Chaque position est un ensemble de différences entre les deux camps : un pion de plus, une case faible, un roi plus sûr. Les joueurs forts ne les pèsent pas toutes. Ils repèrent les quelques-unes qui décident de la partie, et bâtissent leur plan autour.",
      alt='Correction de Lecture des déséquilibres sur une position du championnat du monde 1978 : Activité et Espace aux Blancs, Sécurité du roi aux Noirs, trois bonnes réponses',
      caption='Kortschnoj – Karpov, championnat du monde 1978, aux Noirs de jouer. Trois réponses, toutes justes : les Blancs ont les pièces les plus actives et plus d\'espace, les Noirs le roi le plus sûr.',
      body="""
<h2>Qu'est-ce qu'un déséquilibre ?</h2>
<p>Un déséquilibre est une différence, durable ou passagère, entre la position des Blancs et celle des Noirs. Jeremy Silman a rendu l'idée célèbre : au lieu de chercher un coup tout de suite, faites d'abord la liste de ce qui diffère, puis choisissez le plan qui tire le meilleur parti de vos avantages.</p>
<p>L'exercice en utilise six, chacun compté sur l'échiquier toujours de la même façon :</p>
<ul>
  <li><strong>Matériel</strong> : pion 1, cavalier 3, fou 3, tour 5, dame 9 ; la paire de fous ajoute un demi-pion.</li>
  <li><strong>Pions</strong> : les pions passés et liés comptent d'autant plus qu'ils sont avancés ; les pions isolés, doublés et arriérés comptent contre.</li>
  <li><strong>Espace</strong> : les pions et les cases sûres derrière eux au centre de l'échiquier (plus compté une fois qu'il reste peu de pièces).</li>
  <li><strong>Activité</strong> : les cases sûres qu'atteignent vos cavaliers, fous, tours et dame, plus les avant-postes et les colonnes ouvertes. En début de partie, le <strong>Développement</strong> prend sa place.</li>
  <li><strong>Sécurité du roi</strong> : les pions qui abritent le roi face aux pièces adverses qui le visent. Une fois les dames échangées, l'<strong>Activité du roi</strong> prend sa place : en finale, le roi devient une pièce de combat.</li>
  <li><strong>Menaces</strong> : le matériel que vous pouvez gagner tout de suite.</li>
</ul>
<p>Matériel, Pions et Espace sont <em>statiques</em> : ils durent. Activité, Sécurité du roi et Menaces sont <em>dynamiques</em> : ils peuvent disparaître en quelques coups, et appellent donc à agir.</p>

<h2>Comment se déroule l'exercice</h2>
<p>Vous recevez une position tirée d'une partie de maître, ou d'une de vos parties. Choisissez les <strong>3 déséquilibres qui la décident</strong>, et pour chacun dites qui a l'avantage, les Blancs ou les Noirs.</p>
<p>La correction montre ensuite chaque déséquilibre avec sa taille : <strong>=</strong> équilibré, <strong>+</strong> un petit avantage, <strong>++</strong> un gros, en blanc pour les Blancs et en noir pour les Noirs. Vous n'avez pas à deviner les tailles, mais les ++ sont les avantages à trouver en premier. Chaque déséquilibre a ses propres seuils : sur les positions de maîtres, environ la moitié sont =, un tiers + et un sur six ++.</p>
<p>Chacun de vos choix compte pour un tiers du score : l'un des trois plus gros avantages, du bon côté, rapporte tous les points ; un avantage plus petit du bon côté, la moitié ; un déséquilibre équilibré ou du mauvais côté, rien. Touchez un déséquilibre pour voir sur l'échiquier comment il a été compté.</p>

<h2>Conseils</h2>
<ul>
  <li>Cherchez d'abord les gros avantages, puis les petits les plus nets.</li>
  <li>Ne choisissez pas un déséquilibre équilibré : il ne rapporte rien.</li>
  <li>Les notes ne s'additionnent pas simplement. Un gros déséquilibre peut l'emporter sur plusieurs petits, et la tactique prime sur tout.</li>
</ul>

<h2>Pourquoi ça aide</h2>
<p>Lire les déséquilibres est l'étape qui précède tout plan. Elle vous dit s'il faut échanger des pièces, où attaquer, quel pion viser, et quand se presser. Pratiquée sur des centaines de positions, elle devient un réflexe que vous emportez dans vos parties. La <a href="../trouver-un-plan-aux-echecs/">Recherche du plan</a> fait le pas suivant : des déséquilibres au plan.</p>
""")),

  dict(play='planq', img='plan-finder',
    en=dict(slug='chess-plans', name='Plan finder',
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
<p>You answer the first two questions, check, then the last two. Each answer counts for a quarter of the score. The review gives the main reason under each answer; tap it to see it on the board.</p>

<h2>Where the answers come from</h2>
<p>The same rules every time, not someone's opinion:</p>
<ul>
  <li><strong>Urgent</strong>: two checks must agree. The count of threats says what each side could win; Stockfish then plays the position for each side, to see what it would really win. Positions where they disagree are left out, so every answer can be shown on the board. A pawn that looks free but that Stockfish doesn't take is poisoned, or there's better: the answer is "quiet".</li>
  <li><strong>The plan</strong>: each imbalance (see <a href="../chess-imbalances/">Imbalance reading</a>) votes for the side to play, + counting 1 and ++ counting 2. An answer goes to a side when its votes add up to 2 or more; otherwise it's "either". One vote short gives half the points.</li>
</ul>
<p>Are they always right? They're the books' principles applied to the position, not a calculated line: a plan is a direction, not the next move. Checked on master games, they hold when the imbalances agree. When nothing argued against a trade, masters tried to trade 56 to 67% of the time, against about 45% on average. And Stockfish finds forcing play good twice as often where the plan says "attack" as where it says "improve". When imbalances pull both ways, concrete reasons decide, and the answer is less certain.</p>

<h2>Tips</h2>
<ul>
  <li>Look at every check, capture and threat, yours and theirs, before judging anything else.</li>
  <li>A pawn that looks free may be poisoned: look at what follows.</li>
  <li>When unsure between attacking and improving, ask whether your edge will still be there in ten moves.</li>
</ul>
"""),
    fr=dict(slug='trouver-un-plan-aux-echecs', name='Recherche du plan',
      title='Comment trouver un plan aux échecs',
      desc="Comment faire un plan aux échecs : voir ce qui est urgent, juger qui est mieux, puis décider s'il faut échanger, attaquer ou améliorer. Un exercice gratuit sur des positions de maîtres et vos propres parties.",
      lead="« Qu'est-ce que je fais maintenant ? » : c'est la question derrière la plupart des mauvais coups. Un plan n'a pas besoin d'être long. Il naît de quelques décisions claires, prises dans le bon ordre.",
      alt='Recherche du plan, première question sur une position du championnat du monde 1978 : une urgence pour les Blancs, et qui est mieux',
      caption='Karpov – Kortschnoj, championnat du monde 1978, aux Blancs de jouer. Première question : y a-t-il une urgence, et qui est mieux ?',
      body="""
<h2>Quatre décisions, dans l'ordre</h2>
<p>La Recherche du plan découpe la planification en quatre questions, en deux étapes, comme un joueur fort réfléchit à une position.</p>
<h3>1. Une urgence ?</h3>
<p>Avant tout plan, ce qui ne peut pas attendre : les échecs, les prises et les menaces, des deux côtés. La position est <strong>calme</strong> (rien à gagner ni à parer tout de suite), ou le camp au trait <strong>peut gagner</strong> quelque chose, ou <strong>doit défendre</strong>. Quand une pièce ou plus est en jeu, c'est elle qui décide du coup, et le plan vient après.</p>
<h3>2. Qui est mieux ?</h3>
<p>Jugez la position dans son ensemble : <strong>équilibrée</strong> (le moteur à moins d'un demi-pion), ou un camp <strong>mieux</strong>. Commencez par le matériel, puis ce qui dure (pions, espace), puis ce qui peut changer vite (pièces, rois).</p>
<h3>3. Échanger, ou garder les pièces ?</h3>
<p>Les échanges aident le camp qui a plus de matériel, de meilleurs pions, qui est à l'étroit, ou dont les pièces sont moins bonnes. L'autre camp veut garder les pièces : moins de matériel, plus d'espace, de meilleures pièces, ou un roi adverse faible. Parfois les raisons s'annulent, et les deux se valent.</p>
<h3>4. Attaquer, ou améliorer ?</h3>
<p>Un avantage qui s'efface (de meilleures pièces, une avance de développement, un roi adverse faible) doit servir maintenant : ouvrez la position et attaquez. Un avantage qui dure (matériel, pions, espace) vous laisse le temps : gardez la position fermée et améliorez d'abord vos pièces.</p>

<h2>Comment se déroule l'exercice</h2>
<p>Vous répondez aux deux premières questions, vérifiez, puis aux deux dernières. Chaque réponse compte pour un quart du score. La correction donne la raison principale sous chaque réponse ; touchez-la pour la voir sur l'échiquier.</p>

<h2>D'où viennent les réponses</h2>
<p>Les mêmes règles à chaque fois, pas l'avis de quelqu'un :</p>
<ul>
  <li><strong>L'urgence</strong> : deux vérifications doivent concorder. Le compte des menaces dit ce que chaque camp pourrait gagner ; Stockfish joue ensuite la position pour chaque camp, pour voir ce qu'il gagnerait vraiment. Les positions où elles divergent sont écartées, pour que chaque réponse puisse se montrer sur l'échiquier. Un pion qui semble gratuit mais que Stockfish ne prend pas est empoisonné, ou il y a mieux : la réponse est « calme ».</li>
  <li><strong>Le plan</strong> : chaque déséquilibre (voir la <a href="../desequilibres-aux-echecs/">Lecture des déséquilibres</a>) vote pour le camp au trait, + comptant 1 et ++ comptant 2. Une réponse va à un camp quand ses votes atteignent 2 ou plus ; sinon c'est « au choix ». Une voix de moins rapporte la moitié des points.</li>
</ul>
<p>Ont-elles toujours raison ? Ce sont les principes des livres appliqués à la position, pas une variante calculée : un plan est une direction, pas le prochain coup. Vérifiées sur des parties de maîtres, elles tiennent quand les déséquilibres vont dans le même sens. Quand rien ne s'opposait à un échange, les maîtres ont cherché à échanger 56 à 67 % du temps, contre environ 45 % en moyenne. Et Stockfish trouve le jeu forcé bon deux fois plus souvent là où le plan dit « attaquer » que là où il dit « améliorer ». Quand les déséquilibres tirent dans les deux sens, ce sont des raisons concrètes qui décident, et la réponse est moins sûre.</p>

<h2>Conseils</h2>
<ul>
  <li>Regardez chaque échec, prise et menace, les vôtres et celles de l'adversaire, avant de juger quoi que ce soit d'autre.</li>
  <li>Un pion qui semble gratuit peut être empoisonné : regardez la suite.</li>
  <li>Entre attaquer et améliorer, demandez-vous si votre avantage sera encore là dans dix coups.</li>
</ul>
""")),

  dict(play='candidates', img='candidate-moves',
    en=dict(slug='candidate-moves', name='Candidate moves',
      title='Candidate moves in chess: find more than one good move',
      desc='What candidate moves are, how to find them (checks, captures, threats, then the plan), and a free exercise grading your picks with Stockfish on master games and your own games.',
      lead="Most mistakes come from playing the first move that looks good. Candidate moves are the habit of finding a few serious options first, then choosing between them.",
      alt="Candidate moves review on a 1954 World Championship position: three picks, graded Best, Good and Good, beside the engine's top 3",
      caption="Smyslov – Botvinnik, World Championship match 1954, Black to play. Three picks, graded against the engine's best: Rxg5 (Best), Nf4 and Nc7 (Good).",
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
    fr=dict(slug='coups-candidats', name='Coups candidats',
      title='Les coups candidats aux échecs : trouver plus d\'un bon coup',
      desc="Ce que sont les coups candidats, comment les trouver (échecs, prises, menaces, puis le plan), et un exercice gratuit qui note vos choix avec Stockfish sur des parties de maîtres et vos propres parties.",
      lead="La plupart des erreurs viennent du premier coup qui a l'air bon. Les coups candidats, c'est l'habitude de trouver d'abord quelques options sérieuses, puis de choisir entre elles.",
      alt='Correction de Coups candidats sur une position du championnat du monde 1987 : trois choix, notés Meilleur, Correct et Correct, à côté des 3 meilleurs coups du moteur',
      caption='Karpov – Kasparov, championnat du monde 1987, aux Blancs de jouer. Trois choix, comparés au meilleur coup du moteur : Rf2 (Meilleur), Qf2 et Kf1 (Correct).',
      body="""
<h2>Qu'est-ce qu'un coup candidat ?</h2>
<p>Un coup candidat est un coup qui mérite un vrai examen. L'idée, rendue célèbre par Alexandre Kotov, est d'en dresser la liste avant d'en calculer aucun, pour ne pas passer tout son temps sur la première idée et en manquer une meilleure. Dans la plupart des positions, plusieurs coups se valent à peu près : savoir les trouver, c'est tout l'art.</p>

<h2>Comment les trouver</h2>
<ul>
  <li><strong>Les coups forcés d'abord</strong> : échecs, prises et menaces, des deux côtés. Même quand vous ne les jouez pas, ils vous disent ce que veut l'adversaire.</li>
  <li><strong>Puis les coups qui suivent le plan</strong>. Dans l'ouverture : développer et roquer. En milieu de partie : jouer sur les déséquilibres (voir la <a href="../desequilibres-aux-echecs/">Lecture des déséquilibres</a>). En finale : activer le roi, pousser les pions passés.</li>
  <li><strong>Vérifiez ce que chaque coup permet</strong> avant de le garder.</li>
</ul>

<h2>Comment se déroule l'exercice</h2>
<p>Choisissez 1 à 3 bons coups pour le camp au trait, en les jouant sur l'échiquier. Stockfish note ensuite chacun par rapport à son meilleur coup : <strong>Meilleur</strong>, <strong>Bon</strong>, <strong>Correct</strong>, <strong>Douteux</strong>, <strong>Erreur</strong> ou <strong>Gaffe</strong>, selon les chances de gain que le coup abandonne. Douteux ou pire ne rapporte rien : mieux vaut moins de coups, mais meilleurs. La correction montre les 3 meilleurs coups du moteur à côté des vôtres.</p>

<h2>Conseils</h2>
<ul>
  <li>Un doute sur un coup ? Laissez-le de côté. Deux bons coups valent mieux que deux bons et un mauvais.</li>
  <li>Comptez les coups forcés même quand la position semble calme : c'est là que sont les surprises.</li>
  <li>Quand vous avez trouvé un bon coup, cherchez-en un deuxième. C'est l'habitude que l'exercice entraîne.</li>
</ul>
<p>Étape suivante : le <a href="../choisir-le-meilleur-coup/">Choix du coup</a>, choisir le meilleur parmi plusieurs.</p>
""")),

  dict(play='final', img='move-selection',
    en=dict(slug='move-selection', name='Move selection',
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
    fr=dict(slug='choisir-le-meilleur-coup', name='Choix du coup',
      title='Comment choisir le meilleur coup aux échecs',
      desc="Comment choisir entre des coups qui ont l'air bons : trouver le meilleur, puis vérifier ce que chaque coup permet. Un exercice gratuit qui fait classer quatre coups, tirés de parties de maîtres et de vos propres erreurs.",
      lead="Trouver de bons coups, c'est la moitié du travail. L'autre moitié, c'est choisir : plusieurs coups ont l'air bien, un seul est le meilleur. Le Choix du coup entraîne cette dernière décision.",
      alt='Correction de Choix du coup sur une position du championnat du monde 2023 : quatre coups classés, le coup joué Bg3 est le meilleur',
      caption='Nepomniachtchi – Ding Liren, championnat du monde 2023, aux Blancs de jouer. Quatre coups à classer : le coup joué, Bg3, est le meilleur ; Bxd5+ est douteux, Bc2 une erreur et Rxc4 une gaffe.',
      body="""
<h2>Comment se déroule l'exercice</h2>
<p>Vous recevez quatre coups pour le camp au trait : <strong>classez-les, le meilleur d'abord</strong>. L'un d'eux a été joué dans la partie. Dans les parties de maîtres, le coup du maître est souvent le meilleur, mais pas toujours. Dans vos parties, c'est votre coup, et c'est toujours une erreur : l'exercice vous donne une deuxième chance sur une décision que vous avez manquée.</p>
<p>Le score récompense surtout le haut du classement : la 1re place compte pour 50 %, la 2e pour 30 %, la 3e pour 20 %. Chaque place est comparée au meilleur coup restant, si bien qu'un bon deuxième choix rapporte même si le premier était faux. La correction montre la note et l'évaluation de Stockfish pour chaque coup.</p>

<h2>Comment choisir</h2>
<ul>
  <li><strong>Trouvez d'abord le meilleur coup</strong> : c'est la moitié du score, et dans une partie, c'est tout ce qui compte.</li>
  <li><strong>Vérifiez ce que chaque coup permet</strong> : un coup qui perd du matériel ou expose le roi passe en dernier, aussi actif qu'il paraisse.</li>
  <li><strong>Comparez avec le plan</strong> : avec les déséquilibres en tête (voir la <a href="../desequilibres-aux-echecs/">Lecture des déséquilibres</a>), le coup qui sert votre avantage bat en général celui qui s'agite.</li>
</ul>

<h2>Vos propres parties</h2>
<p>Connectez Lichess, ou ajoutez votre nom d'utilisateur Chess.com, et l'application parcourt vos parties récentes, trouve les moments où vous vous êtes trompé, et en fait des exercices. Vous retrouvez vos vraies décisions, avec les meilleurs coups à côté des vôtres.</p>
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
  'en': dict(lang='English', other='Lire en français', hub_title='Chess strategy training: the exercises',
    hub_page='Chess strategy training: guides and FAQ',
    hub_desc='Four free chess strategy exercises: imbalances, plans, candidate moves and move selection, on master games and your own Lichess and Chess.com games.',
    hub_lead="Tactics puzzles always have one right answer. Real games don't. ChessStrategy.org trains what comes before the move: reading the position, choosing a plan, finding good moves, and picking the best one.",
    hub_more="Every exercise uses positions from master games, and from your own games once you connect Lichess or add your Chess.com username. Answers are checked with fixed counting rules and Stockfish, which runs in your browser. It's free, open source and has no ads.",
    start='Start training', questions='Questions', try_top='Try {name}, free', try_h='Try it', play='Play {name}',
    try_p="{name} is one of four exercises on ChessStrategy.org, free and without ads. Positions come from master games, such as World Championship matches, and from your own Lichess and Chess.com games. Answers are checked with fixed counting rules and Stockfish, which runs in your browser."),
  'fr': dict(lang='Français', other='Read in English', hub_title="S'entraîner à la stratégie aux échecs : les exercices",
    hub_page='Entraînement à la stratégie aux échecs : guides et FAQ',
    hub_desc="Quatre exercices gratuits de stratégie aux échecs : déséquilibres, plans, coups candidats et choix du coup, sur des parties de maîtres et vos propres parties Lichess et Chess.com.",
    hub_lead="Les puzzles de tactique ont toujours une seule bonne réponse. Les vraies parties, non. ChessStrategy.org entraîne ce qui vient avant le coup : lire la position, choisir un plan, trouver de bons coups, et choisir le meilleur.",
    hub_more="Chaque exercice utilise des positions de parties de maîtres, et de vos propres parties une fois Lichess connecté ou votre nom d'utilisateur Chess.com ajouté. Les réponses sont vérifiées par des règles de calcul fixes et par Stockfish, qui tourne dans votre navigateur. C'est gratuit, libre et sans publicité.",
    start="Commencer l'entraînement", questions='Questions', try_top='Essayer {name}, gratuit', try_h="L'essayer", play='Jouer à {name}',
    try_p="{name} est l'un des quatre exercices de ChessStrategy.org, gratuit et sans publicité. Les positions viennent de parties de maîtres, comme les matchs de championnat du monde, et de vos propres parties Lichess et Chess.com. Les réponses sont vérifiées par des règles de calcul fixes et par Stockfish, qui tourne dans votre navigateur."),
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
      body = fix(f"""<h1>{html.escape(t['title'])}</h1>
<p class="lead">{t['lead']}</p>
<p><a class="cta" href="{'../' * path.count('/')}?play={g['play']}">{w['try_top'].format(name=t['name'])}</a></p>
<figure><img src="{'../' * path.count('/')}learn/img/{img}" width="390" height="844" alt="{html.escape(t['alt'])}" loading="lazy"><figcaption>{t['caption']}</figcaption></figure>
{t['body'].strip()}
<h2>{w['try_h']}</h2>
<p>{w['try_p'].format(name=t['name'])}</p>
<p><a class="cta" href="{'../' * path.count('/')}?play={g['play']}">{w['play'].format(name=t['name'])}</a></p>""")
      ld = [{ '@context': 'https://schema.org', '@type': 'Article', 'headline': t['title'], 'description': t['desc'], 'inLanguage': lang,
              'image': SITE + f'learn/img/{img}', 'url': SITE + path.removesuffix('index.html'),
              'publisher': { '@type': 'Organization', 'name': 'ChessStrategy.org', 'url': SITE } },
            { '@context': 'https://schema.org', **crumbs(('Guides', HUB[lang]), (t['name'], path.removesuffix('index.html'))) }]
      out[path] = page(path, lang, t['title'], t['desc'], body, alt, ld)
      urls.append(path.removesuffix('index.html'))
    # the index: the guides, then the FAQ
    path = HUB[lang] + 'index.html'
    cards = ''.join(f'<a class="card" href="{g[lang]["slug"]}/"><strong>{g[lang]["name"]}</strong><span>{html.escape(g[lang]["title"])}</span></a>' for g in GUIDES)
    faq = ''.join(f'<h3 class="faq-h">{html.escape(sec)}</h3>' + ''.join(f'<details><summary>{html.escape(q)}</summary><div class="a">{a}</div></details>' for q, a in qs) for sec, qs in FAQ[lang])
    hub = fix(f"""<h1>{html.escape(w['hub_title'])}</h1>
<p class="lead">{w['hub_lead']}</p>
<div class="cards">{cards}</div>
<p>{w['hub_more']}</p>
<p><a class="cta" href="{'../' * path.count('/')}">{w['start']}</a></p>
<h2 id="faq">{w['questions']}</h2>
{faq}""")
    plain = lambda h: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fix(h)))).strip()
    ld = [{ '@context': 'https://schema.org', '@type': 'CollectionPage', 'name': w['hub_title'], 'url': SITE + HUB[lang], 'inLanguage': lang,
            'hasPart': [{ '@type': 'Article', 'headline': g[lang]['title'], 'url': SITE + HUB[lang] + g[lang]['slug'] + '/' } for g in GUIDES] },
          { '@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': lang,
            'mainEntity': [{ '@type': 'Question', 'name': plain(q), 'acceptedAnswer': { '@type': 'Answer', 'text': plain(a) } } for _, qs in FAQ[lang] for q, a in qs] }]
    out[path] = page(path, lang, w['hub_page'], w['hub_desc'], hub, HUB[other] + 'index.html', ld, kind='website')
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
