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