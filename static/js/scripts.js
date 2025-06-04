// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Character counter for tweet textarea
    const tweetTextarea = document.querySelector('textarea[name="content"]');
    if (tweetTextarea) {
        const charCounter = tweetTextarea.parentElement.querySelector('small');
        const maxLength = tweetTextarea.getAttribute('maxlength');
        
        // Update character count when typing
        tweetTextarea.addEventListener('input', function() {
            const remaining = maxLength - this.value.length;
            charCounter.textContent = `${remaining} characters remaining`;
            
            // Change color when approaching limit
            if (remaining <= 20) {
                charCounter.classList.add('text-danger');
            } else {
                charCounter.classList.remove('text-danger');
            }
        });
    }
    
    // Bootstrap tooltip initialization (if needed)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});