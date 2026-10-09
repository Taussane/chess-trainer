// Runs the account server here, without Cloudflare: D1 emulated on Node's built-in SQLite (the
// same SQL), Lichess replaced by a stand-in that knows a few tokens. Used by the tests.
//   import { makeEnv, serve } from './local.mjs'
//   node worker/test/local.mjs 8787      -> http://localhost:8787 (for the browser tests)
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import worker from '../src/index.js';

const here = path.dirname(fileURLToPath(import.meta.url));

// The subset of D1 the server uses: prepare().bind().first()/all()/run(), batch().
export function makeD1() {
  const db = new DatabaseSync(':memory:');
  const dir = path.join(here, '..', 'migrations');
  for (const f of readdirSync(dir).filter(f => f.endsWith('.sql')).sort()) db.exec(readFileSync(path.join(dir, f), 'utf8'));
  const stmt = (sql, args = []) => ({
    bind: (...a) => stmt(sql, a),
    first: async () => db.prepare(sql).get(...args) ?? null,
    all: async () => ({ results: db.prepare(sql).all(...args) }),
    run: async () => { db.prepare(sql).run(...args); return { success: true }; },
    _run: () => db.prepare(sql).run(...args),
  });
  return {
    prepare: sql => stmt(sql),
    batch: async list => { db.exec('BEGIN'); try { list.forEach(s => s._run()); db.exec('COMMIT'); } catch (e) { db.exec('ROLLBACK'); throw e; } return list.map(() => ({ success: true })); },
    raw: db,
  };
}

// Stand-in Lichess: tokens -> players; counts how often it is asked.
export const LICHESS_PLAYERS = { 'tok-taussane': { id: 'taussane', username: 'Taussane' }, 'tok-other': { id: 'other', username: 'Other' } };
export const lichessCalls = { n: 0 };
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, opts = {}) => {
  if (String(url) === 'https://lichess.org/api/account') {
    lichessCalls.n++;
    const tok = ((opts.headers && (opts.headers.Authorization || opts.headers.authorization)) || '').replace('Bearer ', '');
    const p = LICHESS_PLAYERS[tok];
    return new Response(JSON.stringify(p || { error: 'No such token' }), { status: p ? 200 : 401, headers: { 'Content-Type': 'application/json' } });
  }
  const cc = String(url).match(/^https:\/\/api\.chess\.com\/pub\/player\/([^/]+)(\/games\/archives|\/games\/(\d{4})\/(\d{2})\/pgn)?$/);
  if (cc) {   // stand-in Chess.com: one player, "ccplayer", games from tests/chesscom-sample.pgn
    chesscomCalls.push(String(url));
    if (cc[1] !== 'ccplayer') return new Response('{"code":0}', { status: 404 });
    if (!cc[2]) return new Response(JSON.stringify({ username: 'ccplayer', url: 'https://www.chess.com/member/CCPlayer' }));   // as Chess.com: lowercase, capitals in the address
    if (cc[2] === '/games/archives') return new Response(JSON.stringify({ archives: ['09', '10'].map(m => 'https://api.chess.com/pub/player/ccplayer/games/2026/' + m) }));
    const games = CHESSCOM_SAMPLE.split(/\n\s*\n(?=\[Event )/).filter(g => g.includes(`[UTCDate "${cc[3]}.${cc[4]}.`));
    return new Response(games.join('\n\n'), { headers: { 'Content-Type': 'application/x-chess-pgn' } });
  }
  if (String(url) === 'https://www.googleapis.com/oauth2/v3/certs') { googleCalls.n++; return new Response(JSON.stringify({ keys: [GOOGLE_JWK] })); }
  return realFetch(url, opts);
};
// Stand-in Google: a key pair of our own; googleIdToken() signs ID tokens as Google would.
export const GOOGLE_CLIENT = 'test-client.apps.googleusercontent.com';
export const googleCalls = { n: 0 };
const googlePair = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
const GOOGLE_JWK = { ...(await crypto.subtle.exportKey('jwk', googlePair.publicKey)), kid: 'test-key', alg: 'RS256', use: 'sig' };
const b64u = b => Buffer.from(b).toString('base64url');
export async function googleIdToken(claims = {}) {
  const now = Math.floor(Date.now() / 1000);
  const head = b64u(JSON.stringify({ alg: 'RS256', kid: 'test-key', typ: 'JWT' }));
  const body = b64u(JSON.stringify({ iss: 'https://accounts.google.com', aud: GOOGLE_CLIENT, sub: '1001', email: 'player@example.com', email_verified: true, iat: now, exp: now + 3600, ...claims }));
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', googlePair.privateKey, new TextEncoder().encode(head + '.' + body));
  return head + '.' + body + '.' + b64u(sig);
}
export const chesscomCalls = [];
const CHESSCOM_SAMPLE = readFileSync(path.join(here, '..', '..', 'tests', 'chesscom-sample.pgn'), 'utf8');

export function makeEnv(origins = 'https://taussane.github.io,https://site.test') {
  return { DB: makeD1(), ALLOWED_ORIGINS: origins, GOOGLE_CLIENT_ID: GOOGLE_CLIENT };
}

export function serve(env, port) {
  return createServer(async (req, res) => {
    const chunks = []; for await (const c of req) chunks.push(c);
    if (req.url.startsWith('/test/google-id-token?')) {   // tests only: an ID token as Google would give the page
      const q = Object.fromEntries(new URL('http://x' + req.url).searchParams);
      res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end(await googleIdToken(q));
    }
    const r = new Request('http://localhost:' + port + req.url, { method: req.method, headers: req.headers, body: ['GET', 'HEAD', 'OPTIONS'].includes(req.method) ? undefined : Buffer.concat(chunks) });
    const out = await worker.fetch(r, env);
    res.writeHead(out.status, Object.fromEntries(out.headers));
    res.end(Buffer.from(await out.arrayBuffer()));
  }).listen(port);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.argv[2] || 8787);
  serve(makeEnv(), port);
  console.log('account server on http://localhost:' + port);
}
