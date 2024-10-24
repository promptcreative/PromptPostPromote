document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = imageTable ? imageTable.querySelector('tbody') : null;
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar ? progressBar.querySelector('.progress-bar') : null;
    const feedbackModal = document.getElementById('feedbackModal') ? 
        new bootstrap.Modal(document.getElementById('feedbackModal')) : null;
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Load existing images with retry mechanism
    let retryCount = 0;
    const maxRetries = 3;
    
    function loadImagesWithRetry() {
        loadImages().catch(error => {
            console.error('Error loading images:', error);
            if (retryCount < maxRetries) {
                retryCount++;
                const delay = Math.min(1000 * Math.pow(2, retryCount), 5000);
                setTimeout(loadImagesWithRetry, delay);
            } else {
                showErrorMessage('Failed to load images after multiple attempts. Please refresh the page.');
            }
        });
    }
    
    loadImagesWithRetry();
    
    // Error message display function
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
        const toast = new bootstrap.Toast(document.createElement('div'));
        if (toast.element) {
            toast.element.className = 'toast position-fixed bottom-0 end-0 m-3';
            toast.element.innerHTML = `
                <div class="toast-header bg-success text-white">
                    <strong class="me-auto">Success</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            `;
            document.body.appendChild(toast.element);
            toast.show();
            setTimeout(() => toast.element.remove(), 3000);
        }
    }
    
    // Handle file upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file');
            const files = fileInput ? fileInput.files : [];
            
            if (files.length === 0) {
                showErrorMessage('Please select at least one file to upload');
                return;
            }

            if (progressBar) progressBar.classList.remove('d-none');
            if (progressBarInner) {
                progressBarInner.style.width = '0%';
                progressBarInner.setAttribute('aria-valuenow', 0);
            }
            
            try {
                let completed = 0;
                const totalFiles = files.length;
                
                for (const file of files) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.error || `Upload failed for ${file.name}`);
                    }
                    
                    const data = await response.json();
                    addImageToTable(data);
                    
                    completed++;
                    if (progressBarInner) {
                        const progress = (completed / totalFiles) * 100;
                        progressBarInner.style.width = `${progress}%`;
                        progressBarInner.setAttribute('aria-valuenow', progress);
                    }
                }
                
                showSuccessMessage('Files uploaded successfully');
                this.reset();
                
                setTimeout(() => {
                    if (progressBar) progressBar.classList.add('d-none');
                    if (progressBarInner) progressBarInner.style.width = '0%';
                }, 1000);
            } catch (error) {
                showErrorMessage('Error uploading files: ' + error.message);
                if (progressBar) progressBar.classList.add('d-none');
            }
        });
    }
    
    // Handle export
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            window.location.href = '/export';
        });
    }

    // Handle cell editing
    if (tableBody) {
        tableBody.addEventListener('dblclick', function(e) {
            const cell = e.target.closest('td');
            if (!cell) return;
            
            const row = cell.parentElement;
            if (!row) return;
            
            const columnIndex = Array.from(row.cells).indexOf(cell);
            
            // Make category, post title, description, key points, and hashtags editable
            if (![0, 2, 3, 4, 5].includes(columnIndex)) return;
            
            const currentText = cell.textContent.trim();
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group';
            
            const textarea = document.createElement('textarea');
            textarea.value = currentText;
            textarea.className = 'form-control';
            textarea.style.width = '100%';
            textarea.style.minHeight = [0, 2].includes(columnIndex) ? 'auto' : '60px';
            
            const saveButton = document.createElement('button');
            saveButton.className = 'btn btn-success';
            saveButton.innerHTML = '<i class="bi bi-check"></i> Save';
            saveButton.style.height = 'fit-content';
            
            inputGroup.appendChild(textarea);
            inputGroup.appendChild(saveButton);
            
            const originalContent = cell.innerHTML;
            cell.innerHTML = '';
            cell.appendChild(inputGroup);
            textarea.focus();
            
            async function saveChanges() {
                const newValue = textarea.value.trim();
                if (!newValue) {
                    showErrorMessage('Field cannot be empty');
                    return;
                }
                
                if (newValue === currentText) {
                    cell.innerHTML = originalContent;
                    return;
                }

                const imageId = row.dataset.imageId;
                const field = columnIndex === 0 ? 'category' : 
                            columnIndex === 2 ? 'post_title' :
                            columnIndex === 3 ? 'description' :
                            columnIndex === 4 ? 'key_points' : 'hashtags';
                
                saveButton.disabled = true;
                saveButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';

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

            saveButton.addEventListener('click', saveChanges);
            
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

        // Handle Generate Content, Feedback, and Remove buttons
        tableBody.addEventListener('click', async function(e) {
            const target = e.target.closest('button');
            if (!target) return;
            
            const row = target.closest('tr');
            if (!row) return;

            if (target.classList.contains('generate-content-btn')) {
                const categoryCell = row.cells[0];
                const category = categoryCell ? categoryCell.textContent.trim() : '';
                
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
                        const error = await response.json();
                        throw new Error(error.error || 'Failed to generate content');
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
            } else if (target.classList.contains('feedback-btn') && feedbackModal) {
                const imageId = row.dataset.imageId;
                const postTitle = row.querySelector('td:nth-child(3)')?.textContent || '';
                const description = row.querySelector('td:nth-child(4)')?.textContent || '';
                const keyPoints = row.querySelector('td:nth-child(5)')?.textContent || '';
                const hashtags = row.querySelector('td:nth-child(6)')?.textContent || '';
                
                document.getElementById('generatedTitle').textContent = postTitle;
                document.getElementById('generatedDescription').textContent = description;
                document.getElementById('generatedKeyPoints').textContent = keyPoints;
                document.getElementById('generatedHashtags').textContent = hashtags;
                document.getElementById('feedbackText').value = '';
                
                setupFeedbackButtons(imageId);
                feedbackModal.show();
            } else if (target.classList.contains('remove-entry-btn')) {
                if (confirm('Are you sure you want to remove this entry? This action cannot be undone.')) {
                    const imageId = row.dataset.imageId;
                    target.disabled = true;
                    target.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Removing...';
                    
                    try {
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
            }
        });
    }
    
    function setupFeedbackButtons(imageId) {
        const acceptBtn = document.getElementById('acceptContent');
        const refineBtn = document.getElementById('refineContent');
        const restartBtn = document.getElementById('restartContent');
        
        if (!acceptBtn || !refineBtn || !restartBtn || !feedbackModal) return;
        
        // Remove existing event listeners
        const newAcceptBtn = acceptBtn.cloneNode(true);
        const newRefineBtn = refineBtn.cloneNode(true);
        const newRestartBtn = restartBtn.cloneNode(true);
        
        acceptBtn.parentNode.replaceChild(newAcceptBtn, acceptBtn);
        refineBtn.parentNode.replaceChild(newRefineBtn, refineBtn);
        restartBtn.parentNode.replaceChild(newRestartBtn, restartBtn);
        
        // Add new event listeners
        newAcceptBtn.addEventListener('click', () => {
            feedbackModal.hide();
            const row = document.querySelector(`tr[data-image-id="${imageId}"]`);
            if (row) {
                const feedbackBtn = row.querySelector('.feedback-btn');
                if (feedbackBtn) {
                    feedbackBtn.classList.remove('btn-outline-info');
                    feedbackBtn.classList.add('btn-outline-success');
                }
            }
        });
        
        newRefineBtn.addEventListener('click', async () => {
            const feedbackText = document.getElementById('feedbackText');
            const feedback = feedbackText ? feedbackText.value.trim() : '';
            
            if (!feedback) {
                showErrorMessage('Please provide feedback for refinement');
                return;
            }
            
            try {
                newRefineBtn.disabled = true;
                newRefineBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Refining...';
                
                const response = await fetch(`/refine_content/${imageId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ feedback: feedback })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to refine content');
                }
                
                const refinedImage = await response.json();
                updateTableContent(refinedImage);
                feedbackModal.hide();
                showSuccessMessage('Content refined successfully');
                
            } catch (error) {
                showErrorMessage('Error refining content: ' + error.message);
            } finally {
                newRefineBtn.disabled = false;
                newRefineBtn.innerHTML = '<i class="bi bi-pencil"></i> Refine';
            }
        });
        
        newRestartBtn.addEventListener('click', async () => {
            try {
                newRestartBtn.disabled = true;
                newRestartBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Resetting...';
                
                const response = await fetch(`/reset_content/${imageId}`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to reset content');
                }
                
                const resetImage = await response.json();
                updateTableContent(resetImage);
                feedbackModal.hide();
                
                const row = document.querySelector(`tr[data-image-id="${imageId}"]`);
                if (row) {
                    const feedbackBtn = row.querySelector('.feedback-btn');
                    if (feedbackBtn) {
                        feedbackBtn.classList.remove('btn-outline-success');
                        feedbackBtn.classList.add('btn-outline-info');
                    }
                }
                showSuccessMessage('Content reset successfully');
                
            } catch (error) {
                showErrorMessage('Error resetting content: ' + error.message);
            } finally {
                newRestartBtn.disabled = false;
                newRestartBtn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Delete & Restart';
            }
        });
    }
    
    function updateTableContent(image) {
        if (!image) return;
        
        const row = document.querySelector(`tr[data-image-id="${image.id}"]`);
        if (row) {
            row.cells[0].textContent = image.category || '';
            row.cells[2].textContent = image.post_title || '';
            row.cells[3].textContent = image.description || '';
            row.cells[4].textContent = image.key_points || '';
            row.cells[5].textContent = image.hashtags || '';
            
            const feedbackBtn = row.querySelector('.feedback-btn');
            if (feedbackBtn && (image.description || image.hashtags)) {
                feedbackBtn.style.display = 'inline-block';
            }
        }
    }
    
    async function loadImages() {
        try {
            const response = await fetch('/images');
            if (!response.ok) {
                throw new Error('Failed to load images');
            }
            const images = await response.json();
            if (Array.isArray(images)) {
                images.forEach(addImageToTable);
            }
        } catch (error) {
            throw error;
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
            <td>${image.post_title || ''}</td>
            <td>${image.description || ''}</td>
            <td>${image.key_points || ''}</td>
            <td>${image.hashtags || ''}</td>
            <td>${new Date(image.created_at).toLocaleString()}</td>
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
                            style="display: ${image.description ? 'inline-block' : 'none'}"
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
