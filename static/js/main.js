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
        document.querySelector('.container').insertBefore(alertDiv, imageTable);
        setTimeout(() => alertDiv.remove(), 5000);
    }

    function showSuccessMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.querySelector('.container').insertBefore(alertDiv, imageTable);
        setTimeout(() => alertDiv.remove(), 3000);
    }

    // Handle file upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file');
            if (!fileInput) return;

            const files = fileInput.files;
            if (files.length === 0) {
                showErrorMessage('Please select at least one file to upload');
                return;
            }

            if (progressBar) progressBar.classList.remove('d-none');
            if (progressBarInner) {
                progressBarInner.style.width = '0%';
                progressBarInner.setAttribute('aria-valuenow', '0');
            }

            try {
                for (const file of files) {
                    const formData = new FormData();
                    formData.append('file', file);

                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`Upload failed for ${file.name}`);
                    }

                    const data = await response.json();
                    addImageToTable(data);
                }

                showSuccessMessage('Files uploaded successfully');
                fileInput.value = '';
                
                if (progressBar) {
                    setTimeout(() => progressBar.classList.add('d-none'), 1000);
                }
            } catch (error) {
                showErrorMessage(error.message);
                if (progressBar) progressBar.classList.add('d-none');
            }
        });
    }

    // Handle export
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            window.location.href = '/export';
        });
    }

    // Handle cell editing
    if (tableBody) {
        tableBody.addEventListener('dblclick', async function(e) {
            const cell = e.target.closest('td');
            if (!cell) return;

            const row = cell.parentElement;
            if (!row) return;

            const columnIndex = Array.from(row.cells).indexOf(cell);
            if (![0, 3, 4, 5, 6].includes(columnIndex)) return;

            const currentText = cell.textContent.trim();
            const textarea = document.createElement('textarea');
            textarea.value = currentText;
            textarea.className = 'form-control';
            textarea.style.width = '100%';
            textarea.style.minHeight = '60px';

            const originalContent = cell.innerHTML;
            cell.innerHTML = '';
            cell.appendChild(textarea);
            textarea.focus();

            async function saveChanges() {
                const newValue = textarea.value.trim();
                if (!newValue) {
                    showErrorMessage('Field cannot be empty');
                    cell.innerHTML = originalContent;
                    return;
                }

                if (newValue === currentText) {
                    cell.innerHTML = originalContent;
                    return;
                }

                const imageId = row.dataset.imageId;
                const field = columnIndex === 0 ? 'category' :
                            columnIndex === 3 ? 'post_title' :
                            columnIndex === 4 ? 'description' :
                            columnIndex === 5 ? 'key_points' : 'hashtags';

                try {
                    const response = await fetch(`/update/${imageId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            field: field,
                            value: newValue
                        })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to update');
                    }

                    cell.textContent = newValue;
                    showSuccessMessage('Content updated successfully');
                } catch (error) {
                    showErrorMessage('Error updating: ' + error.message);
                    cell.innerHTML = originalContent;
                }
            }

            textarea.addEventListener('blur', saveChanges);
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    saveChanges();
                }
                if (e.key === 'Escape') {
                    cell.innerHTML = originalContent;
                }
            });
        });

        // Handle buttons
        tableBody.addEventListener('click', async function(e) {
            const target = e.target.closest('button');
            if (!target) return;

            const row = target.closest('tr');
            if (!row) return;

            const imageId = row.dataset.imageId;

            if (target.classList.contains('generate-content-btn')) {
                const category = row.cells[0].textContent.trim();
                if (!category) {
                    showErrorMessage('Please set a category first before generating content');
                    return;
                }

                try {
                    target.disabled = true;
                    target.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Generating...';

                    const response = await fetch('/generate_category_content', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ category: category })
                    });

                    if (!response.ok) {
                        throw new Error('Failed to generate content');
                    }

                    const result = await response.json();
                    if (result.success) {
                        result.images.forEach(updateTableContent);
                        showSuccessMessage('Content generated successfully');
                    }
                } catch (error) {
                    showErrorMessage('Error generating content: ' + error.message);
                } finally {
                    target.disabled = false;
                    target.innerHTML = '<i class="bi bi-lightbulb"></i> Generate';
                }
            } else if (target.classList.contains('feedback-btn')) {
                const modalElement = document.getElementById('feedbackModal');
                if (!modalElement || !feedbackModal) {
                    showErrorMessage('Feedback modal not found or not initialized');
                    return;
                }

                try {
                    const postTitle = row.cells[3].textContent.trim();
                    const description = row.cells[4].textContent.trim();
                    const keyPoints = row.cells[5].textContent.trim();
                    const hashtags = row.cells[6].textContent.trim();

                    document.getElementById('generatedTitle').textContent = postTitle;
                    document.getElementById('generatedDescription').textContent = description;
                    document.getElementById('generatedKeyPoints').textContent = keyPoints;
                    document.getElementById('generatedHashtags').textContent = hashtags;
                    document.getElementById('feedbackText').value = '';

                    setupFeedbackButtons(imageId);
                    feedbackModal.show();
                } catch (error) {
                    console.error('Error showing feedback modal:', error);
                    showErrorMessage('Error showing feedback dialog: ' + error.message);
                }
            } else if (target.classList.contains('remove-entry-btn')) {
                if (!confirm('Are you sure you want to remove this entry? This action cannot be undone.')) {
                    return;
                }

                try {
                    target.disabled = true;
                    target.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Removing...';

                    const response = await fetch(`/remove_image/${imageId}`, {
                        method: 'POST'
                    });

                    if (!response.ok) {
                        throw new Error('Failed to remove image');
                    }

                    row.remove();
                    showSuccessMessage('Entry removed successfully');
                } catch (error) {
                    showErrorMessage('Error removing entry: ' + error.message);
                    target.disabled = false;
                    target.innerHTML = '<i class="bi bi-trash"></i> Remove';
                }
            }
        });
    }

    function setupFeedbackButtons(imageId) {
        const acceptBtn = document.getElementById('acceptContent');
        const refineBtn = document.getElementById('refineContent');
        const restartBtn = document.getElementById('restartContent');

        if (!acceptBtn || !refineBtn || !restartBtn) {
            throw new Error('Feedback buttons not found');
        }

        acceptBtn.onclick = async function() {
            try {
                feedbackModal.hide();
                const row = document.querySelector(`tr[data-image-id="${imageId}"]`);
                if (!row) return;

                const feedbackBtn = row.querySelector('.feedback-btn');
                if (feedbackBtn) {
                    feedbackBtn.classList.remove('btn-outline-info');
                    feedbackBtn.classList.add('btn-outline-success');
                }
            } catch (error) {
                showErrorMessage('Error accepting content: ' + error.message);
            }
        };

        refineBtn.onclick = async function() {
            const feedbackText = document.getElementById('feedbackText');
            if (!feedbackText) return;

            const feedback = feedbackText.value.trim();
            if (!feedback) {
                showErrorMessage('Please provide feedback for refinement');
                return;
            }

            try {
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Refining...';

                const response = await fetch(`/refine_content/${imageId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ feedback: feedback })
                });

                if (!response.ok) {
                    throw new Error('Failed to refine content');
                }

                const refinedImage = await response.json();
                updateTableContent(refinedImage);
                feedbackModal.hide();
                showSuccessMessage('Content refined successfully');
            } catch (error) {
                showErrorMessage('Error refining content: ' + error.message);
            } finally {
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-pencil"></i> Refine';
            }
        };

        restartBtn.onclick = async function() {
            try {
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Resetting...';

                const response = await fetch(`/reset_content/${imageId}`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Failed to reset content');
                }

                const resetImage = await response.json();
                updateTableContent(resetImage);
                feedbackModal.hide();
                showSuccessMessage('Content reset successfully');
            } catch (error) {
                showErrorMessage('Error resetting content: ' + error.message);
            } finally {
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Delete & Restart';
            }
        };
    }

    function updateTableContent(image) {
        if (!image) return;

        const row = document.querySelector(`tr[data-image-id="${image.id}"]`);
        if (!row) return;

        row.cells[0].textContent = image.category || '';
        row.cells[3].textContent = image.post_title || '';
        row.cells[4].textContent = image.description || '';
        row.cells[5].textContent = image.key_points || '';
        row.cells[6].textContent = image.hashtags || '';

        const feedbackBtn = row.querySelector('.feedback-btn');
        if (feedbackBtn && (image.description || image.post_title)) {
            feedbackBtn.style.display = 'inline-block';
        }
    }

    function addImageToTable(image) {
        if (!image || !tableBody) return;

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
