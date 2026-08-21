// Service worker: home-screen presence and a shell that loads instantly.
//
// This is the reference you open standing at a cabinet with a meter in one
// hand, which is exactly where the wifi is someone else's and barely there.
// Installing it puts it one tap away and makes the shell load from disk.
//
// ## What it deliberately does not do
//
// It does not make the manuals available offline. The scans live in R2 and are
// large; quietly filling a phone with them because someone opened a page is
// not a decision a cache should make on its own. Pinning a chosen manual for a
// job is a real feature and wants designing — which documents, what storage
// budget, how you tell it to forget — rather than falling out of a fetch
// handler. So anything that is not the shell goes straight to the network,
// untouched.
//
// ## Why network-first
//
// Nothing here is content-hashed: /css/app.css and /js/app.js keep their names
// across every deploy. Cache-first would pin whichever build a reader happened
// to arrive on, permanently. So the cache only answers when the network does
// not — current build online, last-seen shell offline. Cloudflare serves these
// with an ETag, so an unchanged file costs a 304 and no body.

const CACHE = 'crt-shell-v1';

const SHELL = [
  '/',
  '/css/app.css',
  '/js/app.js',
  '/favicon.svg',
  '/manifest.webmanifest',
];

// Only these are worth holding. Everything else — /api/, /pdf/, page scans —
// is either large, or a lookup whose answer should not be a day old.
const SHELL_PREFIXES = ['/css/', '/js/', '/assets/'];

function isShell(pathname) {
  return (
    SHELL.includes(pathname) ||
    SHELL_PREFIXES.some((p) => pathname.startsWith(p)) ||
    pathname.startsWith('/icon-') ||
    pathname === '/apple-touch-icon.png'
  );
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      // Individually, so one missing entry cannot fail the install and leave
      // the previous worker silently in place.
      await Promise.all(SHELL.map((url) => cache.add(url).catch(() => {})));
      await self.skipWaiting();
    }),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(names.filter((n) => n !== CACHE).map((n) => caches.delete(n)));
      await self.clients.claim();
    })(),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const navigation = request.mode === 'navigate';
  if (!navigation && !isShell(url.pathname)) return; // scans and API: not ours

  event.respondWith(
    (async () => {
      try {
        const fresh = await fetch(request);
        if (fresh.ok) {
          const cache = await caches.open(CACHE);
          // Every client route renders from the same shell, so one entry
          // serves /search and /boards as well as /.
          cache.put(navigation ? '/' : request, fresh.clone());
        }
        return fresh;
      } catch {
        const cached =
          (await caches.match(request)) ||
          (navigation ? await caches.match('/') : undefined);
        if (cached) return cached;
        throw new Error('offline and nothing cached');
      }
    })(),
  );
});
