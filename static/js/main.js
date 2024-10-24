document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = imageTable ? imageTable.querySelector('tbody') : null;
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar ? progressBar.querySelector('.progress-bar') : null;
    const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'), {
        keyboard: true,
        backdrop: true
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ... [Previous code remains the same until line 283] ...

    } else if (target.classList.contains('feedback-btn')) {
        console.log('Feedback button clicked');
        const row = target.closest('tr');
        const imageId = row.dataset.imageId;
        
        try {
            const postTitle = row.querySelector('td:nth-child(4)')?.textContent.trim() || '';
            const description = row.querySelector('td:nth-child(5)')?.textContent.trim() || '';
            const keyPoints = row.querySelector('td:nth-child(6)')?.textContent.trim() || '';
            const hashtags = row.querySelector('td:nth-child(7)')?.textContent.trim() || '';
            
            console.log('Content retrieved:', { postTitle, description, keyPoints, hashtags });
            
            if (document.getElementById('feedbackModal')) {
                document.getElementById('generatedTitle').textContent = postTitle;
                document.getElementById('generatedDescription').textContent = description;
                document.getElementById('generatedKeyPoints').textContent = keyPoints;
                document.getElementById('generatedHashtags').textContent = hashtags;
                document.getElementById('feedbackText').value = '';
                
                setupFeedbackButtons(imageId);
                feedbackModal.show();
            } else {
                console.error('Feedback modal element not found');
            }
        } catch (error) {
            console.error('Error showing feedback modal:', error);
            showErrorMessage('Error showing feedback dialog: ' + error.message);
        }

    // ... [Rest of the code remains the same until updateTableContent function] ...

    function updateTableContent(image) {
        if (!image) {
            console.error('No image data provided to updateTableContent');
            return;
        }
        
        const row = document.querySelector(`tr[data-image-id="${image.id}"]`);
        if (row) {
            try {
                row.cells[0].textContent = image.category || '';
                row.cells[2].textContent = image.original_filename || '';
                row.cells[3].textContent = image.post_title || '';
                row.cells[4].textContent = image.description || '';
                row.cells[5].textContent = image.key_points || '';
                row.cells[6].textContent = image.hashtags || '';
                
                const feedbackBtn = row.querySelector('.feedback-btn');
                if (feedbackBtn && (image.description || image.hashtags)) {
                    feedbackBtn.style.display = 'inline-block';
                }
            } catch (error) {
                console.error('Error updating table content:', error);
            }
        } else {
            console.error('Row not found for image ID:', image.id);
        }
    }

    function addImageToTable(image) {
        if (!image || !tableBody) {
            console.error('Invalid image data or table body not found');
            return;
        }
        
        const row = document.createElement('tr');
        row.dataset.imageId = image.id;
        row.innerHTML = `
            <td>${image.category || ''}</td>
            <td>
                <img src="/static/uploads/${image.stored_filename}" 
                     alt="${image.original_filename}"
                     class="img-thumbnail"
                     style="max-width: 100px;"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%23ccc%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23666%22>Error</text></svg>'">
            </td>
            <td>${image.original_filename || ''}</td>
            <td>${image.post_title || ''}</td>
            <td>${image.description || ''}</td>
            <td>${image.key_points || ''}</td>
            <td>${image.hashtags || ''}</td>
            <td>
                <div class="btn-group" role="group">
                    <button type="button" 
                            class="btn btn-sm btn-outline-primary generate-content-btn" 
                            data-bs-toggle="tooltip"
                            title="Generate initial content">
                        <i class="bi bi-lightbulb"></i> Generate
                    </button>
                    <button type="button" 
                            class="btn btn-sm btn-outline-info feedback-btn" 
                            style="display: ${image.description || image.post_title ? 'inline-block' : 'none'}"
                            data-bs-toggle="tooltip"
                            title="Provide feedback and refine content">
                        <i class="bi bi-chat-dots"></i> Feedback
                    </button>
                    <button type="button"
                            class="btn btn-sm btn-outline-danger remove-entry-btn"
                            data-bs-toggle="tooltip"
                            title="Remove this entry">
                        <i class="bi bi-trash"></i> Remove
                    </button>
                </div>
            </td>
        `;
        
        tableBody.insertBefore(row, tableBody.firstChild);
        
        // Initialize tooltips for the new row
        row.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }
});
