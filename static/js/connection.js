// JavaScript for database connection page

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('connect-form');
    const connectBtn = document.getElementById('connect-btn');
    const errorAlert = document.getElementById('error-alert');
    const successAlert = document.getElementById('success-alert');
    const savedPathAlert = document.getElementById('saved-path-alert');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    const savedPathMessage = document.getElementById('saved-path-message');
    const dbPathInput = document.getElementById('db-path');

    // Load saved path from localStorage
    const savedPath = localStorage.getItem('chromadb_path');
    if (savedPath) {
        dbPathInput.value = savedPath;
        savedPathMessage.textContent = 'Using previously saved database path';
        savedPathAlert.classList.remove('d-none');
        
        // Show clear path link
        const clearPathLink = document.getElementById('clear-path-link');
        clearPathLink.style.display = 'block';
        
        // Auto-hide the saved path alert after 3 seconds
        setTimeout(() => {
            savedPathAlert.style.opacity = '0.7';
            setTimeout(() => {
                savedPathAlert.classList.add('d-none');
                savedPathAlert.style.opacity = '1';
            }, 300);
        }, 3000);
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const dbPath = dbPathInput.value.trim();
        
        if (!dbPath) {
            showError('Please enter a database path');
            return;
        }

        // Show loading state
        connectBtn.disabled = true;
        connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
        hideAlerts();

        try {
            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ db_path: dbPath })
            });

            const data = await response.json();

            if (response.ok) {
                // Save the successful path to localStorage
                localStorage.setItem('chromadb_path', dbPath);
                
                showSuccess(data.message);
                // Redirect to collections page after a short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                showError(data.detail || 'Failed to connect to database');
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        } finally {
            // Reset button state
            connectBtn.disabled = false;
            connectBtn.innerHTML = '<i class="fas fa-plug"></i> Connect to Database';
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorAlert.classList.remove('d-none');
        successAlert.classList.add('d-none');
    }

    function showSuccess(message) {
        successMessage.textContent = message;
        successAlert.classList.remove('d-none');
        errorAlert.classList.add('d-none');
    }

    function hideAlerts() {
        errorAlert.classList.add('d-none');
        successAlert.classList.add('d-none');
        savedPathAlert.classList.add('d-none');
    }

    // Global function to clear saved path
    window.clearSavedPath = function() {
        localStorage.removeItem('chromadb_path');
        dbPathInput.value = '';
        const clearPathLink = document.getElementById('clear-path-link');
        clearPathLink.style.display = 'none';
        savedPathAlert.classList.add('d-none');
        
        // Show confirmation
        savedPathMessage.textContent = 'Saved path cleared';
        savedPathAlert.classList.remove('d-none');
        savedPathAlert.classList.remove('alert-info');
        savedPathAlert.classList.add('alert-success');
        
        // Auto-hide after 2 seconds
        setTimeout(() => {
            savedPathAlert.classList.add('d-none');
            savedPathAlert.classList.remove('alert-success');
            savedPathAlert.classList.add('alert-info');
        }, 2000);
    };
});