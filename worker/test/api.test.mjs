// The account server's rules, run here on the stand-in database and stand-in Lichess.
// node --test worker/test/
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeEnv, lichessCalls, chesscomCalls, googleIdToken, googleCalls } from './local.mjs';
import worker from '../src/index.js';

const ORIGIN = 'https://taussane.github.io';
function call(env, method, path, { token = 'tok-taussane', body, origin = ORIGIN, headers: extra = {} } = {}) {
  const headers = { Origin: origin, ...extra };
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
  await call(env, 'POST', '/api/games', { body: { games: [{ id: 'cc-9', site: 'chesscom', sans: ['d4'] }] } });
  assert.equal((await j(await call(env, 'GET', '/api/games'))).body.games.length, 0, 'no Chess.com games without a Chess.com username');
  await call(env, 'PUT', '/api/meta/chesscom', { body: { data: { username: 'CCPlayer' } } });
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

test('Chess.com: a player is found or not; their newest live games, after a time, newest first', async () => {
  const env = makeEnv();
  assert.deepEqual((await j(await call(env, 'GET', '/api/chesscom/player?user=CCPlayer'))).body, { username: 'CCPlayer' });
  assert.equal((await call(env, 'GET', '/api/chesscom/player?user=nobody')).status, 404);
  assert.equal((await call(env, 'GET', '/api/chesscom/player?user=../x')).status, 400);
  assert.equal((await call(env, 'GET', '/api/chesscom/games?user=ccplayer', { token: null })).status, 401, 'only for signed-in players');
  const all = await (await call(env, 'GET', '/api/chesscom/games?user=ccplayer&max=100')).text();
  const dates = [...all.matchAll(/\[UTCDate "([^"]+)"\]/g)].map(m => m[1]);
  assert.equal(dates.length, 9, 'the daily game is left out');
  assert.deepEqual(dates, dates.slice().sort().reverse(), 'newest first');
  chesscomCalls.length = 0;
  const since = Date.UTC(2026, 9, 14, 0, 0, 0);   // 14 October: only the October month is read
  const newer = await (await call(env, 'GET', '/api/chesscom/games?user=ccplayer&since=' + since)).text();
  assert.ok([...newer.matchAll(/\[UTCDate "([^"]+)"\]/g)].every(m => m[1] >= '2026.10.14'));
  assert.ok(!chesscomCalls.some(u => u.includes('/2026/09/')), 'older months are not read');
  const two = await (await call(env, 'GET', '/api/chesscom/games?user=ccplayer&max=2')).text();
  assert.equal([...two.matchAll(/\[Event /g)].length, 2);
});

test('Google: a checked ID token gives our own login; the same Google account finds the same account', async () => {
  const env = makeEnv();
  const login = async idToken => j(await call(env, 'POST', '/api/login/google', { token: null, body: { idToken } }));
  const a = await login(await googleIdToken());
  assert.equal(a.status, 200); assert.equal(a.body.email, 'player@example.com');
  const me = await j(await call(env, 'GET', '/api/me', { token: null, headers: { Authorization: 'Bearer ' + a.body.token, 'X-Auth-Site': 'app' } }));
  assert.equal(me.status, 200);
  assert.deepEqual(me.body.connections, [{ site: 'google', username: 'player@example.com', verified: true }]);
  const b = await login(await googleIdToken());   // another device
  assert.notEqual(b.body.token, a.body.token);
  const me2 = await j(await call(env, 'GET', '/api/me', { token: null, headers: { Authorization: 'Bearer ' + b.body.token, 'X-Auth-Site': 'app' } }));
  assert.equal(me2.body.account.id, me.body.account.id);
  assert.ok(!JSON.stringify(env.DB.raw.prepare('SELECT * FROM sessions').all()).includes(a.body.token), 'our tokens are never stored');
  // refused: another site's client, expired, unverified email, tampered, forged signature, made-up token
  const forged = (await googleIdToken()).split('.'); forged[1] = Buffer.from(JSON.stringify({ iss: 'https://accounts.google.com', aud: 'test-client.apps.googleusercontent.com', sub: '666', email: 'x@y.z', exp: 2e9 })).toString('base64url');
  for (const bad of [await googleIdToken({ aud: 'someone-else' }), await googleIdToken({ exp: 1000 }), await googleIdToken({ email_verified: false }), forged.join('.'), 'abc'])
    assert.equal((await login(bad)).status, 401);
  assert.equal((await call(env, 'GET', '/api/me', { token: null, headers: { Authorization: 'Bearer made-up', 'X-Auth-Site': 'app' } })).status, 401);
  // log out: that token stops working, the other device's still works
  await call(env, 'DELETE', '/api/session', { token: null, headers: { Authorization: 'Bearer ' + a.body.token, 'X-Auth-Site': 'app' } });
  assert.equal((await call(env, 'GET', '/api/me', { token: null, headers: { Authorization: 'Bearer ' + a.body.token, 'X-Auth-Site': 'app' } })).status, 401);
  assert.equal((await call(env, 'GET', '/api/me', { token: null, headers: { Authorization: 'Bearer ' + b.body.token, 'X-Auth-Site': 'app' } })).status, 200);
  assert.ok(googleCalls.n >= 1);
});

test('linking: a Google login added to a Lichess account; an existing Google account is merged into it', async () => {
  const env = makeEnv();
  const app = tok => ({ token: null, headers: { Authorization: 'Bearer ' + tok, 'X-Auth-Site': 'app' } });
  // The Google account already has progress, a game and a Chess.com name; the Lichess one too.
  const g = (await j(await call(env, 'POST', '/api/login/google', { token: null, body: { idToken: await googleIdToken({ sub: '77' }) } }))).body;
  await call(env, 'POST', '/api/results', { ...app(g.token), body: { rows: [{ a: 'analysis', acc: 50, ts: 10 }, { a: 'final', acc: 60, ts: 20 }] } });
  await call(env, 'PUT', '/api/meta/chesscom', { ...app(g.token), body: { data: { username: 'CCPlayer' } } });
  await call(env, 'POST', '/api/games', { ...app(g.token), body: { games: [{ id: 'cc-1', site: 'chesscom', sans: ['e4'] }] } });
  await call(env, 'PUT', '/api/meta/profile', { ...app(g.token), body: { data: { joinedAt: 1 } } });
  await call(env, 'POST', '/api/results', { body: { rows: [{ a: 'analysis', acc: 70, ts: 10 }, { a: 'candidates', acc: 80, ts: 30 }] } });
  await call(env, 'PUT', '/api/meta/profile', { body: { data: { joinedAt: 5 } } });
  const lich = (await j(await call(env, 'GET', '/api/me'))).body.account.id;
  const r = await j(await call(env, 'POST', '/api/link/google', { body: { idToken: await googleIdToken({ sub: '77' }) } }));
  assert.deepEqual(r.body, { ok: true, merged: true });
  const me = (await j(await call(env, 'GET', '/api/me'))).body;
  assert.equal(me.account.id, lich);
  assert.deepEqual(me.connections.map(c => c.site).sort(), ['google', 'lichess']);
  const rows = (await j(await call(env, 'GET', '/api/results?after=-1'))).body.rows;
  assert.deepEqual(rows.map(x => [x.ts, x.a, x.acc]), [[10, 'analysis', 70], [20, 'final', 60], [30, 'candidates', 80]], 'both; on a clash the Lichess account wins');
  assert.deepEqual((await j(await call(env, 'GET', '/api/games'))).body.games.map(x => x.id), ['cc-1']);
  assert.deepEqual((await j(await call(env, 'GET', '/api/meta/chesscom'))).body.data, { username: 'CCPlayer' });
  assert.deepEqual((await j(await call(env, 'GET', '/api/meta/profile'))).body.data, { joinedAt: 1 }, 'training since: the earlier date');
  // The Google login (old token and a new one) now opens the same account; one account is left.
  assert.equal((await j(await call(env, 'GET', '/api/me', app(g.token)))).body.account.id, lich);
  const g2 = (await j(await call(env, 'POST', '/api/login/google', { token: null, body: { idToken: await googleIdToken({ sub: '77' }) } }))).body;
  assert.equal((await j(await call(env, 'GET', '/api/me', app(g2.token)))).body.account.id, lich);
  assert.equal(env.DB.raw.prepare('SELECT COUNT(*) n FROM accounts').get().n, 1);
  // The other way: a Google-only account adds a Lichess login that has no account yet.
  const h = (await j(await call(env, 'POST', '/api/login/google', { token: null, body: { idToken: await googleIdToken({ sub: '88' }) } }))).body;
  assert.equal((await j(await call(env, 'POST', '/api/link/lichess', { ...app(h.token), body: { token: 'tok-other' } }))).body.merged, false);
  const hid = (await j(await call(env, 'GET', '/api/me', app(h.token)))).body.account.id;
  assert.equal((await j(await call(env, 'GET', '/api/me', { token: 'tok-other' }))).body.account.id, hid);
  assert.equal((await call(env, 'POST', '/api/link/lichess', { ...app(h.token), body: { token: 'tok-nobody' } })).status, 401);
  // Lichess off again: only while Google stays; its games go.
  assert.equal((await call(env, 'DELETE', '/api/link/lichess', { token: 'tok-taussane' })).status, 200, 'Taussane has Google (sub 77) linked');
  assert.deepEqual((await j(await call(env, 'GET', '/api/me', app(g2.token)))).body.connections.map(c => c.site), ['google']);
  const solo = makeEnv(); await call(solo, 'GET', '/api/me');
  assert.equal((await call(solo, 'DELETE', '/api/link/lichess')).status, 400, 'not when Lichess is the only login');
});
