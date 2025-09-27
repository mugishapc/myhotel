// Crescent Hotel App - PROPER FIX with PWA support
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crescent Hotel App loaded - PWA enabled');
    
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
    
    // Initialize PWA with proper error handling
    initializePWA();
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

// PROPER PWA INITIALIZATION
function initializePWA() {
    if ('serviceWorker' in navigator) {
        // Register service worker with proper scope
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then(function(registration) {
                console.log('ServiceWorker registered successfully:', registration);
                
                // Check for updates every time the app loads
                registration.update();
                
                // Handle controller change (when SW updates)
                navigator.serviceWorker.addEventListener('controllerchange', function() {
                    window.location.reload();
                });
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed:', error);
            });
    }
    
    // Add install prompt for PWA
    let deferredPrompt;
    const installBtn = document.createElement('button');
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
                    console.log('User accepted install');
                }
                deferredPrompt = null;
            });
        };
    });
    
    document.body.appendChild(installBtn);
}

// Clear cache function (for manual cache clearing if needed)
function clearAppCache() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(registrations) {
            for (let registration of registrations) {
                registration.unregister();
            }
        });
        
        caches.keys().then(function(cacheNames) {
            cacheNames.forEach(function(cacheName) {
                caches.delete(cacheName);
            });
        }).then(() => {
            window.location.reload();
        });
    }
}