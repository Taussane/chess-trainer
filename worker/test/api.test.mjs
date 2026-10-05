// The account server's rules, run here on the stand-in database and stand-in Lichess.
// node --test worker/test/
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeEnv, lichessCalls } from './local.mjs';
import worker from '../src/index.js';

const ORIGIN = 'https://taussane.github.io';
function call(env, method, path, { token = 'tok-taussane', body, origin = ORIGIN } = {}) {
  const headers = { Origin: origin };
  if (token) headers.Authorization = 'Bearer ' + token;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  return worker.fetch(new Request('https://api.test' + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) }), env);
}
const j = async r => ({ status: r.status, body: await r.json() });

test('first sign-in creates the account; later ones find it; Lichess is asked once a day', async () => {
  const env = makeEnv(); lichessCalls.n = 0;
  const a = await j(await call(env, 'GET', '/api/me'));
  assert.equal(a.status, 200);
  assert.deepEqual(a.body.connections, [{ site: 'lichess', username: 'Taussane', verified: true }]);
  const b = await j(await call(env, 'GET', '/api/me'));
  assert.equal(b.body.account.id, a.body.account.id);
  assert.equal(lichessCalls.n, 1, 'the second request uses the remembered sign-in');
  const o = await j(await call(env, 'GET', '/api/me', { token: 'tok-other' }));
  assert.notEqual(o.body.account.id, a.body.account.id);
  assert.equal(env.DB.raw.prepare('SELECT COUNT(*) n FROM sessions').get().n, 2);
  assert.ok(!JSON.stringify(env.DB.raw.prepare('SELECT * FROM sessions').all()).includes('tok-'), 'tokens are never stored');
});

test('no or unknown token: refused', async () => {
  const env = makeEnv();
  assert.equal((await call(env, 'GET', '/api/me', { token: null })).status, 401);
  assert.equal((await call(env, 'GET', '/api/me', { token: 'tok-nobody' })).status, 401);
});

test('results: added once, read back in order and in pages, each account only its own', async () => {
  const env = makeEnv();
  const rows = Array.from({ length: 1200 }, (_, i) => ({ a: 'analysis', acc: 70, ts: 1000 + i, src: 'masters', key: 'k' + i, miss: false }));
  for (let i = 0; i < rows.length; i += 500) assert.equal((await call(env, 'POST', '/api/results', { body: { rows: rows.slice(i, i + 500) } })).status, 200);
  await call(env, 'POST', '/api/results', { body: { rows: rows.slice(0, 10) } });   // sent twice: ignored
  const p1 = (await j(await call(env, 'GET', '/api/results?after=-1&limit=1000'))).body.rows;
  const p2 = (await j(await call(env, 'GET', '/api/results?after=' + p1[p1.length - 1].ts + '&limit=1000'))).body.rows;
  assert.equal(p1.length, 1000); assert.equal(p2.length, 200);
  assert.deepEqual(p1[5], rows[5]);
  assert.equal((await j(await call(env, 'GET', '/api/results', { token: 'tok-other' }))).body.rows.length, 0);
  assert.equal((await call(env, 'POST', '/api/results', { body: { rows: rows.slice(0, 501) } })).status, 400);
});

test('games: saved without their positions, replaced, removed', async () => {
  const env = makeEnv();
  const g = { id: 'abcdEFGH', site: 'lichess', sans: ['e4', 'e5'], evals: null, status: 'queued', positions: [{ key: 'x' }] };
  await call(env, 'POST', '/api/games', { body: { games: [g, { id: 'cc-123', site: 'chesscom', sans: ['d4'] }] } });
  await call(env, 'POST', '/api/games', { body: { games: [{ ...g, status: 'evaluated' }] } });
  let games = (await j(await call(env, 'GET', '/api/games'))).body.games;
  assert.equal(games.length, 2);
  const a = games.find(x => x.id === 'abcdEFGH');
  assert.equal(a.status, 'evaluated'); assert.equal(a.positions, undefined);
  await call(env, 'DELETE', '/api/games/abcdEFGH');
  games = (await j(await call(env, 'GET', '/api/games'))).body.games;
  assert.deepEqual(games.map(x => x.id), ['cc-123']);
});

test('meta documents; log out forgets the sign-in; delete account removes everything', async () => {
  const env = makeEnv(); lichessCalls.n = 0;
  assert.deepEqual((await j(await call(env, 'GET', '/api/meta/profile'))).body, { exists: false, data: null });
  await call(env, 'PUT', '/api/meta/profile', { body: { data: { joinedAt: 5 } } });
  assert.deepEqual((await j(await call(env, 'GET', '/api/meta/profile'))).body, { exists: true, data: { joinedAt: 5 } });
  await call(env, 'DELETE', '/api/session');
  await call(env, 'GET', '/api/me');
  assert.equal(lichessCalls.n, 2, 'after logging out, the next request is checked with Lichess again');
  await call(env, 'POST', '/api/results', { body: { rows: [{ a: 'final', acc: 50, ts: 1 }] } });
  await call(env, 'DELETE', '/api/account');
  for (const t of ['accounts', 'connections', 'sessions', 'results', 'games', 'meta'])
    assert.equal(env.DB.raw.prepare(`SELECT COUNT(*) n FROM ${t}`).get().n, 0, t + ' emptied');
  const again = await j(await call(env, 'GET', '/api/me'));   // signing in again starts a fresh account
  assert.equal(again.status, 200);
});

test('only the website may call it from a browser', async () => {
  const env = makeEnv();
  const ok = await call(env, 'OPTIONS', '/api/me', { token: null });
  assert.equal(ok.status, 204); assert.equal(ok.headers.get('Access-Control-Allow-Origin'), ORIGIN);
  const bad = await call(env, 'OPTIONS', '/api/me', { token: null, origin: 'https://evil.example' });
  assert.equal(bad.status, 403);
  const r = await call(env, 'GET', '/api/me', { origin: 'https://evil.example' });
  assert.equal(r.headers.get('Access-Control-Allow-Origin'), null);
});
