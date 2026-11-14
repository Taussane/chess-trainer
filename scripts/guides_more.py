# The guides, the FAQ and the words around them in German, Spanish and Italian (build-pages.py merges them with
# its English and French). Same order and keys as there.

GUIDES_MORE = {
'imbalances': dict(
  de=dict(slug='ungleichgewichte-im-schach', name='Ungleichgewichte', sub='Lerne, eine Stellung zu lesen',
    title='Ungleichgewichte im Schach: lerne, eine Stellung zu lesen',
    desc='Was Ungleichgewichte im Schach sind (Material, Bauern, Raum, Aktivität, Königssicherheit, Drohungen), wie man sie abwägt, und eine kostenlose Übung, um sie an Meisterpartien und deinen eigenen Partien zu lesen.',
    lead='Jede Stellung ist eine Reihe von Unterschieden zwischen beiden Seiten. Starke Spieler erkennen die wenigen, die die Partie entscheiden, und planen danach: eine Idee, die Jeremy Silman bekannt gemacht hat.',
    alt='Auswertung der Übung Ungleichgewichte in einer WM-Stellung von 1929: Aktivität und Bauern für Weiß richtig, Material für Schwarz gewählt, obwohl ausgeglichen, Raum für Schwarz verpasst',
    caption='Aktivität und Bauern für Weiß: richtig. Material wurde Schwarz gegeben, ist aber ausgeglichen: Raum war die richtige Wahl.',
    body="""
<h2>Die sechs Ungleichgewichte</h2>
<ul>
  <li><strong>Material</strong>: Bauer 1, Springer und Läufer 3, Turm 5, Dame 9; das Läuferpaar zählt einen halben Bauern extra.</li>
  <li><strong>Bauern</strong>: Frei- und verbundene Bauern, umso mehr, je weiter sie vorgerückt sind; isolierte, doppelte und rückständige Bauern zählen dagegen.</li>
  <li><strong>Raum</strong>: die Bauern und die sicheren Felder dahinter im Zentrum.</li>
  <li><strong>Aktivität</strong>: die sicheren Felder, die deine Figuren erreichen, Vorposten, offene Linien. Zu Partiebeginn stattdessen die <strong>Entwicklung</strong>.</li>
  <li><strong>Königssicherheit</strong>: der Bauernschutz gegen angreifende Figuren. Ohne Damen stattdessen die <strong>Königsaktivität</strong>.</li>
  <li><strong>Drohungen</strong>: Material, das du sofort gewinnen kannst, und Drohungen für den nächsten Zug, etwa ein Bauernzug, der eine Figur angreift.</li>
</ul>
<p>Material, Bauern und Raum sind <em>statisch</em>: Sie bleiben meist bestehen. Die anderen sind <em>dynamisch</em>: Nutze sie, bevor sie verblassen.</p>

<h2>Die Übung</h2>
<p>Wähle 3 der Ungleichgewichte, die die Stellung entscheiden (es können mehr als 3 sein), und wer den Vorteil hat. Die Auswertung zeigt die Größe jedes einzelnen: <strong>=</strong> ausgeglichen; <strong>+</strong> oder <strong>++</strong> ein kleiner oder großer Vorteil für Weiß, <strong>−</strong> oder <strong>−−</strong> für Schwarz. Eine Wahl unter den 3 größten Vorteilen, auf der richtigen Seite, bringt volle Punkte; ein kleinerer Vorteil die Hälfte; ein ausgeglichener oder die falsche Seite nichts.</p>
<p>Suche zuerst die ++. Ein großes Ungleichgewicht kann mehrere kleine aufwiegen, und Taktik schlägt sie alle.</p>
"""),
  es=dict(slug='desequilibrios-en-ajedrez', name='Desequilibrios', sub='Aprende a leer una posición',
    title='Los desequilibrios en ajedrez: aprende a leer una posición',
    desc='Qué son los desequilibrios en ajedrez (material, peones, espacio, actividad, seguridad del rey, amenazas), cómo sopesarlos, y un ejercicio gratuito para practicar su lectura en partidas de maestros y en tus propias partidas.',
    lead='Cada posición es un conjunto de diferencias entre los dos bandos. Los jugadores fuertes detectan las pocas que deciden la partida y planifican en torno a ellas: una idea que hizo famosa Jeremy Silman.',
    alt='Corrección de Desequilibrios en una posición del Campeonato del Mundo de 1929: Actividad y Peones para las blancas, correctos; Material dado a las negras aunque está equilibrado; Espacio para las negras, olvidado',
    caption='Actividad y Peones para las blancas: correcto. El Material se dio a las negras, pero está equilibrado: había que elegir el Espacio.',
    body="""
<h2>Los seis desequilibrios</h2>
<ul>
  <li><strong>Material</strong>: peón 1, caballo y alfil 3, torre 5, dama 9; la pareja de alfiles suma medio peón.</li>
  <li><strong>Peones</strong>: peones pasados y ligados, más cuanto más avanzados; los peones aislados, doblados y retrasados cuentan en contra.</li>
  <li><strong>Espacio</strong>: los peones y las casillas seguras detrás de ellos en el centro.</li>
  <li><strong>Actividad</strong>: las casillas seguras que alcanzan tus piezas, los puestos avanzados, las columnas abiertas. Al principio de la partida, el <strong>Desarrollo</strong> en su lugar.</li>
  <li><strong>Seguridad del rey</strong>: el refugio de peones frente a las piezas atacantes. Sin damas, la <strong>Actividad del rey</strong> en su lugar.</li>
  <li><strong>Amenazas</strong>: el material que puedes ganar ya, y las amenazas para la siguiente jugada, como un avance de peón que ataca una pieza.</li>
</ul>
<p>Material, Peones y Espacio son <em>estáticos</em>: tienden a durar. Los demás son <em>dinámicos</em>: úsalos antes de que se desvanezcan.</p>

<h2>El ejercicio</h2>
<p>Elige 3 de los desequilibrios que deciden la posición (puede haber más de 3) y quién tiene la ventaja. La corrección muestra el tamaño de cada uno: <strong>=</strong> equilibrado; <strong>+</strong> o <strong>++</strong> una ventaja pequeña o grande para las blancas, <strong>−</strong> o <strong>−−</strong> para las negras. Una elección entre las 3 mayores ventajas, del bando correcto, suma todos los puntos; una ventaja menor, la mitad; uno equilibrado o del bando equivocado, nada.</p>
<p>Busca primero los ++. Un gran desequilibrio puede pesar más que varios pequeños, y la táctica les gana a todos.</p>
"""),
  it=dict(slug='squilibri-negli-scacchi', name='Squilibri', sub='Impara a leggere una posizione',
    title='Gli squilibri negli scacchi: impara a leggere una posizione',
    desc='Cosa sono gli squilibri negli scacchi (materiale, pedoni, spazio, attività, sicurezza del re, minacce), come valutarli, e un esercizio gratuito per allenarti a leggerli su partite di maestri e sulle tue partite.',
    lead='Ogni posizione è un insieme di differenze tra i due lati. I giocatori forti individuano le poche che decidono la partita e ci costruiscono il piano attorno: un\'idea resa celebre da Jeremy Silman.',
    alt='Correzione di Squilibri su una posizione del Campionato del mondo 1929: Attività e Pedoni al Bianco giusti, Materiale dato al Nero anche se equilibrato, Spazio al Nero mancato',
    caption='Attività e Pedoni al Bianco: giusto. Il Materiale è stato dato al Nero, ma è equilibrato: andava scelto lo Spazio.',
    body="""
<h2>I sei squilibri</h2>
<ul>
  <li><strong>Materiale</strong>: pedone 1, cavallo e alfiere 3, torre 5, donna 9; la coppia degli alfieri aggiunge mezzo pedone.</li>
  <li><strong>Pedoni</strong>: pedoni passati e collegati, tanto più quanto sono avanzati; i pedoni isolati, doppiati e arretrati contano contro.</li>
  <li><strong>Spazio</strong>: i pedoni e le case sicure dietro di loro al centro.</li>
  <li><strong>Attività</strong>: le case sicure che raggiungono i tuoi pezzi, gli avamposti, le colonne aperte. All'inizio della partita, lo <strong>Sviluppo</strong> al suo posto.</li>
  <li><strong>Sicurezza del re</strong>: il riparo di pedoni contro i pezzi che attaccano. Senza donne, l'<strong>Attività del re</strong> al suo posto.</li>
  <li><strong>Minacce</strong>: il materiale che puoi vincere subito, e le minacce per la mossa successiva, come una spinta di pedone che attacca un pezzo.</li>
</ul>
<p>Materiale, Pedoni e Spazio sono <em>statici</em>: tendono a durare. Gli altri sono <em>dinamici</em>: usali prima che svaniscano.</p>

<h2>L'esercizio</h2>
<p>Scegli 3 degli squilibri che decidono la posizione (possono essere più di 3) e chi ha il vantaggio. La correzione mostra la misura di ciascuno: <strong>=</strong> equilibrato; <strong>+</strong> o <strong>++</strong> un vantaggio piccolo o grande per il Bianco, <strong>−</strong> o <strong>−−</strong> per il Nero. Una scelta tra i 3 vantaggi più grandi, dal lato giusto, vale tutti i punti; un vantaggio più piccolo, metà; uno equilibrato o dal lato sbagliato, niente.</p>
<p>Cerca prima i ++. Un grande squilibrio può pesare più di diversi piccoli, e la tattica batte tutti.</p>
""")),

'planq': dict(
  de=dict(slug='schachplan-finden', name='Planfindung', sub='Wie man im Schach einen allgemeinen Plan findet',
    title='Wie man im Schach einen Plan findet',
    desc='Wie man im Schach einen Plan macht: prüfen, was dringend ist, beurteilen, wer besser steht, dann entscheiden, ob getauscht und ob angegriffen oder verbessert wird. Eine kostenlose Übung an Meisterstellungen und deinen eigenen Partien.',
    lead='„Ein schlechter Plan ist besser als gar keiner“, sagt die alte Weisheit (oft Tschigorin zugeschrieben). Ein Plan gibt dir eine Richtung für die Suche nach guten Zügen und hilft dir, bessere Entscheidungen zu treffen. Vier Fragen, der Reihe nach, können zu einem führen.',
    alt='Auswertung der Planfindung in einer WM-Stellung von 1963: Figuren behalten richtig, Beides statt Öffnen / Angreifen, 75 %',
    caption='Der schwarze König steckt im Zentrum fest, und die weiße Dame steht schon auf g6. Dieser schwache König entscheidet den Plan.',
    body="""
<h2>Vier Fragen</h2>
<ol>
  <li><strong>Etwas Dringendes?</strong> Schachs, Schlagzüge und Drohungen, für beide Seiten: etwas zu gewinnen oder zu verteidigen, etwa ein Bauer oder die Qualität. (Stellungen, in denen eine Figur oder mehr auf dem Spiel steht, sind ausgenommen: Dort entscheidet die Drohung den Zug.)</li>
  <li><strong>Wer steht besser?</strong> Die Ungleichgewichte abzuwägen ist ein guter Weg, das einzuschätzen, und die entscheidendsten sollten die Kernpunkte deines Plans bestimmen. Ausgeglichen heißt: die Engine innerhalb eines halben Bauern.</li>
  <li><strong>Tauschen oder Figuren behalten?</strong> Abtausch hilft der Seite mit mehr Material, mit besseren Bauern oder mit weniger Raum. Behalte die Figuren mit besseren Figuren, mehr Raum oder gegen einen schwachen König.</li>
  <li><strong>Angreifen oder verbessern?</strong> Ein Vorteil, der verblasst (aktive Figuren, Entwicklungsvorsprung, ein schwacher König), verlangt, die Stellung zu öffnen und anzugreifen. Einer, der bleibt (Material, Bauern, Raum), lässt Zeit zum Verbessern.</li>
</ol>

<h2>Die Übung</h2>
<p>Beantworte die ersten beiden Fragen, prüfe, dann die letzten beiden. Jede Antwort ist ein Viertel der Wertung.</p>
<p>Der Plan folgt den Ungleichgewichten. Wenn sie in beide Richtungen ziehen, zählen beide Antworten.</p>
"""),
  es=dict(slug='como-hacer-un-plan-en-ajedrez', name='Búsqueda del plan', sub='Cómo encontrar un plan general en ajedrez',
    title='Cómo hacer un plan en ajedrez',
    desc='Cómo hacer un plan en ajedrez: ver qué es urgente, juzgar quién está mejor, y decidir si cambiar piezas y si atacar o mejorar. Un ejercicio gratuito con posiciones de maestros y tus propias partidas.',
    lead='«Un mal plan es mejor que ningún plan», dice el viejo refrán (a menudo atribuido a Chigorin). Un plan te da una dirección para buscar buenas jugadas y te ayuda a tomar mejores decisiones. Cuatro preguntas, en orden, pueden llevarte a uno.',
    alt='Corrección de Búsqueda del plan en una posición del Campeonato del Mundo de 1963: Mantener piezas correcto, Cualquiera en vez de Abrir / Atacar, 75 %',
    caption='El rey negro sigue atrapado en el centro, con la dama blanca ya en g6. Ese rey débil decide el plan.',
    body="""
<h2>Cuatro preguntas</h2>
<ol>
  <li><strong>¿Algo urgente?</strong> Jaques, capturas y amenazas, de ambos bandos: algo que ganar o que defender, como un peón o la calidad. (Las posiciones donde está en juego una pieza o más quedan fuera: ahí, la amenaza decide la jugada.)</li>
  <li><strong>¿Quién está mejor?</strong> Sopesar los desequilibrios es una buena forma de juzgarlo, y los más decisivos deberían dar forma a los aspectos clave de tu plan. Equilibrada significa el motor a menos de medio peón.</li>
  <li><strong>¿Cambiar o mantener las piezas?</strong> Los cambios ayudan al bando con más material, con mejores peones o con menos espacio. Mantén las piezas con mejores piezas, más espacio o frente a un rey débil.</li>
  <li><strong>¿Atacar o mejorar?</strong> Una ventaja que se desvanece (piezas activas, ventaja en desarrollo, un rey débil) pide abrir y atacar. Una que dura (material, peones, espacio) deja tiempo para mejorar.</li>
</ol>

<h2>El ejercicio</h2>
<p>Responde las dos primeras preguntas, comprueba, y luego las dos últimas. Cada respuesta vale una cuarta parte de la puntuación.</p>
<p>El plan sigue a los desequilibrios. Cuando tiran en ambos sentidos, las dos respuestas cuentan.</p>
"""),
  it=dict(slug='trovare-un-piano-negli-scacchi', name='Ricerca del piano', sub='Come trovare un piano generale negli scacchi',
    title='Come trovare un piano negli scacchi',
    desc='Come fare un piano negli scacchi: vedere cosa è urgente, giudicare chi sta meglio, poi decidere se cambiare i pezzi e se attaccare o migliorare. Un esercizio gratuito su posizioni di maestri e sulle tue partite.',
    lead='«Un cattivo piano è meglio di nessun piano», dice il vecchio adagio (spesso attribuito a Čigorin). Un piano ti dà una direzione per cercare buone mosse e ti aiuta a prendere decisioni migliori. Quattro domande, in ordine, possono portarti a uno.',
    alt='Correzione di Ricerca del piano su una posizione del Campionato del mondo 1963: Tieni i pezzi giusto, Indifferente invece di Apri / Attacca, 75%',
    caption='Il re nero è bloccato al centro, con la donna bianca già in g6. Quel re debole decide il piano.',
    body="""
<h2>Quattro domande</h2>
<ol>
  <li><strong>Qualcosa di urgente?</strong> Scacchi, catture e minacce, per entrambi i lati: qualcosa da vincere o da difendere, come un pedone o la qualità. (Le posizioni in cui è in gioco un pezzo o più sono escluse: lì è la minaccia a decidere la mossa.)</li>
  <li><strong>Chi sta meglio?</strong> Valutare gli squilibri è un buon modo per giudicarlo, e i più decisivi dovrebbero dare forma agli aspetti chiave del tuo piano. Equilibrata vuol dire il motore entro mezzo pedone.</li>
  <li><strong>Cambiare o tenere i pezzi?</strong> I cambi aiutano il lato con più materiale, con pedoni migliori o con meno spazio. Tieni i pezzi con pezzi migliori, più spazio o contro un re debole.</li>
  <li><strong>Attaccare o migliorare?</strong> Un vantaggio che svanisce (pezzi attivi, vantaggio di sviluppo, un re debole) chiede di aprire e attaccare. Uno che dura (materiale, pedoni, spazio) lascia il tempo di migliorare.</li>
</ol>

<h2>L'esercizio</h2>
<p>Rispondi alle prime due domande, verifica, poi alle ultime due. Ogni risposta vale un quarto del punteggio.</p>
<p>Il piano segue gli squilibri. Quando tirano in entrambe le direzioni, valgono tutte e due le risposte.</p>
""")),

'candidates': dict(
  de=dict(slug='kandidatenzuege', name='Kandidatenzüge', sub='Einen oder mehrere gute Züge finden',
    title='Kandidatenzüge im Schach: mehr als einen guten Zug finden',
    desc='Was Kandidatenzüge sind, wie man sie findet (Schachs, Schlagzüge, Drohungen, dann der Plan), und eine kostenlose Übung, die deine Wahl mit Stockfish bewertet, an Meisterpartien und deinen eigenen Partien.',
    lead='Die meisten Fehler entstehen, wenn man den ersten Zug spielt, der gut aussieht. Alexander Kotows Rat: zuerst einige ernsthafte Optionen auflisten, dann wählen.',
    alt='Auswertung der Kandidatenzüge in einer WM-Stellung von 2024: bxa3 und Qa5, die beiden besten Züge der Engine, dann h5, zweifelhaft; auch der dritte Zug der Engine ist zweifelhaft',
    caption='Hier halten nur zwei Züge, bxa3 und Qa5, und beide wurden gefunden. Die dritte Wahl hätte man aber weglassen sollen.',
    body="""
<h2>Wie man sie findet</h2>
<ul>
  <li><strong>Zuerst forcierende Züge</strong>: Schachs, Schlagzüge und Drohungen, für beide Seiten.</li>
  <li><strong>Dann Züge, die dem <a href="../schachplan-finden/">Plan</a> folgen</strong>: Sie holen das Beste aus deinen entscheidendsten Ungleichgewichten heraus oder verringern die des Gegners.</li>
  <li><strong>Denk an die Partiephase</strong>, besonders wenn der Plan ist, zu verbessern: In der Eröffnung entwickeln und den König in Sicherheit bringen; im Mittelspiel bessere Felder für deine Figuren finden und deine Schwächen beheben; im Endspiel den König aktivieren und deine Freibauern vorschieben.</li>
</ul>

<h2>Die Übung</h2>
<p>Wähle 1 bis 3 starke Züge. Stockfish bewertet jeden im Vergleich zu seinem besten Zug: Bester, Gut, Ok, Zweifelhaft, Fehler oder Patzer. Zweifelhaft oder schlechter bringt nichts: Im Zweifel lieber weniger wählen.</p>
"""),
  es=dict(slug='jugadas-candidatas', name='Jugadas candidatas', sub='Encuentra una o más buenas jugadas',
    title='Jugadas candidatas en ajedrez: encuentra más de una buena jugada',
    desc='Qué son las jugadas candidatas, cómo encontrarlas (jaques, capturas, amenazas, luego el plan), y un ejercicio gratuito que califica tus elecciones con Stockfish en partidas de maestros y en tus propias partidas.',
    lead='La mayoría de los errores vienen de jugar la primera jugada que parece buena. El consejo de Alexander Kotov: haz primero una lista de algunas opciones serias, luego elige.',
    alt='Corrección de Jugadas candidatas en una posición del Campeonato del Mundo de 2024: bxa3 y Qa5, las dos mejores del motor, luego h5, dudosa; la propia 3.ª jugada del motor también es dudosa',
    caption='Aquí solo aguantan dos jugadas, bxa3 y Qa5, y se encontraron las dos. Pero la tercera elección debía haberse evitado.',
    body="""
<h2>Cómo encontrarlas</h2>
<ul>
  <li><strong>Primero las jugadas forzantes</strong>: jaques, capturas y amenazas, de ambos bandos.</li>
  <li><strong>Luego las jugadas que siguen el <a href="../como-hacer-un-plan-en-ajedrez/">plan</a></strong>: sacan el máximo de tus desequilibrios más decisivos, o reducen los del rival.</li>
  <li><strong>Ten en cuenta la fase de la partida</strong>, sobre todo cuando el plan es mejorar: en la apertura, desarrolla y pon a salvo tu rey; en el medio juego, busca mejores casillas para tus piezas y corrige tus debilidades; en el final, activa tu rey y avanza tus peones pasados.</li>
</ul>

<h2>El ejercicio</h2>
<p>Elige de 1 a 3 jugadas fuertes. Stockfish califica cada una frente a su mejor jugada: Mejor, Buena, Aceptable, Dudosa, Error o Error grave. Dudosa o peor no suma nada: ante la duda, elige menos.</p>
"""),
  it=dict(slug='mosse-candidate', name='Mosse candidate', sub='Trova una o più buone mosse',
    title='Le mosse candidate negli scacchi: trova più di una buona mossa',
    desc='Cosa sono le mosse candidate, come trovarle (scacchi, catture, minacce, poi il piano), e un esercizio gratuito che valuta le tue scelte con Stockfish su partite di maestri e sulle tue partite.',
    lead='La maggior parte degli errori nasce dal giocare la prima mossa che sembra buona. Il consiglio di Aleksandr Kotov: elenca prima alcune opzioni serie, poi scegli.',
    alt='Correzione di Mosse candidate su una posizione del Campionato del mondo 2024: bxa3 e Qa5, le due migliori del motore, poi h5, dubbia; anche la 3ª mossa del motore è dubbia',
    caption='Qui reggono solo due mosse, bxa3 e Qa5, e sono state trovate entrambe. La terza scelta però andava evitata.',
    body="""
<h2>Come trovarle</h2>
<ul>
  <li><strong>Prima le mosse forzanti</strong>: scacchi, catture e minacce, per entrambi i lati.</li>
  <li><strong>Poi le mosse che seguono il <a href="../trovare-un-piano-negli-scacchi/">piano</a></strong>: sfruttano al meglio i tuoi squilibri più decisivi, o riducono quelli dell'avversario.</li>
  <li><strong>Tieni presente la fase della partita</strong>, soprattutto quando il piano è migliorare: in apertura sviluppa e metti al sicuro il re; nel mediogioco trova case migliori per i tuoi pezzi e correggi le tue debolezze; nel finale attiva il re e spingi i tuoi pedoni passati.</li>
</ul>

<h2>L'esercizio</h2>
<p>Scegli da 1 a 3 mosse forti. Stockfish valuta ciascuna rispetto alla sua mossa migliore: Migliore, Buona, Accettabile, Dubbia, Errore o Errore grave. Dubbia o peggio non vale niente: nel dubbio, scegline meno.</p>
""")),

'final': dict(
  de=dict(slug='besten-zug-waehlen', name='Zugwahl', sub='Wie man den besten Zug wählt',
    title='Wie man im Schach den besten Zug wählt',
    desc='Wie man im Schach zwischen gut aussehenden Zügen wählt: den besten finden, dann prüfen, was jeder Zug zulässt. Eine kostenlose Übung, in der du vier Züge aus Meisterpartien und deinen eigenen Partien ordnest.',
    lead='Mehrere Züge mögen gut aussehen, aber nur einer ist der beste. Wenn das Erkunden der <a href="../kandidatenzuege/">Kandidatenzüge</a> dir einige ernsthafte Optionen gegeben hat, bleibt als letzter Schritt die Wahl zwischen ihnen, und genau dort gehen viele Partien verloren.',
    alt='Auswertung der Zugwahl in einer WM-Stellung von 1963: vier Züge geordnet, der Partiezug Nxe4 ist der beste, zwei zweifelhafte',
    caption='Der Partiezug Nxe4 ist der beste und wurde gefunden. Qh2, der einzige andere spielbare Zug, hätte auf Platz 2 gehört.',
    body="""
<h2>Deine Optionen ordnen</h2>
<ul>
  <li><strong>Prüfe jeden Zug auf einen Patzer</strong>: Schau dir die Schachs, Schlagzüge und Drohungen des Gegners danach an. Ein Zug, der Material verliert oder deinen König entblößt, rutscht meist nach unten, so bedrohlich er auch aussieht.</li>
  <li><strong>Vergleiche die entstehenden Stellungen</strong>: Bevorzuge Züge, die das Beste aus deinen Vorteilen machen oder die des Gegners verringern, wie es dein Plan verlangt.</li>
  <li><strong>Wenn zwei Züge gleich aussehen</strong>, verliere nicht zu viel Zeit damit: Wenn sie wirklich gleich stark sind, ändert die Wahl wenig.</li>
</ul>

<h2>Die Übung</h2>
<p>Ordne vier Züge vom besten zum schlechtesten. Einer wurde in der Partie gespielt. In deinen eigenen Partien kommen deine Fehler zuerst: eine zweite Chance bei einer Entscheidung, die schiefging.</p>
<p>Den besten Zug zu finden ist die halbe Wertung: Platz 1 zählt 50 %, Platz 2 30 %, Platz 3 20 %, jeweils im Vergleich zum besten verbleibenden Zug.</p>
"""),
  es=dict(slug='elegir-la-mejor-jugada', name='Elección de jugada', sub='Cómo elegir la mejor jugada',
    title='Cómo elegir la mejor jugada en ajedrez',
    desc='Cómo elegir entre jugadas que parecen buenas: encontrar la mejor y comprobar lo que permite cada una. Un ejercicio gratuito en el que ordenas cuatro jugadas de partidas de maestros y de tus propias partidas.',
    lead='Varias jugadas pueden parecer buenas, pero solo una es la mejor. Cuando explorar las <a href="../jugadas-candidatas/">jugadas candidatas</a> te ha dado algunas opciones serias, queda el último paso: elegir entre ellas, y ahí es donde se pierden muchas partidas.',
    alt='Corrección de Elección de jugada en una posición del Campeonato del Mundo de 1963: cuatro jugadas ordenadas, la jugada de la partida Nxe4 es la mejor, dos dudosas',
    caption='La jugada de la partida, Nxe4, es la mejor y se encontró. Qh2, la única otra jugada jugable, debía ir 2.ª.',
    body="""
<h2>Ordenar tus opciones</h2>
<ul>
  <li><strong>Comprueba que ninguna jugada sea un error grave</strong>: mira los jaques, capturas y amenazas del rival después de ella. Una jugada que pierde material o expone tu rey suele bajar en la lista, por amenazante que parezca.</li>
  <li><strong>Compara las posiciones a las que llegas</strong>: prefiere las jugadas que sacan el máximo de tus ventajas o reducen las del rival, como pide tu plan.</li>
  <li><strong>Cuando dos jugadas parecen iguales</strong>, no les dediques demasiado tiempo: si de verdad tienen una fuerza parecida, la elección no cambiará mucho.</li>
</ul>

<h2>El ejercicio</h2>
<p>Ordena cuatro jugadas de la mejor a la peor. Una se jugó en la partida. En tus propias partidas, tus errores van primero: una segunda oportunidad en una decisión que salió mal.</p>
<p>Encontrar la mejor jugada es la mitad de la puntuación: el 1.er puesto vale el 50 %, el 2.º el 30 %, el 3.º el 20 %, cada uno comparado con la mejor jugada restante.</p>
"""),
  it=dict(slug='scegliere-la-mossa-migliore', name='Scelta della mossa', sub='Come scegliere la mossa migliore',
    title='Come scegliere la mossa migliore negli scacchi',
    desc='Come scegliere tra mosse che sembrano buone: trovare la migliore, poi verificare cosa concede ogni mossa. Un esercizio gratuito in cui ordini quattro mosse da partite di maestri e dalle tue partite.',
    lead='Diverse mosse possono sembrare buone, ma solo una è la migliore. Quando l\'esplorazione delle <a href="../mosse-candidate/">mosse candidate</a> ti ha dato alcune opzioni serie, resta l\'ultimo passo: scegliere tra loro, ed è lì che si perdono molte partite.',
    alt='Correzione di Scelta della mossa su una posizione del Campionato del mondo 1963: quattro mosse ordinate, la mossa della partita Nxe4 è la migliore, due dubbie',
    caption='La mossa della partita, Nxe4, è la migliore ed è stata trovata. Qh2, l\'unica altra mossa giocabile, andava messa 2ª.',
    body="""
<h2>Ordinare le opzioni</h2>
<ul>
  <li><strong>Verifica che nessuna mossa sia un errore grave</strong>: guarda gli scacchi, le catture e le minacce dell'avversario dopo di essa. Una mossa che perde materiale o espone il re di solito scende in classifica, per quanto minacciosa sembri.</li>
  <li><strong>Confronta le posizioni che ottieni</strong>: preferisci le mosse che sfruttano al meglio i tuoi vantaggi o riducono quelli dell'avversario, come chiede il tuo piano.</li>
  <li><strong>Quando due mosse sembrano equivalenti</strong>, non perderci troppo tempo: se hanno davvero una forza simile, la scelta non cambierà molto.</li>
</ul>

<h2>L'esercizio</h2>
<p>Ordina quattro mosse dalla migliore alla peggiore. Una è stata giocata nella partita. Nelle tue partite i tuoi errori vengono prima: una seconda possibilità su una decisione andata male.</p>
<p>Trovare la mossa migliore vale metà del punteggio: il 1º posto conta il 50%, il 2º il 30%, il 3º il 20%, ciascuno confrontato con la migliore mossa rimasta.</p>
""")),
}

FAQ_MORE = {
'de': [
  ('Über die App', [
    ('Was trainiert sie?', 'Strategie: was in einer ruhigen Stellung zu tun ist, wenn es keine Taktik zu finden gibt. Taktik-Apps trainieren Taktik sehr gut, aber die meisten Partien entscheiden sich in Stellungen, in denen die Frage nicht „Was gewinnt?“ lautet, sondern „Was ist los, und worauf sollte ich hinarbeiten?“.'),
    ('Für wen ist sie?', 'Für Vereinsspieler, die ihre Taktik schon kennen und nicht weiterwissen, wenn die Stellung ruhig ist: kein Plan, oder ein Plan, der nicht zur Stellung passt.'),
    ('Wie lehrt sie?', 'Durch Übung an echten Stellungen, mit einer Auswertung nach jeder Antwort. Jede Idee wird konkret: Ein Ungleichgewicht ist eine Zählung von Dingen auf dem Brett, die beim Antippen eingezeichnet wird, und jede Antwort wird von einer Engine oder einer gezählten Regel geprüft. Die Übungen folgen der Reihenfolge der Fragen, die sich starke Spieler stellen.'),
    ('Woher kommen die Ideen?', 'Aus den klassischen Strategiebüchern (Steinitz, Nimzowitsch, Capablanca, Kotow, Silman, Dworezki, Aagaard, Schereschewski) und aus der früheren Bewertung von Stockfish, die dieselben Dinge auf ihre Weise zählt.'),
  ]),
  ('Der Denkprozess', [
    ('Gibt es eine Reihenfolge, über eine Stellung nachzudenken?', 'Ja. Die Bücher sind sich einig, und jede Übung trainiert einen Schritt davon:<ol><li><b>Etwas Dringendes?</b> Schachs, Schlagzüge und Drohungen, für beide Seiten (Planfindung, Phase 1).</li><li><b>Was unterscheidet die beiden Seiten?</b> Die Ungleichgewichte (Übung Ungleichgewichte).</li><li><b>Wer steht besser?</b> Die zusammen abgewogenen Ungleichgewichte bestimmen deine Haltung: Die Seite mit dem Vorteil spielt, um ihn zu nutzen, die andere verteidigt (Planfindung, Phase 1).</li><li><b>Welcher Plan?</b> Tauschen oder Figuren behalten; öffnen und angreifen, oder geschlossen halten und verbessern (Planfindung, Phase 2).</li><li><b>Welche Züge?</b> Kandidatenzüge, die dem Plan dienen, dann die Wahl, jeden auf einen Patzer geprüft (Kandidatenzüge, Zugwahl).</li></ol>'),
    ('Warum getrennte Übungen und nicht eine Stellung von Anfang bis Ende?', 'Jeder Schritt bekommt sofort seine eigene Auswertung. Bei einer einzigen Stellung würde die Auswertung eines Schritts den nächsten verraten, und eine lange Kette macht jede Runde langsam. Die tägliche Routine geht die Schritte der Reihe nach durch, jeden an seiner eigenen Stellung.'),
    ('Und der Plan des Gegners?', 'Die Schachs, Schlagzüge und Drohungen des Gegners zu prüfen (Schritt 1) ist der erste Teil der Prophylaxe. Die ganze Frage, „Was will mein Gegner?“, kann später eine eigene Übung werden.'),
  ]),
  ('Wertungen und Fortschritt', [
    ('Was ist mein Durchschnitt?', 'Deine Genauigkeit in einer Übung, geglättet über die letzten Stellungen: zuerst ein einfacher Durchschnitt, dann verschiebt ihn jede neue Stellung um 15 % in Richtung ihrer Wertung. Eine schlechte Stellung kostet wenig; eine Serie guter hebt ihn stetig.'),
    ('Was ist die tägliche Routine?', 'Drei Stellungen jeder Übung am Tag, in so vielen Sitzungen, wie du magst, in der Reihenfolge des Denkprozesses.'),
    ('Was sind verpasste Stellungen?', 'Stellungen, in denen du unter deinem damaligen Durchschnitt lagst. Wiederholen spielt sie erneut; mindestens deinen Durchschnitt zu erreichen, nimmt eine von der Liste. Eine heute gespielte Stellung wartet bis morgen.'),
    ('Wo wird mein Fortschritt gespeichert?', 'In deinem Browser, und in deinem Konto, wenn du angemeldet bist, damit er dich auf jedem Gerät begleitet.'),
  ]),
  ('Stellungen und Engine', [
    ('Woher kommen die Stellungen?', 'Aus WM-Partien und, sobald du verbunden bist, aus deinen eigenen Lichess- und Chess.com-Partien. In deinen Partien sucht die App zuerst deine Fehler, dann weitere Stellungen, wie in Meisterpartien.'),
    ('Wie werden die Stellungen ausgewählt?', 'Nach Regeln, mit Stockfish geprüft: ruhige Stellungen, in denen Strategie zählt, über die Partie verteilt, nicht zu nah beieinander, und für jede Übung ein Grund, die Frage zu stellen. Remispartien liefern nur ihre unausgeglichenen Stellungen.'),
    ('Welche Engine?', 'Stockfish 19 (seine „Lite“-Version), die in deinem Browser läuft, sodass nichts irgendwohin geschickt wird: Jede Stellung wird bis Tiefe 20 berechnet, in höchstens ein paar Sekunden. Meisterstellungen kommen außerdem mit ihrer vorab berechneten Bewertung.'),
  ]),
  ('Quellen und Lesetipps', [
    ('Woher kommen die Klänge?', 'Die Zug- und Schlaggeräusche sind zwei Klänge, die aus <a href="https://freesound.org/s/792572/">„chess piece“ von imrius</a> (freesound.org) geschnitten wurden, lizenziert unter <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Änderungen: geschnitten, Hintergrundrauschen reduziert, Lautstärke angeglichen.'),
    ('Welche Bücher stehen hinter der App?', '<ul><li><b>Jeremy Silman, <i>How to Reassess Your Chess</i>:</b> Ungleichgewichte und wie sie zu einem Plan führen.</li><li><b>Aron Nimzowitsch, <i>Mein System</i>:</b> offene Linien, Vorposten, Bauernketten, Blockade, Prophylaxe.</li><li><b>José Raúl Capablanca, <i>Grundzüge der Schachstrategie</i>:</b> die Grundlagen jeder Phase.</li><li><b>Alexander Kotow, <i>Denke wie ein Großmeister</i>:</b> Kandidatenzüge und die Reihenfolge des Denkens.</li><li><b>Mark Dworezki und Artur Jussupow, <i>Positionelles Spiel</i>:</b> prophylaktisches Denken.</li><li><b>Jacob Aagaard, <i>Grandmaster Preparation: Positional Play</i>:</b> drei Fragen für jede ruhige Stellung.</li><li><b>Michail Schereschewski, <i>Endspielstrategie</i>:</b> der König, die zwei Schwächen und keine Eile.</li></ul>'),
  ]),
],
'es': [
  ('Sobre la app', [
    ('¿Qué entrena?', 'La estrategia: qué hacer en una posición tranquila, cuando no hay táctica que encontrar. Las apps de problemas entrenan muy bien la táctica, pero la mayoría de las partidas se deciden en posiciones donde la pregunta no es «¿qué gana?» sino «¿qué está pasando y a qué debo apuntar?».'),
    ('¿Para quién es?', 'Para jugadores de club que ya conocen su táctica y se sienten perdidos cuando la posición está tranquila: sin plan, o con un plan que no encaja con la posición.'),
    ('¿Cómo enseña?', 'Con práctica sobre posiciones reales, con una corrección tras cada respuesta. Cada idea se vuelve concreta: un desequilibrio es un recuento de cosas en el tablero, que se dibuja al tocarlo, y cada respuesta la comprueba un motor o una regla contada. Los ejercicios siguen el orden de las preguntas que se hacen los jugadores fuertes.'),
    ('¿De dónde salen las ideas?', 'De los libros clásicos de estrategia (Steinitz, Nimzowitsch, Capablanca, Kotov, Silman, Dvoretsky, Aagaard, Shereshevsky) y de la antigua evaluación de Stockfish, que cuenta lo mismo a su manera.'),
  ]),
  ('El proceso de pensamiento', [
    ('¿Hay un orden para pensar una posición?', 'Sí. Los libros coinciden en uno, y cada ejercicio entrena un paso:<ol><li><b>¿Algo urgente?</b> Jaques, capturas y amenazas, de ambos bandos (Búsqueda del plan, fase 1).</li><li><b>¿Qué diferencia a los dos bandos?</b> Los desequilibrios (ejercicio Desequilibrios).</li><li><b>¿Quién está mejor?</b> Los desequilibrios sopesados juntos deciden tu actitud: el bando con ventaja juega para aprovecharla, el otro defiende (Búsqueda del plan, fase 1).</li><li><b>¿Qué plan?</b> Cambiar o mantener las piezas; abrir y atacar, o mantener cerrado y mejorar (Búsqueda del plan, fase 2).</li><li><b>¿Qué jugadas?</b> Jugadas candidatas que sirvan al plan, y luego la elección, comprobando que ninguna sea un error grave (Jugadas candidatas, Elección de jugada).</li></ol>'),
    ('¿Por qué ejercicios separados y no una posición de principio a fin?', 'Cada paso tiene su corrección enseguida. En una sola posición, la corrección de un paso delataría el siguiente, y una cadena larga hace lenta cada ronda. La rutina diaria recorre los pasos en orden, cada uno en su propia posición.'),
    ('¿Y el plan del rival?', 'Comprobar los jaques, capturas y amenazas del rival (paso 1) es la primera parte de la profilaxis. La pregunta completa, «¿qué quiere mi rival?», podrá ser un ejercicio propio más adelante.'),
  ]),
  ('Puntuaciones y progreso', [
    ('¿Qué es mi media?', 'Tu precisión en un ejercicio, suavizada sobre las posiciones recientes: al principio una media simple, luego cada nueva posición la mueve un 15 % hacia su puntuación. Una mala posición cuesta poco; una serie de buenas la sube de forma constante.'),
    ('¿Qué es la rutina diaria?', 'Tres posiciones de cada ejercicio al día, en tantas sesiones como quieras, en el orden del pensamiento.'),
    ('¿Qué son las posiciones falladas?', 'Las posiciones en las que sacaste menos que tu media del momento. Repetir las vuelve a jugar; llegar al menos a tu media quita una de la lista. Una posición jugada hoy espera hasta mañana.'),
    ('¿Dónde se guarda mi progreso?', 'En tu navegador, y en tu cuenta cuando has iniciado sesión, para que te acompañe en todos tus dispositivos.'),
  ]),
  ('Las posiciones y el motor', [
    ('¿De dónde salen las posiciones?', 'De partidas del Campeonato del Mundo y, una vez conectado, de tus propias partidas de Lichess y Chess.com. En tus partidas, la app busca primero tus errores y luego otras posiciones, como en las partidas de maestros.'),
    ('¿Cómo se eligen las posiciones?', 'Con reglas, comprobadas con Stockfish: posiciones tranquilas donde la estrategia importa, repartidas por la partida, no demasiado cercanas entre sí, y para cada ejercicio un motivo para preguntar. Las partidas tablas solo aportan sus posiciones desequilibradas.'),
    ('¿Qué motor?', 'Stockfish 19 (su versión «lite»), que funciona en tu navegador, así que no se envía nada a ninguna parte: cada posición se analiza hasta la profundidad 20, en unos segundos como mucho. Las posiciones de maestros también traen su evaluación calculada de antemano.'),
  ]),
  ('Créditos y lecturas', [
    ('¿De dónde salen los sonidos?', 'Los sonidos de jugada y de captura son dos sonidos recortados de <a href="https://freesound.org/s/792572/">«chess piece» de imrius</a> (freesound.org), con licencia <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Cambios: recorte, ruido de fondo reducido, volumen igualado.'),
    ('¿Qué libros hay detrás de la app?', '<ul><li><b>Jeremy Silman, <i>Cómo reevaluar su ajedrez</i>:</b> los desequilibrios y cómo llevan a un plan.</li><li><b>Aron Nimzowitsch, <i>Mi sistema</i>:</b> columnas abiertas, puestos avanzados, cadenas de peones, bloqueo, profilaxis.</li><li><b>José Raúl Capablanca, <i>Fundamentos del ajedrez</i>:</b> las bases de cada fase.</li><li><b>Alexander Kotov, <i>Piense como un gran maestro</i>:</b> las jugadas candidatas y el orden del pensamiento.</li><li><b>Mark Dvoretsky y Artur Yusupov, <i>Positional Play</i>:</b> el pensamiento profiláctico.</li><li><b>Jacob Aagaard, <i>Grandmaster Preparation: Positional Play</i>:</b> tres preguntas para cualquier posición tranquila.</li><li><b>Mijaíl Shereshevsky, <i>Estrategia de finales</i>:</b> el rey, las dos debilidades y no tener prisa.</li></ul>'),
  ]),
],
'it': [
  ("Sull'app", [
    ('Cosa allena?', 'La strategia: cosa fare in una posizione tranquilla, quando non c\'è una tattica da trovare. Le app di problemi allenano molto bene la tattica, ma la maggior parte delle partite si decide in posizioni dove la domanda non è «cosa vince?» ma «cosa sta succedendo, e a cosa devo puntare?».'),
    ('A chi è rivolta?', 'Ai giocatori di club che conoscono già la tattica e si sentono persi quando la posizione è tranquilla: nessun piano, o un piano che non si adatta alla posizione.'),
    ('Come insegna?', 'Con la pratica su posizioni reali, con una correzione dopo ogni risposta. Ogni idea diventa concreta: uno squilibrio è un conteggio di cose sulla scacchiera, disegnato quando lo tocchi, e ogni risposta è verificata da un motore o da una regola di calcolo. Gli esercizi seguono l\'ordine delle domande che si pongono i giocatori forti.'),
    ('Da dove vengono le idee?', 'Dai libri classici di strategia (Steinitz, Nimzowitsch, Capablanca, Kotov, Silman, Dvoretsky, Aagaard, Shereshevsky) e dalla vecchia valutazione di Stockfish, che conta le stesse cose a modo suo.'),
  ]),
  ('Il processo di pensiero', [
    ("C'è un ordine per pensare a una posizione?", 'Sì. I libri concordano su uno, e ogni esercizio ne allena un passo:<ol><li><b>Qualcosa di urgente?</b> Scacchi, catture e minacce, per entrambi i lati (Ricerca del piano, fase 1).</li><li><b>Cosa distingue i due lati?</b> Gli squilibri (esercizio Squilibri).</li><li><b>Chi sta meglio?</b> Gli squilibri valutati insieme decidono il tuo atteggiamento: il lato in vantaggio gioca per sfruttarlo, l\'altro si difende (Ricerca del piano, fase 1).</li><li><b>Quale piano?</b> Cambiare o tenere i pezzi; aprire e attaccare, o tenere chiuso e migliorare (Ricerca del piano, fase 2).</li><li><b>Quali mosse?</b> Mosse candidate che servono il piano, poi la scelta, verificando che nessuna sia un errore grave (Mosse candidate, Scelta della mossa).</li></ol>'),
    ('Perché esercizi separati e non una posizione dall\'inizio alla fine?', 'Ogni passo ha subito la sua correzione. Su una sola posizione, la correzione di un passo svelerebbe il successivo, e una catena lunga rende lento ogni giro. La routine quotidiana percorre i passi in ordine, ciascuno sulla sua posizione.'),
    ("E il piano dell'avversario?", 'Verificare scacchi, catture e minacce dell\'avversario (passo 1) è la prima parte della profilassi. La domanda completa, «cosa vuole il mio avversario?», potrà diventare un esercizio a sé più avanti.'),
  ]),
  ('Punteggi e progressi', [
    ("Cos'è la mia media?", 'La tua precisione in un esercizio, livellata sulle posizioni recenti: all\'inizio una media semplice, poi ogni nuova posizione la sposta del 15% verso il suo punteggio. Una posizione andata male costa poco; una serie di buone la alza con costanza.'),
    ("Cos'è la routine quotidiana?", 'Tre posizioni di ogni esercizio al giorno, in quante sessioni vuoi, nell\'ordine del ragionamento.'),
    ('Cosa sono le posizioni sbagliate?', 'Le posizioni in cui hai fatto meno della tua media di allora. Ripeti le rigioca; raggiungere almeno la tua media ne toglie una dall\'elenco. Una posizione giocata oggi aspetta fino a domani.'),
    ('Dove sono conservati i miei progressi?', 'Nel tuo browser, e nel tuo account quando hai effettuato l\'accesso, così ti seguono su tutti i dispositivi.'),
  ]),
  ('Le posizioni e il motore', [
    ('Da dove vengono le posizioni?', 'Da partite del Campionato del mondo e, una volta collegato, dalle tue partite su Lichess e Chess.com. Nelle tue partite l\'app cerca prima i tuoi errori, poi altre posizioni, come nelle partite di maestri.'),
    ('Come vengono scelte le posizioni?', 'Con delle regole, verificate con Stockfish: posizioni tranquille in cui la strategia conta, distribuite lungo la partita, non troppo vicine tra loro, e per ogni esercizio un motivo per porre la domanda. Le partite patte danno solo le loro posizioni squilibrate.'),
    ('Quale motore?', 'Stockfish 19 (la sua versione «lite»), che gira nel tuo browser, quindi nulla viene inviato altrove: ogni posizione è analizzata fino alla profondità 20, in pochi secondi al massimo. Le posizioni dei maestri arrivano anche con la loro valutazione calcolata in anticipo.'),
  ]),
  ('Crediti e letture', [
    ('Da dove vengono i suoni?', 'I suoni di mossa e di cattura sono due suoni tagliati da <a href="https://freesound.org/s/792572/">«chess piece» di imrius</a> (freesound.org), con licenza <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Modifiche: taglio, rumore di fondo ridotto, volume uniformato.'),
    ("Quali libri ci sono dietro l'app?", '<ul><li><b>Jeremy Silman, <i>How to Reassess Your Chess</i>:</b> gli squilibri, e come portano a un piano.</li><li><b>Aron Nimzowitsch, <i>Il mio sistema</i>:</b> colonne aperte, avamposti, catene di pedoni, blocco, profilassi.</li><li><b>José Raúl Capablanca, <i>Fondamenti degli scacchi</i>:</b> le basi di ogni fase.</li><li><b>Aleksandr Kotov, <i>Pensa come un grande maestro</i>:</b> le mosse candidate e l\'ordine del ragionamento.</li><li><b>Mark Dvoretsky e Artur Jusupov, <i>Positional Play</i>:</b> il pensiero profilattico.</li><li><b>Jacob Aagaard, <i>Grandmaster Preparation: Positional Play</i>:</b> tre domande per ogni posizione tranquilla.</li><li><b>Michail Shereshevsky, <i>Endgame Strategy</i>:</b> il re, le due debolezze, e non avere fretta.</li></ul>'),
  ]),
],
}

W_MORE = {
  'de': dict(faq='Häufige Fragen', exercises='Übungen',
    intro='Taktikaufgaben haben immer genau eine richtige Antwort. Echte Partien nicht. ChessStrategy.org trainiert, was vor dem Zug kommt: die Stellung lesen, einen Plan wählen, gute Züge finden und den besten auswählen.',
    faq_desc='Wie ChessStrategy.org funktioniert: seine vier Schachstrategie-Übungen (Ungleichgewichte, Pläne, Kandidatenzüge, Zugwahl), Wertungen, Stellungen und die Engine.'),
  'es': dict(faq='Preguntas frecuentes', exercises='Ejercicios',
    intro='Los problemas de táctica siempre tienen una única respuesta correcta. Las partidas reales, no. ChessStrategy.org entrena lo que viene antes de la jugada: leer la posición, elegir un plan, encontrar buenas jugadas y escoger la mejor.',
    faq_desc='Cómo funciona ChessStrategy.org: sus cuatro ejercicios de estrategia de ajedrez (desequilibrios, planes, jugadas candidatas, elección de jugada), puntuaciones, posiciones y el motor.'),
  'it': dict(faq='Domande frequenti', exercises='Esercizi',
    intro='I problemi di tattica hanno sempre una sola risposta giusta. Le partite vere no. ChessStrategy.org allena ciò che viene prima della mossa: leggere la posizione, scegliere un piano, trovare buone mosse e sceglierne la migliore.',
    faq_desc='Come funziona ChessStrategy.org: i suoi quattro esercizi di strategia scacchistica (squilibri, piani, mosse candidate, scelta della mossa), punteggi, posizioni e il motore.'),
}

LEGAL_MORE = [
  ('de', 'Datenschutz', 'Was ChessStrategy.org über dich speichert, wo, und wie du es löschst.', "Nutzungsbedingungen", 'Die Nutzungsbedingungen von ChessStrategy.org, kostenloses Open-Source-Schachstrategie-Training.'),
  ('es', 'Privacidad', 'Qué guarda ChessStrategy.org sobre ti, dónde, y cómo borrarlo.', 'Condiciones de uso', 'Las condiciones de uso de ChessStrategy.org, entrenamiento de estrategia de ajedrez gratuito y de código abierto.'),
  ('it', 'Privacy', 'Cosa conserva ChessStrategy.org su di te, dove, e come cancellarlo.', "Termini d'uso", "I termini d'uso di ChessStrategy.org, allenamento di strategia scacchistica gratuito e open source."),
]
