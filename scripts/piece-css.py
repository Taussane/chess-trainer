#!/usr/bin/env python3
# Writes the board's piece images (the Caliente set, vendor/pieces/caliente/) into app/index.html, as
# base64 data URIs between /*PIECE_CSS*/ and /*END PIECE_CSS*/. Run after changing the SVGs.
import base64, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app/index.html'
rules = []
for c in 'wb':
    for t in 'KQRBNP':
        svg = (ROOT / f'vendor/pieces/caliente/{c}{t}.svg').read_bytes()
        txt = svg.decode()
        assert "'" not in txt
        # URL-encoded rather than base64: a third smaller, and it compresses better
        enc = txt.replace('"', "'").replace('%', '%25').replace('#', '%23').replace('<', '%3C').replace('>', '%3E').replace('{', '%7B').replace('}', '%7D')
        rules.append(f'.pc-{c}{t}{{background-image:url("data:image/svg+xml,{enc}")}}')
css = '\n  '.join(rules)
src = APP.read_text()
src = re.sub(r'/\*PIECE_CSS\*/.*?/\*END PIECE_CSS\*/', lambda m: '/*PIECE_CSS*/\n  ' + css + '\n  /*END PIECE_CSS*/', src, flags=re.S)
APP.write_text(src)
print('piece css:', len(css), 'bytes')
