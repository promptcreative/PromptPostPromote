document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = imageTable ? imageTable.querySelector('tbody') : null;
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar ? progressBar.querySelector('.progress-bar') : null;
    const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'));

    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));

    // Load existing images
    async function loadImages() {
        try {
            const response = await fetch('/images');
            if (!response.ok) throw new Error('Failed to load images');
            const images = await response.json();
            if (Array.isArray(images)) {
                images.forEach(addImageToTable);
            }
        } catch (error) {
            showErrorMessage('Error loading images: ' + error.message);
        }
    }

    loadImages();

    function showErrorMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = document.querySelector('.container');
        const imageTable = document.getElementById('imageTable');
        
        if (container) {
            try {
                if (imageTable && imageTable.parentNode === container) {
                    container.insertBefore(alertDiv, imageTable);
                } else {
                    container.appendChild(alertDiv);
                }
            } catch (error) {
                container.appendChild(alertDiv);
            }
            setTimeout(() => alertDiv.remove(), 5000);
        }
    }

    function showSuccessMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = document.querySelector('.container');
        const imageTable = document.getElementById('imageTable');
        
        if (container) {
            try {
                if (imageTable && imageTable.parentNode === container) {
                    container.insertBefore(alertDiv, imageTable);
                } else {
                    container.appendChild(alertDiv);
                }
            } catch (error) {
                container.appendChild(alertDiv);
            }
            setTimeout(() => alertDiv.remove(), 3000);
        }
    }

    // [Rest of the code remains unchanged...]
    [Previous code content from line 52 onwards]
