// Service Worker - COMPLETE RESET VERSION
const CACHE_NAME = 'crescent-hotel-reset-v1';

self.addEventListener('install', (event) => {
    console.log('Service Worker: Install');
    self.skipWaiting(); // Activate immediately
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activate');
    event.waitUntil(
        // Delete ALL old caches
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    console.log('Deleting cache:', cacheName);
                    return caches.delete(cacheName);
                })
            );
        }).then(() => {
            console.log('All old caches deleted');
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', (event) => {
    // FOR NOW: Bypass service worker completely for all requests
    // This ensures the site always works
    return fetch(event.request);
    
    // Later we can enable caching carefully:
    // event.respondWith(
    //     fetch(event.request).catch(() => {
    //         return caches.match(event.request);
    //     })
    // );
});