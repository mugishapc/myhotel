// Crescent Hotel App - PWA INSTALLABLE VERSION
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crescent Hotel App - PWA version loaded');
    
    // Initialize PWA features
    initializePWA();
    
    // Initialize app
    setTimeout(initializeApp, 1000);
});

function initializePWA() {
    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js?version=3.0', { 
            scope: '/',
            updateViaCache: 'none'
        })
        .then(function(registration) {
            console.log('PWA ServiceWorker registered successfully:', registration);
            
            // Check for updates every hour
            setInterval(() => {
                registration.update();
            }, 60 * 60 * 1000);
        })
        .catch(function(error) {
            console.log('ServiceWorker registration failed:', error);
        });
    }
    
    // Initialize install prompt
    initializeInstallPrompt();
}

function initializeInstallPrompt() {
    let deferredPrompt;
    const installContainer = document.getElementById('installContainer');

    window.addEventListener('beforeinstallprompt', (e) => {
        console.log('PWA install prompt triggered');
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault();
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        
        // Show install button
        showInstallButton();
    });

    function showInstallButton() {
        if (!deferredPrompt) return;
        
        // Remove existing install button if any
        const existingBtn = document.getElementById('installButton');
        if (existingBtn) existingBtn.remove();
        
        const installBtn = document.createElement('button');
        installBtn.id = 'installButton';
        installBtn.innerHTML = '📱 Install App';
        installBtn.className = 'btn btn-success btn-lg';
        installBtn.title = 'Install Crescent Hotel App on your device';
        
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            
            // Show the install prompt
            deferredPrompt.prompt();
            
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            
            console.log(`User response to the install prompt: ${outcome}`);
            
            // Hide the install button
            installBtn.style.display = 'none';
            
            // We've used the prompt, and can't use it again, throw it away
            deferredPrompt = null;
        });
        
        installContainer.appendChild(installBtn);
        
        // Auto-hide the button after 30 seconds
        setTimeout(() => {
            if (installBtn.parentNode) {
                installBtn.style.display = 'none';
            }
        }, 30000);
    }

    // Track app installation
    window.addEventListener('appinstalled', (evt) => {
        console.log('Crescent Hotel App was successfully installed!');
        // Hide the install button
        const installBtn = document.getElementById('installButton');
        if (installBtn) installBtn.style.display = 'none';
        
        // Show success message
        showInstallSuccessMessage();
    });
}

function showInstallSuccessMessage() {
    // Create a temporary success message
    const successMsg = document.createElement('div');
    successMsg.innerHTML = `
        <div class="alert alert-success alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 1050; min-width: 300px;">
            <strong>Success!</strong> App installed successfully!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.body.appendChild(successMsg);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (successMsg.parentNode) {
            successMsg.remove();
        }
    }, 5000);
}

function initializeApp() {
    console.log('Initializing app features...');
    
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
        
        /* PWA specific styles */
        @media (display-mode: standalone) {
            body {
                padding-top: env(safe-area-inset-top);
                padding-bottom: env(safe-area-inset-bottom);
            }
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

// Check if app is running in standalone mode (installed)
function isRunningAsPWA() {
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true;
}

// Update UI if running as PWA
if (isRunningAsPWA()) {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('App is running as installed PWA');
        // You can add PWA-specific UI changes here
    });
}