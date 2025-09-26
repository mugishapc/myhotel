// Enhanced JavaScript with click animations
document.addEventListener('DOMContentLoaded', function() {
    console.log('Crescent Hotel App Loaded');
    
    // 1. Auto-dismiss alerts after 5 seconds
    initAlerts();
    
    // 2. Button click animations
    initButtonAnimations();
    
    // 3. Form loading states
    initFormLoading();
    
    // 4. Safe PWA features
    initPWA();
});

function initAlerts() {
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
}

function initButtonAnimations() {
    // Add click animations to ALL buttons
    document.addEventListener('click', function(e) {
        // Check if it's a button or link with btn class
        if (e.target.tagName === 'BUTTON' || 
            e.target.classList.contains('btn') ||
            e.target.closest('button') ||
            e.target.closest('.btn')) {
            
            let button = e.target;
            
            // If clicked on inner element, find the parent button
            if (!button.classList.contains('btn') && button.tagName !== 'BUTTON') {
                button = button.closest('button') || button.closest('.btn');
            }
            
            if (button) {
                // Add pressing effect
                button.style.transform = 'scale(0.95)';
                button.style.transition = 'transform 0.1s ease';
                
                // Add ripple effect
                createRippleEffect(button, e);
                
                // Restore after animation
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 150);
            }
        }
    });
}

function createRippleEffect(button, event) {
    // Remove existing ripples
    const existingRipples = button.querySelectorAll('.ripple');
    existingRipples.forEach(ripple => ripple.remove());
    
    // Create ripple element
    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    
    // Get button position and click coordinates
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    // Style the ripple
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    
    // Add to button
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
        if (ripple.parentNode === button) {
            button.removeChild(ripple);
        }
    }, 600);
}

function initFormLoading() {
    // Add loading states to form buttons
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                // Don't prevent default form submission
                addLoadingState(submitButton);
            }
        });
    });
}

function addLoadingState(button) {
    const originalHTML = button.innerHTML;
    
    // Add spinner and change text
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        Processing...
    `;
    button.disabled = true;
    
    // Safety: restore after 5 seconds if still loading
    setTimeout(() => {
        if (button.innerHTML.includes('spinner-border')) {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }, 5000);
}

function initPWA() {
    // Optional PWA features
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('PWA Service Worker registered');
            })
            .catch(error => {
                console.log('PWA not available');
            });
    }
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    /* Ripple effect styles */
    .ripple {
        position: absolute;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.7);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    /* Button animations */
    .btn {
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
    }
    
    .btn:active {
        transform: scale(0.95);
    }
    
    /* Spinner styles */
    .spinner-border-sm {
        width: 1rem;
        height: 1rem;
    }
    
    /* Enhanced focus states */
    .btn:focus {
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
    }
    
    /* Hover effects */
    .btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
`;
document.head.appendChild(style);

console.log('Button animations loaded - Click any button to see effects!');