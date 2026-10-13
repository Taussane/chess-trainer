#!/usr/bin/env python3
# Writes the board's piece images (Cburnett set, vendor/pieces/cburnett/) into app/index.html, as
# base64 data URIs between /*PIECE_CSS*/ and /*END PIECE_CSS*/. Run after changing the SVGs.
import base64, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app/index.html'
rules = []
for c in 'wb':
    for t in 'KQRBNP':
        svg = (ROOT / f'vendor/pieces/cburnett/{c}{t}.svg').read_bytes()
        key = t if c == 'w' else t.lower()
        rules.append(f'.pc-{c}{t}{{background-image:url("data:image/svg+xml;base64,{base64.b64encode(svg).decode()}")}}')
css = '\n  '.join(rules)
src = APP.read_text()
src = re.sub(r'/\*PIECE_CSS\*/.*?/\*END PIECE_CSS\*/', lambda m: '/*PIECE_CSS*/\n  ' + css + '\n  /*END PIECE_CSS*/', src, flags=re.S)
APP.write_text(src)
print('piece css:', len(css), 'bytes')
