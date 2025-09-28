// Service Worker for Crescent Hotel PWA - FIXED VERSION
const CACHE_NAME = 'crescent-hotel-v1.2'; // Changed version to force update
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-128x128.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-152x152.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-384x384.png',
    '/static/icons/icon-512x512.png'
];

// Install event - SKIP WAITING FOR IMMEDIATE ACTIVATION
self.addEventListener('install', function(event) {
    self.skipWaiting(); // Force activation immediately
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

// Activate event - CLEAR OLD CACHES
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
        }).then(function() {
            return self.clients.claim(); // Take control immediately
        })
    );
});

// Fetch event - NETWORK FIRST STRATEGY
self.addEventListener('fetch', function(event) {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    event.respondWith(
        fetch(event.request)
            .then(function(response) {
                // If network request succeeds, update cache
                if (response.status === 200) {
                    caches.open(CACHE_NAME)
                        .then(function(cache) {
                            cache.put(event.request, response.clone());
                        });
                }
                return response;
            })
            .catch(function() {
                // If network fails, try cache
                return caches.match(event.request)
                    .then(function(response) {
                        return response || caches.match('/offline');
                    });
            })
    );
});