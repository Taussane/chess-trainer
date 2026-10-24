// The installed app's helper (registered by the page on the website only): network first, so you always
// get the latest version when online; the last copy of each page and file is kept for when you're offline.
// Calls to the account server, Lichess and Chess.com are never cached.
const CACHE = 'cst-v5';
self.addEventListener('install', e=>self.skipWaiting());
self.addEventListener('activate', e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e=>{
  const r = e.request, u = new URL(r.url);
  if(r.method!=='GET' || u.origin!==self.location.origin) return;   // other sites: straight to the network
  if(['code', 'state', 'error'].some(k=>u.searchParams.has(k))) return;   // back from a login: its one-time code is never kept
  e.respondWith(fetch(r).then(res=>{
    if(res.ok){ const copy = res.clone(); caches.open(CACHE).then(c=>c.put(r, copy)).catch(()=>{}); }
    return res;
  }).catch(()=>caches.match(r, { ignoreSearch: r.mode==='navigate' }).then(m=>m || Response.error())));
});
