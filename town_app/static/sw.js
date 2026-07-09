// OnBrandCraftz Service Worker — enables PWA install + offline shell
const CACHE = 'oncraftz-v1';
const SHELL = ['/', '/favicon.png', '/icon-192.png', '/icon-512.png', '/manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Always go to network for: API calls, WebSocket upgrades, data files, agent tasks
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/ws') ||
      url.pathname.startsWith('/data/') ||
      e.request.method !== 'GET') {
    return;
  }
  // For the app shell: serve from cache, fall back to network
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(resp => {
      if (resp.ok && url.origin === location.origin) {
        const clone = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return resp;
    }))
  );
});
