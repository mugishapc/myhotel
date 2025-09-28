// Crescent Hotel App - FIXED VERSION
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crescent Hotel App - Fixed version loaded');
    
    // IMMEDIATELY clear service workers and caches
    clearAllServiceWorkers();
    
    // Initialize app after a short delay
    setTimeout(initializeApp, 1000);
});

function initializeApp() {
    console.log('Initializing app...');
    
    // Add the CSS for 3 dots animation
    const style = document.createElement('style');
    style.textContent = `
        .loading-dots {
            display: inline-block;
            font-size: 20px;
            font-weight: bold;
        }
        .dot {
            animation: bounce 1.4s infinite both;
            display: inline-block;
        }
        .dot1 { animation-delay: -0.32s; }
        .dot2 { animation-delay: -0.16s; }
        .dot3 { animation-delay: 0s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        .btn-loading {
            background-color: #6c757d !important;
            opacity: 0.8;
        }
    `;
    document.head.appendChild(style);

    // Handle form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"], .btn[type="submit"]');
            if (submitBtn) {
                showThreeDots(submitBtn);
            }
        });
    });

    // Handle regular button clicks
    document.addEventListener('click', function(e) {
        const button = e.target.closest('.btn, button');
        if (button && !button.disabled && button.type !== 'submit') {
            showThreeDots(button);
        }
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (error) {
                alert.style.display = 'none';
            }
        });
    }, 5000);
    
    // Form validation
    const formsValidation = document.querySelectorAll('form');
    formsValidation.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Register service worker only after everything is stable
    setTimeout(registerSafeServiceWorker, 5000);
}

function showThreeDots(button) {
    const originalHTML = button.innerHTML;
    
    button.innerHTML = `
        <span class="loading-dots">
            <span class="dot dot1">.</span>
            <span class="dot dot2">.</span>
            <span class="dot dot3">.</span>
        </span>
    `;
    button.disabled = true;
    button.classList.add('btn-loading');
    
    setTimeout(() => {
        if (button.classList.contains('btn-loading')) {
            button.innerHTML = originalHTML;
            button.disabled = false;
            button.classList.remove('btn-loading');
        }
    }, 3000);
}

// COMPLETE Service Worker Cleanup
function clearAllServiceWorkers() {
    if ('serviceWorker' in navigator) {
        console.log('Clearing all service workers...');
        
        // Unregister all service workers
        navigator.serviceWorker.getRegistrations().then(function(registrations) {
            console.log('Found', registrations.length, 'service workers to unregister');
            for(let registration of registrations) {
                registration.unregister().then(function(success) {
                    console.log('ServiceWorker unregistered:', success);
                }).catch(function(error) {
                    console.log('Error unregistering service worker:', error);
                });
            }
        }).catch(function(error) {
            console.log('Error getting service worker registrations:', error);
        });
        
        // Clear all caches
        if ('caches' in window) {
            caches.keys().then(function(cacheNames) {
                console.log('Clearing', cacheNames.length, 'caches');
                cacheNames.forEach(function(cacheName) {
                    caches.delete(cacheName).then(function(success) {
                        console.log('Cache deleted:', cacheName, success);
                    });
                });
            }).catch(function(error) {
                console.log('Error clearing caches:', error);
            });
        }
        
        // Clear storage
        try {
            localStorage.removeItem('service-worker-registered');
            sessionStorage.clear();
        } catch (e) {
            console.log('Error clearing storage:', e);
        }
    }
}

// Safe Service Worker Registration
function registerSafeServiceWorker() {
    if ('serviceWorker' in navigator) {
        // Double check no existing registrations
        navigator.serviceWorker.getRegistrations().then(registrations => {
            if (registrations.length === 0) {
                // Register with very specific scope and version
                navigator.serviceWorker.register('/sw.js?version=' + Date.now(), { 
                    scope: '/',
                    updateViaCache: 'none'
                })
                .then(function(registration) {
                    console.log('Safe ServiceWorker registered successfully');
                    localStorage.setItem('service-worker-registered', 'true');
                })
                .catch(function(error) {
                    console.log('ServiceWorker registration failed:', error);
                });
            } else {
                console.log('Service workers already registered, skipping');
            }
        });
    }
}

// Install prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    setTimeout(() => {
        showInstallButton();
    }, 5000);
});

function showInstallButton() {
    if (!deferredPrompt) return;
    
    const installBtn = document.createElement('button');
    installBtn.innerHTML = '📱 Install App';
    installBtn.className = 'btn btn-success';
    installBtn.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000;';
    
    installBtn.onclick = () => {
        installBtn.style.display = 'none';
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            deferredPrompt = null;
        });
    };
    
    document.body.appendChild(installBtn);
}

// Global error handler to catch any issues
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});