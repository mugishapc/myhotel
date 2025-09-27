// Service Worker for Crescent Hotel - SAFE PWA IMPLEMENTATION
const CACHE_NAME = 'crescent-hotel-v3.0';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/script.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/login',
    '/dashboard'
];

// Install event - Cache essential files only
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('Service Worker installed');
                return self.skipWaiting();
            })
    );
});

// Activate event - Clean up old caches carefully
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker activated');
            return self.clients.claim();
        })
    );
});

// Fetch event - NETWORK FIRST with fallback
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests and external URLs
    if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) {
        return;
    }

    // Special handling for API routes - always go to network
    if (event.request.url.includes('/api/') || event.request.url.includes('/sell_room') || 
        event.request.url.includes('/restore_room') || event.request.url.includes('/add_expense')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Cache successful responses for static assets only
                if (response.status === 200 && 
                    (event.request.url.includes('/static/') || 
                     event.request.url === self.location.origin + '/' ||
                     event.request.url.includes('/login'))) {
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                        .then((cache) => {
                            cache.put(event.request, responseToCache);
                        });
                }
                return response;
            })
            .catch((error) => {
                // Only use cache for static assets and essential pages
                if (event.request.url.includes('/static/') || 
                    event.request.url === self.location.origin + '/' ||
                    event.request.url.includes('/login') ||
                    event.request.url.includes('/dashboard')) {
                    
                    return caches.match(event.request)
                        .then((response) => {
                            return response || fetch(event.request);
                        });
                }
                
                // For dynamic content, always try network again
                return fetch(event.request);
            })
    );
});

// Handle messages from the main thread
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
});