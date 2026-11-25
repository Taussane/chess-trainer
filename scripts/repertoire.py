#!/usr/bin/env python3
"""Opening repertoire (beta): merges the Lichess studies in library/repertoire/ into one tree per colour.

Writes:
  data/repertoire-study.pgn : two chapters (White, Black) to import into one Lichess study
  app/index.html            : the /*REPERTOIRE*/ graph used by the Repertoire screen

Rules (objective, so a new study merges the same way):
  - chapters starting from a FEN are grafted where the merged tree first reaches that position;
  - the same move from the same node is merged: comments joined (no duplicates), arrows and squares deduplicated;
  - at a position where it's your move, the main line (first variation) is your move; your other moves are
    sidelines ("not your line", their comment shown when played);
  - DROP: lines removed by decision (see below).
Graph: positions keyed by placement, side and castling (no en passant square, no clocks), so transpositions meet.
"""
import chess, chess.pgn, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS = {'w': ['scotch-game', 'alternatives-after-e4'], 'b': ['caro-kann', 'slav-defense']}
DROP = {'w': ['d4'], 'b': ['d4 d5']}   # decided: 1.d4 was an explanation line (White); 1.d4 c6 covers the Slav (Black)

def key(b): return ' '.join(b.fen().split()[:3])
def load(name):
    out = []
    with open(os.path.join(ROOT, 'library/repertoire', name + '.pgn')) as fh:
        while (g := chess.pgn.read_game(fh)): out.append(g)
    return out
def text(c): return re.sub(r'\s+', ' ', re.sub(r'\[%[^\]]*\]', '', c)).strip()
def merge_into(dst, src):
    arrows = {}
    for a in getattr(dst, '_rep_arrows', dst.arrows()) + src.arrows(): arrows.setdefault((a.tail, a.head, a.color), a)   # (read before the comments lose their annotations)
    arrows = list(arrows.values())
    for attr in ('comment', 'starting_comment'):
        a, b = text(getattr(dst, attr)), text(getattr(src, attr))
        if b and b not in a: a = (a + ' ' + b).strip()
        setattr(dst, attr, a)
    dst._rep_arrows = arrows
def graft(dst, src, chapter):
    for v in src.variations:
        ex = next((d for d in dst.variations if d.move == v.move), None)
        if ex is None: ex = dst.add_variation(v.move); ex._rep_ch = chapter
        merge_into(ex, v); graft(ex, v, chapter)
def find(node, k):
    q = [node]
    while q:
        n = q.pop(0)
        if key(n.board()) == k: return n
        q += n.variations
def walk(n):
    yield n
    for v in n.variations: yield from walk(v)

def build(colour):
    root = chess.pgn.Game(); root._rep_arrows = []
    for name in SETS[colour]:
        for ch in load(name):
            label = f"{ch.headers.get('StudyName')}: {ch.headers.get('ChapterName')}"
            at = find(root, key(ch.board())) if 'FEN' in ch.headers else root
            assert at is not None, label
            merge_into(at, ch); graft(at, ch, label)
    for line in DROP[colour]:   # a dropped line's comments go to the same position reached another way
        n = root
        for san in line.split(): n = next(v for v in n.variations if n.board().san(v.move) == san)
        kept = {key(x.board()): x for x in walk(root) if not any(x is y for y in walk(n))}
        for x in walk(n):
            same = kept.get(key(x.board()))
            if same is not None and x.comment: merge_into(same, x)
        n.parent.variations.remove(n)
    for n in walk(root): n.set_arrows(getattr(n, '_rep_arrows', n.arrows()))
    return root

def graph(root, colour):
    me = chess.WHITE if colour == 'w' else chess.BLACK
    nodes, comments, names = {}, [], []
    def cid(c):
        if not c: return -1
        if c not in comments: comments.append(c)
        return comments.index(c)
    for n in walk(root):
        b = n.board(); k = key(b); lst = nodes.setdefault(k, [])
        for i, v in enumerate(n.variations):
            san = b.san(v.move)
            flag = (1 if i == 0 else 2) if b.turn == me else 0
            ch = getattr(v, '_rep_ch', '')
            if ch not in names: names.append(ch)
            old = next((m for m in lst if m[0] == san), None)
            if old:
                if flag == 1: old[1] = 1   # (your main move somewhere wins over a sideline elsewhere)
                continue
            lst.append([san, flag, cid(text(v.comment)), names.index(ch)])
    for k, lst in nodes.items():   # your move at a transposition reached from two chapters: one main move only
        mains = [m for m in lst if m[1] == 1]
        for m in mains[1:]: m[1] = 2
    return { 'n': {k: v for k, v in nodes.items() if v}, 'c': comments, 'ch': names }

def main():
    out, data = [], {}
    for colour, title in (('w', 'White'), ('b', 'Black')):
        root = build(colour)
        root.headers.clear(); root.headers['Event'] = f'Repertoire: {title}'
        root.headers['ChapterName'] = title; root.headers['Orientation'] = 'white' if colour == 'w' else 'black'
        out.append(str(root)); data[colour] = graph(root, colour)
    with open(os.path.join(ROOT, 'data/repertoire-study.pgn'), 'w') as f: f.write('\n\n\n'.join(out) + '\n')
    app = os.path.join(ROOT, 'app/index.html'); s = open(app).read()
    js = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    s2, k = re.subn(r'/\*REPERTOIRE\*/\{.*?\};\n', lambda m: '/*REPERTOIRE*/' + js + ';\n', s, count=1, flags=re.S)
    assert k == 1, 'no /*REPERTOIRE*/ marker in app/index.html'
    open(app, 'w').write(s2)
    print('positions:', {c: len(d['n']) for c, d in data.items()}, 'comments:', {c: len(d['c']) for c, d in data.items()})

if __name__ == '__main__': main()
