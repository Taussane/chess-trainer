// The account server (Cloudflare Worker + D1). See docs/accounts.md.
//
// Every request signs in with the player's own Lichess token (Authorization: Bearer …), checked
// with Lichess itself (/api/account) and then remembered for a day by its SHA-256 (the token is
// never stored). The Lichess player is a *connection* of one of our accounts; the first sign-in
// creates the account. Each request then reads or writes that account's rows only.
//
//   GET    /api/me                      account, its connections
//   GET    /api/results?after=&limit=   results after a time, oldest first (at most 1000)
//   POST   /api/results   {rows:[…]}    add results (a row already there is ignored)
//   GET    /api/games                   all games
//   POST   /api/games     {games:[…]}   add or replace games
//   DELETE /api/games/:id               remove one game
//   GET    /api/meta/:name              a small document (profile, games-cleared, …)
//   PUT    /api/meta/:name              replace it
//   DELETE /api/session                 forget this sign-in here (log out)
//   DELETE /api/account                 delete the account and everything in it

const SITES = {
  // How each site's sign-in is checked: its token -> { id, username } of the player.
  lichess: async token => {
    const r = await fetch('https://lichess.org/api/account', { headers: { Authorization: 'Bearer ' + token } });
    if (!r.ok) return null;
    const a = await r.json();
    return a && a.id && a.username ? { id: String(a.id), username: String(a.username) } : null;
  },
};
const DAY = 864e5, MAX_ROWS = 500, MAX_GAME_BYTES = 200000;

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
  const site = req.headers.get('X-Auth-Site') || 'lichess';
  const token = ((req.headers.get('Authorization') || '').match(/^Bearer (\S+)$/) || [])[1];
  if (!token || !SITES[site]) throw fail(401, 'sign in first');
  const tokenHash = await sha256(site + ':' + token);
  if (m === 'DELETE' && path === '/api/session') {
    await env.DB.prepare('DELETE FROM sessions WHERE token_hash = ?').bind(tokenHash).run();
    return json({ ok: true });
  }
  const account = await signIn(env, site, token, tokenHash);
  if (!account) throw fail(401, 'sign-in not accepted');
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
    for (const g of games) {
      if (!g || typeof g.id !== 'string' || !g.id || !Array.isArray(g.sans)) continue;
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

async function body(req) {
  const t = await req.text();
  if (t.length > 2e6) throw fail(413, 'too large');
  try { return JSON.parse(t || '{}') || {}; } catch (e) { throw fail(400, 'not JSON'); }
}
async function sha256(s) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
}
