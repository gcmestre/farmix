// CompoundMeds - Application JavaScript

// Auto-dismiss messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.getElementById('messages');
    if (messages) {
        setTimeout(function() {
            messages.querySelectorAll('[class*="rounded-md"]').forEach(function(msg) {
                msg.style.transition = 'opacity 0.5s';
                msg.style.opacity = '0';
                setTimeout(function() { msg.remove(); }, 500);
            });
        }, 5000);
    }
});

// HTMX event handlers
document.body.addEventListener('htmx:beforeSwap', function(evt) {
    // Handle 422 responses (validation errors) by swapping anyway
    if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    }
});
