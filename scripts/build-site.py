# Builds the website's page (index.html at the top of the repository, served by GitHub Pages)
# from the app (app/index.html, which is also what's published inside Claude): the same page,
# wrapped in a full HTML document with the phone settings a website needs.
# Usage: python3 scripts/build-site.py   (run after any change to the app; tests/website.py, in `npm run test:all`, checks it)
import pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
app = (root / 'app' / 'index.html').read_text(encoding='utf-8')
icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%E2%99%9E%3C/text%3E%3C/svg%3E"
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<meta name="theme-color" content="#12161B">\n'
        '<meta name="description" content="Chess strategy training on positions from master games and your own Lichess and Chess.com games.">\n'
        f'<link rel="icon" href="{icon}">\n'
        '<!-- Built from app/index.html by scripts/build-site.py: edit the app, not this file. -->\n'
        '</head>\n<body>\n' + app + '\n</body>\n</html>\n')
out = root / 'index.html'
if '--check' in sys.argv:
    ok = out.exists() and out.read_text(encoding='utf-8') == page
    print('index.html is up to date' if ok else 'index.html is out of date: run python3 scripts/build-site.py')
    sys.exit(0 if ok else 1)
out.write_text(page, encoding='utf-8')
print('index.html built,', len(page)//1024, 'KB')
