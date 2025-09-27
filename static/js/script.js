// Crescent Hotel App - SAFE PWA IMPLEMENTATION
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crescent Hotel App loaded - Safe PWA enabled');
    
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
        
        /* Install button styles */
        .install-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .cache-clear-btn {
            position: fixed;
            bottom: 70px;
            right: 20px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
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
    
    // Initialize Safe PWA
    initializeSafePWA();
});

function showThreeDots(button) {
    const originalHTML = button.innerHTML;
    
    // Show 3 dots animation
    button.innerHTML = `
        <span class="loading-dots">
            <span class="dot dot1">.</span>
            <span class="dot dot2">.</span>
            <span class="dot dot3">.</span>
        </span>
    `;
    button.disabled = true;
    button.classList.add('btn-loading');
    
    // Auto-restore after 3 seconds (safety measure)
    setTimeout(() => {
        if (button.classList.contains('btn-loading')) {
            button.innerHTML = originalHTML;
            button.disabled = false;
            button.classList.remove('btn-loading');
        }
    }, 3000);
}

// SAFE PWA INITIALIZATION
function initializeSafePWA() {
    if ('serviceWorker' in navigator) {
        // Register service worker with error handling
        navigator.serviceWorker.register('/sw.js?v=3.0', { scope: '/' })
            .then(function(registration) {
                console.log('ServiceWorker registered successfully:', registration);
                
                // Check for updates every hour
                setInterval(() => {
                    registration.update();
                }, 60 * 60 * 1000);
                
                // Handle updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed:', error);
                // If registration fails, clear any existing workers
                clearProblematicServiceWorkers();
            });
        
        // Handle controller changes (app updates)
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('Controller changed, reloading page...');
            window.location.reload();
        });
    }
    
    // Add install prompt
    setupInstallPrompt();
    
    // Add cache clear button for safety
    addCacheClearButton();
}

// INSTALL PROMPT SETUP
function setupInstallPrompt() {
    let deferredPrompt;
    const installBtn = document.createElement('button');
    installBtn.id = 'installPWA';
    installBtn.innerHTML = '📱 Install App';
    installBtn.className = 'btn btn-success install-btn';
    installBtn.style.display = 'none';
    
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        installBtn.style.display = 'block';
        
        installBtn.onclick = () => {
            installBtn.style.display = 'none';
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted PWA installation');
                }
                deferredPrompt = null;
            });
        };
    });
    
    window.addEventListener('appinstalled', () => {
        console.log('PWA was installed');
        installBtn.style.display = 'none';
        deferredPrompt = null;
    });
    
    document.body.appendChild(installBtn);
}

// CACHE CLEAR BUTTON FOR SAFETY
function addCacheClearButton() {
    const clearBtn = document.createElement('button');
    clearBtn.id = 'clearCache';
    clearBtn.innerHTML = '🔄 Clear Cache';
    clearBtn.className = 'btn btn-warning cache-clear-btn';
    clearBtn.style.display = 'block';
    
    clearBtn.onclick = () => {
        if (confirm('Clear app cache? This will reload the page.')) {
            clearAppCache();
        }
    };
    
    document.body.appendChild(clearBtn);
}

// SAFE CACHE CLEARING
function clearAppCache() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(registrations => {
            registrations.forEach(registration => {
                registration.unregister();
            });
        });
    }
    
    if ('caches' in window) {
        caches.keys().then(cacheNames => {
            cacheNames.forEach(cacheName => {
                caches.delete(cacheName);
            });
        });
    }
    
    // Reload after a short delay
    setTimeout(() => {
        window.location.reload(true);
    }, 1000);
}

// CLEAR PROBLEMATIC SERVICE WORKERS
function clearProblematicServiceWorkers() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(registrations => {
            registrations.forEach(registration => {
                registration.unregister();
            });
        });
    }
}

// UPDATE NOTIFICATION
function showUpdateNotification() {
    if (confirm('A new version is available. Reload to update?')) {
        window.location.reload();
    }
}