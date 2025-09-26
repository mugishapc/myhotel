
// Enhanced JavaScript for PWA functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Add app-like interactions
    addAppLikeInteractions();
});

function addAppLikeInteractions() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('button[type="submit"], .btn-primary, .btn-success');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.type === 'submit' || this.classList.contains('btn-primary') || this.classList.contains('btn-success')) {
                // Add loading spinner
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
                this.disabled = true;
                
                // Restore after 2 seconds if still on same page
                setTimeout(() => {
                    if (this.innerHTML.includes('spinner-border')) {
                        this.innerHTML = originalText;
                        this.disabled = false;
                    }
                }, 2000);
            }
        });
    });

    // Prevent double clicks
    let lastClickTime = 0;
    document.addEventListener('click', function(e) {
        const currentTime = new Date().getTime();
        if (currentTime - lastClickTime < 1000) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        lastClickTime = currentTime;
    });

    // Add touch feedback
    document.addEventListener('touchstart', function() {}, { passive: true });

    // Handle online/offline status
    window.addEventListener('online', function() {
        showNotification('Connection restored', 'success');
    });

    window.addEventListener('offline', function() {
        showNotification('You are offline', 'warning');
    });
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
    notification.style.zIndex = '1060';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Request device permissions for PWA
if ('serviceWorker' in navigator && 'Notification' in window) {
    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            console.log('Notification permission granted');
        }
    });
}

// Handle app launch
if (window.matchMedia('(display-mode: standalone)').matches) {
    document.body.classList.add('standalone');
    
    // Add standalone specific styles
    const style = document.createElement('style');
    style.textContent = `
        .standalone body {
            padding-top: env(safe-area-inset-top);
            padding-bottom: env(safe-area-inset-bottom);
            padding-left: env(safe-area-inset-left);
            padding-right: env(safe-area-inset-right);
        }
        
        .standalone .navbar {
            padding-top: env(safe-area-inset-top);
        }
    `;
    document.head.appendChild(style);
}