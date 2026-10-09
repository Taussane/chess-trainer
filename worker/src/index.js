// The account server (Cloudflare Worker + D1). See docs/accounts.md.
//
// Two ways to sign in, both ending in a Bearer token on every request (the token is never stored,
// only its SHA-256):
//  - Lichess (X-Auth-Site: lichess): the player's own Lichess token, checked with Lichess itself
//    (/api/account), then remembered for a day.
//  - Google (X-Auth-Site: app): POST /api/login/google with the ID token Google gave the page; it is
//    checked here (Google's signature, this site's client id, not expired, email verified), and the
//    page gets a token of ours, valid until logging out (or 180 days unused).
// The player is a *connection* (lichess, google) of one of our accounts; the first sign-in creates
// the account. Each request then reads or writes that account's rows only.
//
//   POST   /api/login/google {idToken}  sign in with Google -> {token, email}
//   POST   /api/link/google  {idToken}  add a Google login to this account (not offered in the app:
//                                       Lichess is the main login, Google links Lichess instead)
//   POST   /api/link/lichess {token}    add a Lichess login to this account
//                                       (if that login already has an account, the two are merged
//                                       into this one: progress, games and settings together)
//   GET    /api/me                      account, its connections
//   GET    /api/results?after=&limit=   results after a time, oldest first (at most 1000)
//   POST   /api/results   {rows:[…]}    add results (a row already there is ignored)
//   GET    /api/games                   all games
//   POST   /api/games     {games:[…]}   add or replace games
//   DELETE /api/games/:id               remove one game
//   GET    /api/meta/:name              a small document (profile, games-cleared, …)
//   PUT    /api/meta/:name              replace it
//   GET    /api/chesscom/player?user=   a Chess.com player's name as Chess.com spells it (404: none)
//   GET    /api/chesscom/games?user=&since=&max=
//                                       their newest games played after `since` (ms), as PGN text:
//                                       live games only (no daily, no variants), newest first
//   DELETE /api/session                 forget this sign-in here (log out)
//   DELETE /api/account                 delete the account and everything in it

const SITES = {
  // How each site's sign-in is checked: its token -> { id, username } of the player.
  lichess: async token => {
    const r = await fetch('https://lichess.org/api/account', { headers: { Authorization: 'Bearer ' + token, Accept: 'application/json',
      'User-Agent': 'chess-trainer-api (https://github.com/Taussane/chess-trainer)' } });
    if (r.status === 429) throw fail(503, 'Lichess is busy (too many requests); try again in a minute');
    if (r.status >= 500) throw fail(503, 'Lichess did not answer (' + r.status + ')');
    if (!r.ok) return null;
    const a = await r.json();
    return a && a.id && a.username ? { id: String(a.id), username: String(a.username) } : null;
  },
};
const DAY = 864e5, APP_SESSION_DAYS = 180, MAX_ROWS = 500, MAX_GAME_BYTES = 200000;
const UA = { 'User-Agent': 'chess-trainer-api (https://github.com/Taussane/chess-trainer)' };

export default {
  async fetch(req, env) {
    const cors = corsHeaders(req, env);
    if (req.method === 'OPTIONS') return new Response(null, { status: cors ? 204 : 403, headers: cors || {} });
    try {
      const res = await route(req, env);
      if (cors) for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
      return res;
    } catch (e) {
      const res = json({ error: e.status ? e.message : 'server error' }, e.status || 500);
      if (cors) for (const [k, v] of Object.entries(cors)) res.headers.set(k, v);
      return res;
    }
  },
};

function corsHeaders(req, env) {
  const origin = req.headers.get('Origin');
  const allowed = String(env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!origin || !allowed.includes(origin)) return null;
  return {
    'Access-Control-Allow-Origin': origin, Vary: 'Origin',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type, X-Auth-Site',
    'Access-Control-Max-Age': '86400',
  };
}
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const fail = (status, message) => Object.assign(new Error(message), { status });

async function route(req, env) {
  const url = new URL(req.url), path = url.pathname.replace(/\/+$/, ''), m = req.method;
  if (path === '/api/health') return json({ ok: true });
  if (m === 'POST' && path === '/api/login/google') return googleLogin(env, (await body(req)).idToken);
  const site = req.headers.get('X-Auth-Site') || 'lichess';
  const token = ((req.headers.get('Authorization') || '').match(/^Bearer (\S+)$/) || [])[1];
  if (!token || !(SITES[site] || site === 'app')) throw fail(401, 'sign in first');
  const tokenHash = await sha256(site + ':' + token);
  if (m === 'DELETE' && path === '/api/session') {
    await env.DB.prepare('DELETE FROM sessions WHERE token_hash = ?').bind(tokenHash).run();
    return json({ ok: true });
  }
  const account = await signIn(env, site, token, tokenHash);
  if (!account) throw fail(401, site === 'app' ? 'your login has expired; log in again' : 'Lichess did not accept this login');
  const DB = env.DB;

  if (m === 'GET' && path === '/api/me') {
    const a = await DB.prepare('SELECT id, created_at FROM accounts WHERE id = ?').bind(account).first();
    const { results: cs } = await DB.prepare('SELECT site, username, verified FROM connections WHERE account_id = ? ORDER BY added_at').bind(account).all();
    return json({ account: { id: a.id, createdAt: a.created_at }, connections: cs.map(c => ({ site: c.site, username: c.username, verified: !!c.verified })) });
  }
  if (m === 'GET' && path === '/api/results') {
    const after = Number(url.searchParams.get('after') || -1), limit = Math.max(1, Math.min(1000, Number(url.searchParams.get('limit') || 1000)));
    const { results: rows } = await DB.prepare('SELECT data FROM results WHERE account_id = ? AND ts > ? ORDER BY ts LIMIT ?').bind(account, after, limit).all();
    return json({ rows: rows.map(r => JSON.parse(r.data)) });
  }
  if (m === 'POST' && path === '/api/results') {
    const rows = (await body(req)).rows;
    if (!Array.isArray(rows) || rows.length > MAX_ROWS) throw fail(400, 'rows: a list of at most ' + MAX_ROWS);
    const ok = rows.filter(r => r && Number.isFinite(r.ts) && typeof r.a === 'string' && typeof r.acc === 'number');
    if (ok.length) await DB.batch(ok.map(r => DB.prepare('INSERT OR IGNORE INTO results (account_id, ts, a, data) VALUES (?, ?, ?, ?)').bind(account, r.ts, r.a, JSON.stringify(r))));
    return json({ added: ok.length });
  }
  if (m === 'GET' && path === '/api/games') {
    const { results: rows } = await DB.prepare('SELECT data FROM games WHERE account_id = ? ORDER BY updated_at').bind(account).all();
    return json({ games: rows.map(r => JSON.parse(r.data)) });
  }
  if (m === 'POST' && path === '/api/games') {
    const games = (await body(req)).games;
    if (!Array.isArray(games) || games.length > MAX_ROWS) throw fail(400, 'games: a list of at most ' + MAX_ROWS);
    const now = Date.now(), stmts = [];
    // Chess.com games only while a Chess.com username is connected (so a device that hasn't heard of
    // a disconnect yet can't bring them back).
    const cc = await DB.prepare("SELECT data FROM meta WHERE account_id = ? AND name = 'chesscom'").bind(account).first();
    let ccOn = false; try { ccOn = !!(cc && JSON.parse(cc.data).username); } catch (e) {}
    for (const g of games) {
      if (!g || typeof g.id !== 'string' || !g.id || !Array.isArray(g.sans)) continue;
      if (!ccOn && (g.site === 'chesscom' || g.id.startsWith('cc-'))) continue;
      const { positions, ...keep } = g;   // positions are worked out again by the app
      const data = JSON.stringify(keep);
      if (data.length > MAX_GAME_BYTES) continue;
      stmts.push(DB.prepare('INSERT INTO games (account_id, id, site, data, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT (account_id, id) DO UPDATE SET data = excluded.data, site = excluded.site, updated_at = excluded.updated_at')
        .bind(account, g.id, typeof g.site === 'string' ? g.site : 'lichess', data, now));
    }
    if (stmts.length) await DB.batch(stmts);
    return json({ saved: stmts.length });
  }
  let mm;
  if (m === 'DELETE' && (mm = path.match(/^\/api\/games\/([^/]+)$/))) {
    await DB.prepare('DELETE FROM games WHERE account_id = ? AND id = ?').bind(account, decodeURIComponent(mm[1])).run();
    return json({ ok: true });
  }
  if ((mm = path.match(/^\/api\/meta\/([a-z0-9-]{1,40})$/))) {
    if (m === 'GET') {
      const r = await DB.prepare('SELECT data FROM meta WHERE account_id = ? AND name = ?').bind(account, mm[1]).first();
      return json({ exists: !!r, data: r ? JSON.parse(r.data) : null });
    }
    if (m === 'PUT') {
      const data = JSON.stringify((await body(req)).data ?? null);
      if (data.length > 20000) throw fail(400, 'too large');
      await DB.prepare('INSERT INTO meta (account_id, name, data) VALUES (?, ?, ?) ON CONFLICT (account_id, name) DO UPDATE SET data = excluded.data').bind(account, mm[1], data).run();
      return json({ ok: true });
    }
  }
  if (m === 'GET' && path === '/api/chesscom/player') {
    const user = ccUser(url);
    const p = await (await ccFetch('https://api.chess.com/pub/player/' + user)).json();
    // Chess.com gives "username" in lowercase; the name as the player spells it is in their page's address.
    const spelled = (String(p.url || '').match(/\/member\/([^/?#]+)/) || [])[1];
    return json({ username: spelled && spelled.toLowerCase() === String(p.username || user).toLowerCase() ? decodeURIComponent(spelled) : (p.username || user) });
  }
  if (m === 'GET' && path === '/api/chesscom/games') {
    return new Response(await ccGames(ccUser(url), Number(url.searchParams.get('since') || 0), Math.max(1, Math.min(200, Number(url.searchParams.get('max') || 100)))),
      { headers: { 'Content-Type': 'application/x-chess-pgn' } });
  }
  if (m === 'POST' && (path === '/api/link/google' || path === '/api/link/lichess')) {
    const b = await body(req), google = path.endsWith('google');
    const player = google ? await verifyGoogle(env, b.idToken) : await SITES.lichess(String(b.token || ''));
    if (!player) throw fail(401, (google ? 'Google' : 'Lichess') + ' did not accept this login');
    const linkSite = google ? 'google' : 'lichess', now = Date.now();
    const c = await DB.prepare('SELECT account_id FROM connections WHERE site = ? AND site_user_id = ?').bind(linkSite, player.id).first();
    const stmts = [];
    if (c && c.account_id !== account) stmts.push(...await mergeInto(DB, c.account_id, account));
    if (c) stmts.push(DB.prepare('UPDATE connections SET account_id = ?, username = ?, verified = 1 WHERE site = ? AND site_user_id = ?').bind(account, player.username, linkSite, player.id));
    else stmts.push(DB.prepare('INSERT INTO connections (site, site_user_id, account_id, username, verified, added_at) VALUES (?, ?, ?, ?, 1, ?)').bind(linkSite, player.id, account, player.username, now));
    if (!google) stmts.push(DB.prepare('INSERT INTO sessions (token_hash, account_id, site, checked_at) VALUES (?, ?, ?, ?) ON CONFLICT (token_hash) DO UPDATE SET account_id = excluded.account_id, checked_at = excluded.checked_at')
      .bind(await sha256('lichess:' + b.token), account, 'lichess', now));
    await DB.batch(stmts);
    return json({ ok: true, merged: !!(c && c.account_id !== account) });
  }
  if (m === 'DELETE' && path === '/api/account') {
    await DB.batch(['results', 'games', 'meta', 'sessions', 'connections'].map(t => DB.prepare(`DELETE FROM ${t} WHERE account_id = ?`).bind(account))
      .concat([DB.prepare('DELETE FROM accounts WHERE id = ?').bind(account)]));
    return json({ ok: true });
  }
  throw fail(404, 'not found');
}

// The account for this token: remembered sign-in (checked within a day), else asked to the site;
// a player seen for the first time gets a new account.
async function signIn(env, site, token, tokenHash) {
  const DB = env.DB, now = Date.now();
  const s = await DB.prepare('SELECT account_id, checked_at FROM sessions WHERE token_hash = ?').bind(tokenHash).first();
  if (site === 'app') {   // our own token (Google sign-in): valid while used at least every 180 days
    if (!s) return null;
    if (now - s.checked_at > APP_SESSION_DAYS * DAY) { await DB.prepare('DELETE FROM sessions WHERE token_hash = ?').bind(tokenHash).run(); return null; }
    if (now - s.checked_at > DAY) await DB.prepare('UPDATE sessions SET checked_at = ? WHERE token_hash = ?').bind(now, tokenHash).run();
    return s.account_id;
  }
  if (s && now - s.checked_at < DAY) return s.account_id;
  const player = await SITES[site](token);
  if (!player) { if (s) await DB.prepare('DELETE FROM sessions WHERE token_hash = ?').bind(tokenHash).run(); return null; }
  const c = await DB.prepare('SELECT account_id FROM connections WHERE site = ? AND site_user_id = ?').bind(site, player.id).first();
  let account = c && c.account_id;
  const stmts = [];
  if (!account) {
    account = crypto.randomUUID();
    stmts.push(DB.prepare('INSERT INTO accounts (id, created_at) VALUES (?, ?)').bind(account, now));
    stmts.push(DB.prepare('INSERT INTO connections (site, site_user_id, account_id, username, verified, added_at) VALUES (?, ?, ?, ?, 1, ?)').bind(site, player.id, account, player.username, now));
  } else {
    stmts.push(DB.prepare('UPDATE connections SET username = ?, verified = 1 WHERE site = ? AND site_user_id = ?').bind(player.username, site, player.id));
  }
  stmts.push(DB.prepare('INSERT INTO sessions (token_hash, account_id, site, checked_at) VALUES (?, ?, ?, ?) ON CONFLICT (token_hash) DO UPDATE SET account_id = excluded.account_id, checked_at = excluded.checked_at').bind(tokenHash, account, site, now));
  await DB.batch(stmts);
  return account;
}

// Another account joins this one: its results and games are added (where this account has the same
// one, this account's is kept), its settings fill in what this account doesn't have ("training
// since": the earlier of the two; older saves' missed-position lists: both), its logins now open this account; then it is deleted.
async function mergeInto(DB, from, to) {
  const prof = async id => { const r = await DB.prepare("SELECT data FROM meta WHERE account_id = ? AND name = 'profile'").bind(id).first(); try { return r ? JSON.parse(r.data) || {} : null; } catch (e) { return null; } };
  const [pf, pt] = await Promise.all([prof(from), prof(to)]);
  const early = [pf && pf.joinedAt, pt && pt.joinedAt].filter(x => Number.isFinite(x));
  const joined = pt && pf && early.length ? [DB.prepare("UPDATE meta SET data = ? WHERE account_id = ? AND name = 'profile'").bind(JSON.stringify({ ...pt, joinedAt: Math.min(...early) }), to)] : [];
  // Older saves kept missed positions in a "replay" document: both lists, together.
  const rep = async id => { const r = await DB.prepare("SELECT data FROM meta WHERE account_id = ? AND name = 'replay'").bind(id).first(); try { return r ? JSON.parse(r.data) : null; } catch (e) { return null; } };
  const [rf, rt] = await Promise.all([rep(from), rep(to)]);
  if (rf && rt && Array.isArray(rf.items) && Array.isArray(rt.items)) {
    const items = rt.items.concat(rf.items.filter(x => !rt.items.some(y => y.key === x.key && y.a === x.a)));
    joined.push(DB.prepare("UPDATE meta SET data = ? WHERE account_id = ? AND name = 'replay'").bind(JSON.stringify({ ...rt, items }), to));
  }
  return [
    ...joined,
    DB.prepare('INSERT OR IGNORE INTO results (account_id, ts, a, data) SELECT ?, ts, a, data FROM results WHERE account_id = ?').bind(to, from),
    DB.prepare('INSERT OR IGNORE INTO games (account_id, id, site, data, updated_at) SELECT ?, id, site, data, updated_at FROM games WHERE account_id = ?').bind(to, from),
    DB.prepare('INSERT OR IGNORE INTO meta (account_id, name, data) SELECT ?, name, data FROM meta WHERE account_id = ?').bind(to, from),
    DB.prepare('UPDATE connections SET account_id = ? WHERE account_id = ?').bind(to, from),
    DB.prepare('UPDATE sessions SET account_id = ? WHERE account_id = ?').bind(to, from),
    ...['results', 'games', 'meta'].map(t => DB.prepare(`DELETE FROM ${t} WHERE account_id = ?`).bind(from)),
    DB.prepare('DELETE FROM accounts WHERE id = ?').bind(from),
  ];
}

// ---- Google sign-in ----
// The ID token is a JWT signed by Google (RS256); its keys are published at GOOGLE_CERTS.
const GOOGLE_CERTS = 'https://www.googleapis.com/oauth2/v3/certs';
let googleKeys = { at: 0, keys: [] };
const unb64 = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), c => c.charCodeAt(0));
async function googleKey(kid) {
  for (let fresh = 0; fresh < 2; fresh++) {
    if (fresh || Date.now() - googleKeys.at > 36e5) {
      const r = await fetch(GOOGLE_CERTS);
      if (!r.ok) throw fail(503, 'Google did not answer (' + r.status + ')');
      googleKeys = { at: Date.now(), keys: (await r.json()).keys || [] };
    }
    const k = googleKeys.keys.find(x => x.kid === kid);
    if (k) return crypto.subtle.importKey('jwk', k, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  }
  return null;
}
async function verifyGoogle(env, idToken) {
  const parts = String(idToken || '').split('.');
  if (parts.length !== 3 || !env.GOOGLE_CLIENT_ID) return null;
  let head, claims;
  try { head = JSON.parse(new TextDecoder().decode(unb64(parts[0]))); claims = JSON.parse(new TextDecoder().decode(unb64(parts[1]))); } catch (e) { return null; }
  if (head.alg !== 'RS256') return null;
  const key = await googleKey(head.kid);
  if (!key || !(await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, unb64(parts[2]), new TextEncoder().encode(parts[0] + '.' + parts[1])))) return null;
  const now = Date.now() / 1000;
  if (!['accounts.google.com', 'https://accounts.google.com'].includes(claims.iss) || claims.aud !== env.GOOGLE_CLIENT_ID) return null;
  if (!(claims.exp > now) || !claims.sub || !claims.email || claims.email_verified === false) return null;
  return { id: String(claims.sub), username: String(claims.email) };
}
async function googleLogin(env, idToken) {
  const player = await verifyGoogle(env, idToken);
  if (!player) throw fail(401, 'Google did not accept this login');
  const DB = env.DB, now = Date.now();
  const c = await DB.prepare('SELECT account_id FROM connections WHERE site = ? AND site_user_id = ?').bind('google', player.id).first();
  let account = c && c.account_id;
  const stmts = [];
  if (!account) {
    account = crypto.randomUUID();
    stmts.push(DB.prepare('INSERT INTO accounts (id, created_at) VALUES (?, ?)').bind(account, now));
    stmts.push(DB.prepare('INSERT INTO connections (site, site_user_id, account_id, username, verified, added_at) VALUES (?, ?, ?, ?, 1, ?)').bind('google', player.id, account, player.username, now));
  } else {
    stmts.push(DB.prepare('UPDATE connections SET username = ? WHERE site = ? AND site_user_id = ?').bind(player.username, 'google', player.id));
  }
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const token = btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  stmts.push(DB.prepare('INSERT INTO sessions (token_hash, account_id, site, checked_at) VALUES (?, ?, ?, ?)').bind(await sha256('app:' + token), account, 'app', now));
  await DB.batch(stmts);
  return json({ token, email: player.username });
}

// ---- Chess.com (its public API: no sign-in, read only; one request at a time, as it asks) ----
function ccUser(url) {
  const u = String(url.searchParams.get('user') || '').trim().toLowerCase();
  if (!/^[a-z0-9_-]{3,25}$/.test(u)) throw fail(400, 'not a Chess.com username');
  return u;
}
async function ccFetch(u) {
  const r = await fetch(u, { headers: UA });
  if (r.status === 404 || r.status === 410) throw fail(404, 'no Chess.com player by that name');
  if (r.status === 429) throw fail(503, 'Chess.com is busy; try again in a minute');
  if (!r.ok) throw fail(502, 'Chess.com did not answer (' + r.status + ')');
  return r;
}
function playedAt(pgn) {
  const h = k => (pgn.match(new RegExp('\\[' + k + ' "([^"]*)"\\]')) || [])[1] || '';
  const d = h('UTCDate').match(/^(\d{4})\.(\d{2})\.(\d{2})$/), t = h('UTCTime').match(/^(\d{2}):(\d{2}):(\d{2})$/) || [0, 12, 0, 0];
  return d ? Date.UTC(+d[1], d[2] - 1, +d[3], +t[1], +t[2], +t[3]) : 0;
}
const liveStandard = pgn => !/\[TimeControl "[^"]*\/[^"]*"\]/.test(pgn) && !/\[Variant "(?!Standard)/.test(pgn) && !/\[FEN "/.test(pgn);
async function ccGames(user, since, max) {
  const { archives = [] } = await (await ccFetch(`https://api.chess.com/pub/player/${user}/games/archives`)).json();
  const sinceMonth = since ? new Date(since).toISOString().slice(0, 7).replace('-', '/') : '';
  let games = [];
  for (const a of archives.slice().reverse().slice(0, 24)) {   // newest month first, two years at most
    const month = (a.match(/(\d{4}\/\d{2})$/) || [])[1] || '';
    if (sinceMonth && month < sinceMonth) break;
    const text = await (await ccFetch(a + '/pgn')).text();
    games.push(...text.split(/\n\s*\n(?=\[Event )/).map(g => g.trim()).filter(g => g.startsWith('[Event ') && liveStandard(g) && playedAt(g) > since));
    if (games.length >= max) break;
  }
  games.sort((x, y) => playedAt(y) - playedAt(x));
  return games.slice(0, max).join('\n\n') + (games.length ? '\n' : '');
}

async function body(req) {
  const t = await req.text();
  if (t.length > 2e6) throw fail(413, 'too large');
  try { return JSON.parse(t || '{}') || {}; } catch (e) { throw fail(400, 'not JSON'); }
}
async function sha256(s) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
}
