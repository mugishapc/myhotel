// Service Worker for Crescent Hotel PWA - PROPER FIX
const CACHE_NAME = 'crescent-hotel-v1.3';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Install event
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
            .then(function() {
                return self.skipWaiting(); // Activate immediately
            })
    );
});

// Activate event - Clean up old caches
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(function() {
            return self.clients.claim(); // Take control of all clients
        })
    );
});

// Fetch event - NETWORK FIRST with proper error handling
self.addEventListener('fetch', function(event) {
    // Only handle GET requests and same-origin requests
    if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(function(response) {
                // If valid response, update cache
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then(function(cache) {
                            cache.put(event.request, responseClone);
                        });
                }
                return response;
            })
            .catch(function() {
                // Network failed, try cache
                return caches.match(event.request)
                    .then(function(response) {
                        // Return cached response or fallback
                        return response || caches.match('/');
                    });
            })
    );
});