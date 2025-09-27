// Crescent Hotel App - COMPLETE RESET VERSION
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crescent Hotel App - Reset version loaded');
    
    // FIRST: Clear any problematic service workers immediately
    clearAllServiceWorkers();
    
    // Then load the rest of the app
    initializeApp();
});

function initializeApp() {
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
    
    // Register a SAFE service worker after 3 seconds
    setTimeout(registerSafeServiceWorker, 3000);
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

// NUCLEAR OPTION: Clear ALL service workers
function clearAllServiceWorkers() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(registrations) {
            console.log('Found', registrations.length, 'service workers to unregister');
            registrations.forEach(function(registration) {
                registration.unregister().then(function(success) {
                    console.log('ServiceWorker unregistered:', success);
                });
            });
        });
        
        // Clear all caches
        if ('caches' in window) {
            caches.keys().then(function(cacheNames) {
                console.log('Clearing', cacheNames.length, 'caches');
                cacheNames.forEach(function(cacheName) {
                    caches.delete(cacheName);
                });
            });
        }
        
        // Clear storage
        localStorage.removeItem('service-worker-registered');
        sessionStorage.clear();
    }
}

// Register a VERY SAFE service worker
function registerSafeServiceWorker() {
    if ('serviceWorker' in navigator) {
        // Only register if not already registered
        navigator.serviceWorker.getRegistrations().then(registrations => {
            if (registrations.length === 0) {
                navigator.serviceWorker.register('/sw.js?version=' + Date.now(), { scope: './' })
                    .then(function(registration) {
                        console.log('Safe ServiceWorker registered');
                        localStorage.setItem('service-worker-registered', 'true');
                    })
                    .catch(function(error) {
                        console.log('ServiceWorker registration failed (safe mode):', error);
                    });
            }
        });
    }
}

// Add install prompt (simple version)
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install button after 5 seconds
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