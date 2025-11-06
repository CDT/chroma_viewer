// Custom JavaScript for ChromaDB Viewer

function toggleMetadata(docId) {
    const metadataSection = document.getElementById(`metadata-${docId}`);
    const button = event.target.closest('button');

    if (metadataSection.style.display === 'none' || metadataSection.style.display === '') {
        metadataSection.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times"></i> Hide Metadata';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-outline-secondary');
    } else {
        metadataSection.style.display = 'none';
        button.innerHTML = '<i class="fas fa-info-circle"></i> Metadata';
        button.classList.remove('btn-outline-secondary');
        button.classList.add('btn-outline-primary');
    }
}

function toggleEmbedding(docId) {
    const embeddingSection = document.getElementById(`embedding-${docId}`);
    const button = event.target.closest('button');

    if (embeddingSection.style.display === 'none' || embeddingSection.style.display === '') {
        embeddingSection.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times"></i> Hide Embedding';
        button.classList.remove('btn-outline-success');
        button.classList.add('btn-outline-secondary');
    } else {
        embeddingSection.style.display = 'none';
        button.innerHTML = '<i class="fas fa-vector-square"></i> Embedding';
        button.classList.remove('btn-outline-secondary');
        button.classList.add('btn-outline-success');
    }
}

function toggleFullEmbedding(docId) {
    const fullEmbeddingSection = document.getElementById(`full-embedding-${docId}`);
    const toggleText = document.getElementById(`toggle-text-${docId}`);
    const button = event.target.closest('button');

    if (fullEmbeddingSection.style.display === 'none' || fullEmbeddingSection.style.display === '') {
        fullEmbeddingSection.style.display = 'block';
        toggleText.textContent = 'Hide Full Vector';
        button.innerHTML = '<i class="fas fa-compress"></i> <span id="toggle-text-' + docId + '">Hide Full Vector</span>';
    } else {
        fullEmbeddingSection.style.display = 'none';
        toggleText.textContent = 'Show Full Vector';
        button.innerHTML = '<i class="fas fa-expand"></i> <span id="toggle-text-' + docId + '">Show Full Vector</span>';
    }
}

async function disconnectDatabase() {
    const disconnectBtn = document.getElementById('disconnect-btn');
    
    // Show loading state
    disconnectBtn.disabled = true;
    disconnectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Disconnecting...';
    
    try {
        const response = await fetch('/api/disconnect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Redirect to connection page
            window.location.href = '/';
        } else {
            alert('Error: ' + (data.detail || 'Failed to disconnect'));
            // Reset button state
            disconnectBtn.disabled = false;
            disconnectBtn.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
        }
    } catch (error) {
        alert('Network error: ' + error.message);
        // Reset button state
        disconnectBtn.disabled = false;
        disconnectBtn.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
    }
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.classList.contains('alert-danger')) {
            setTimeout(function() {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 300);
            }, 5000);
        }
    });
});