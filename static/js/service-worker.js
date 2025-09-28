// Service Worker - SIMPLE BYPASS VERSION
const CACHE_NAME = 'crescent-hotel-bypass-v1';

self.addEventListener('install', (event) => {
    console.log('Service Worker: Install - Bypass Mode');
    self.skipWaiting(); // Activate immediately
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activate - Bypass Mode');
    event.waitUntil(
        self.clients.claim().then(() => {
            console.log('Service Worker now controlling clients');
        })
    );
});

self.addEventListener('fetch', (event) => {
    // COMPLETELY BYPASS service worker for all requests
    // This ensures the site always loads from network
    return fetch(event.request);
});