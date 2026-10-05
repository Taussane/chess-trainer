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
  return realFetch(url, opts);
};

export function makeEnv(origins = 'https://taussane.github.io,https://site.test') {
  return { DB: makeD1(), ALLOWED_ORIGINS: origins };
}

export function serve(env, port) {
  return createServer(async (req, res) => {
    const chunks = []; for await (const c of req) chunks.push(c);
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
