#!/usr/bin/env python3
# Writes the board's piece images into app/index.html, as base64 data URIs between /*PIECE_CSS*/ and
# /*END PIECE_CSS*/: the Cburnett set (vendor/pieces/cburnett/, the default) and the Caliente set
# (vendor/pieces/caliente/, chosen in Settings: html.pcs-caliente; loaded as files, only then; the
# profile's king stays Cburnett's).
# Run after changing the SVGs.
import base64, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app/index.html'
rules = []
for c in 'wb':
    for t in 'KQRBNP':
        svg = (ROOT / f'vendor/pieces/cburnett/{c}{t}.svg').read_bytes()
        key = t if c == 'w' else t.lower()
        rules.append(f'.pc-{c}{t}{{background-image:url("data:image/svg+xml;base64,{base64.b64encode(svg).decode()}")}}')
for c in 'wb':
    for t in 'KQRBNP':
        assert (ROOT / f'vendor/pieces/caliente/{c}{t}.svg').exists()   # (files, fetched only once the set is chosen)
        rules.append(f'html.pcs-caliente :not(.acct-dot) > .pc-{c}{t}{{background-image:url("vendor/pieces/caliente/{c}{t}.svg")}}')
css = '\n  '.join(rules)
src = APP.read_text()
src = re.sub(r'/\*PIECE_CSS\*/.*?/\*END PIECE_CSS\*/', lambda m: '/*PIECE_CSS*/\n  ' + css + '\n  /*END PIECE_CSS*/', src, flags=re.S)
APP.write_text(src)
print('piece css:', len(css), 'bytes')
