#!/usr/bin/env python3
# Writes app/sf-eval.js (the JavaScript port of Stockfish 10's evaluation) into app/index.html,
# between /*SF_EVAL*/ and /*END SF_EVAL*/, so the app stays a single file. Run after changing it.
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / 'app/index.html'
js = (ROOT / 'app/sf-eval.js').read_text()
src = APP.read_text()
if '/*SF_EVAL*/' not in src:
    src = src.replace('<script src="https://cdn.jsdelivr.net/npm/chess.js@0.12.1/chess.js"></script>\n',
                      '<script src="https://cdn.jsdelivr.net/npm/chess.js@0.12.1/chess.js"></script>\n<script>/*SF_EVAL*/\n/*END SF_EVAL*/</script>\n', 1)
src = re.sub(r'/\*SF_EVAL\*/.*?/\*END SF_EVAL\*/', lambda m: '/*SF_EVAL*/\n' + js + '/*END SF_EVAL*/', src, flags=re.S)
APP.write_text(src)
print('sf-eval:', len(js), 'bytes')
