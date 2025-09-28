// Service Worker - PWA ENABLED VERSION
const CACHE_NAME = 'crescent-hotel-pwa-v3.0';
const urlsToCache = [
    '/',
    '/login',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/manifest.json'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing PWA...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching app shell');
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('Service Worker: Skip waiting');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating PWA...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Claiming clients');
            return self.clients.claim();
        })
    );
});

// Fetch event - Network first, then cache strategy
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // For API calls, always go to network
    if (event.request.url.includes('/api/') || 
        event.request.url.includes('/sell_room') ||
        event.request.url.includes('/add_expense') ||
        event.request.url.includes('/restore_room')) {
        event.respondWith(fetch(event.request));
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // If valid response, cache it
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // If network fails, try cache
                return caches.match(event.request)
                    .then((cachedResponse) => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // If not in cache, return offline page for navigation requests
                        if (event.request.mode === 'navigate') {
                            return caches.match('/offline');
                        }
                        return new Response('Network error happened', {
                            status: 408,
                            headers: { 'Content-Type': 'text/plain' }
                        });
                    });
            })
    );
});

// Handle background sync (for offline functionality)
self.addEventListener('sync', (event) => {
    console.log('Background sync:', event.tag);
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    console.log('Doing background sync...');
    // You can implement background sync logic here
}