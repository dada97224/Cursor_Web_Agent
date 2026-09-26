const VERSION = "maison-6";
const CACHE = `maison-${VERSION}`;

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(["/", "/css/maison.css", "/js/main.js"])));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((cles) => Promise.all(
    cles.filter((cle) => cle !== CACHE).map((cle) => caches.delete(cle))
  )));
  self.clients.claim();
});

function gardable(url) {
  return url.pathname === "/" || url.pathname === "/api/courses" || url.pathname.startsWith("/js/") || url.pathname.startsWith("/css/") || url.pathname.startsWith("/icones/");
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (!gardable(url)) return;
  event.respondWith((async () => {
    try {
      const reponse = await fetch(event.request);
      const cache = await caches.open(CACHE);
      cache.put(event.request, reponse.clone());
      return reponse;
    } catch (erreur) {
      const garde = await caches.match(event.request);
      if (garde) return garde;
      throw erreur;
    }
  })());
});
