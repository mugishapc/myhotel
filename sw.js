const CACHE_NAME = 'My-hotel-v1.0.0';
const urlsToCache = [
    '/',
    '/login',
    '/dashboard',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-128x128.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-152x152.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-384x384.png',
    '/static/icons/icon-512x512.png',
    '/manifest.json',
    '/offline'
];

// Install event
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
            .catch(function(error) {
                console.log('Cache installation failed:', error);
            })
    );
    self.skipWaiting(); // Force the waiting service worker to become active
});

// Fetch event with better error handling
self.addEventListener('fetch', function(event) {
    // Skip non-GET requests and external URLs
    if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Return cached version if found
                if (response) {
                    return response;
                }

                // Otherwise fetch from network
                return fetch(event.request)
                    .then(function(networkResponse) {
                        // Check if valid response
                        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                            return networkResponse;
                        }

                        // Clone the response
                        var responseToCache = networkResponse.clone();

                        // Add to cache for future visits
                        caches.open(CACHE_NAME)
                            .then(function(cache) {
                                cache.put(event.request, responseToCache);
                            });

                        return networkResponse;
                    })
                    .catch(function(error) {
                        // If network fails and it's a navigation request, show offline page
                        if (event.request.destination === 'document') {
                            return caches.match('/offline');
                        }
                        
                        // For other requests, you might want to return a fallback
                        console.log('Fetch failed; returning offline page instead.', error);
                    });
            })
    );
});

// Activate event - cleanup old caches
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim(); // Take control of all clients immediately
});