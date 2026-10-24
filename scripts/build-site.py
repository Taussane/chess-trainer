# Builds the website's page (index.html at the top of the repository, served by GitHub Pages)
# from the app (app/index.html, which is also what's published inside Claude): the same page,
# wrapped in a full HTML document with the phone settings a website needs.
# Usage: python3 scripts/build-site.py   (run after any change to the app; tests/website.py, in `npm run test:all`, checks it)
import pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
app = (root / 'app' / 'index.html').read_text(encoding='utf-8')
icon = "icons/icon.svg"   # the white king of the board, on the yellow accent (icons/: the app icons, the same)
# What the page may load and call (Content-Security-Policy): its own files; the account server, Lichess
# (logins, games), and the CDNs the engine falls back to; Ko-fi's cup image. Inline scripts and styles are
# the app itself. A safety net: even injected code couldn't send anything to another site.
import re
API = re.search(r"/\*API_BASE\*/'([^']+)'", app).group(1)   # the account server's address, as the app has it
CDNS = 'https://cdn.jsdelivr.net https://cdnjs.cloudflare.com'
CSP = '; '.join([
    "default-src 'self'",
    f"script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' {CDNS}",
    f"worker-src 'self' blob: {CDNS}",
    f"connect-src 'self' {API} https://lichess.org {CDNS}",
    "img-src 'self' data: blob: https://storage.ko-fi.com",
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self' data:",
    "object-src 'none'", "frame-src 'none'", "base-uri 'self'", "form-action 'self'",
])
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<meta name="theme-color" content="#12161B">\n'
        '<meta name="description" content="Chess strategy training on positions from master games and your own Lichess and Chess.com games.">\n'
        # link previews (Open Graph, X/Twitter): icons/og-image.png, 1200x630
        '<meta property="og:type" content="website">\n'
        '<meta property="og:title" content="ChessStrategy.org">\n'
        '<meta property="og:description" content="Free chess strategy training on positions from master games and your own Lichess and Chess.com games.">\n'
        '<meta property="og:url" content="https://chessstrategy.org/">\n'
        '<meta property="og:image" content="https://chessstrategy.org/icons/og-image.png">\n'
        '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<link rel="icon" type="image/svg+xml" href="{icon}">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">\n'
        '<link rel="manifest" href="manifest.webmanifest">\n'
        '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black">\n'
        '<meta name="apple-mobile-web-app-title" content="Chess Strategy">\n'
        # the installed app's offline helper (sw.js), on the website only (not the local test server, not inside Claude)
        "<script>if('serviceWorker' in navigator && /(github\\.io|chessstrategy\\.org)$/.test(location.hostname)) addEventListener('load', ()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));</script>\n"

        '<!-- Built from app/index.html by scripts/build-site.py: edit the app, not this file. -->\n'
        '</head>\n<body>\n' + app + '\n</body>\n</html>\n')
# chess.js from this site (vendor/, the same 0.12.1 file) rather than a CDN: no script from another site in the page.
CDN_CHESS = '<script src="https://cdn.jsdelivr.net/npm/chess.js@0.12.1/chess.js"></script>'
assert page.count(CDN_CHESS) == 1, 'chess.js script tag not found'
page = page.replace(CDN_CHESS, '<script src="vendor/chess.js/chess.js"></script>')
# The desktop preview (chessstrategy.org/preview/, not linked, not indexed): the same page with the desktop
# layout being worked on switched on (html.desk2), its files taken from the site's root.
preview = (page.replace('<html lang="en">', '<html lang="en" class="desk2">', 1)
               .replace('<meta charset="utf-8">\n', '<meta charset="utf-8">\n<base href="../">\n<meta name="robots" content="noindex">\n', 1))
assert preview.count('class="desk2"') == 1 and '<base href' in preview
outs = { root / 'index.html': page, root / 'preview' / 'index.html': preview }
if '--check' in sys.argv:
    ok = all(f.exists() and f.read_text(encoding='utf-8') == t for f, t in outs.items())
    print('index.html is up to date' if ok else 'index.html is out of date: run python3 scripts/build-site.py')
    sys.exit(0 if ok else 1)
for f, t in outs.items():
    f.parent.mkdir(exist_ok=True); f.write_text(t, encoding='utf-8')
print('index.html built,', len(page)//1024, 'KB (and preview/index.html)')
