document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = document.querySelector('#imageTable tbody');
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'));
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Load existing images
    loadImages();
    
    // Handle file upload
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const files = document.getElementById('file').files;
        if (files.length === 0) return;

        progressBar.classList.remove('d-none');
        progressBarInner.style.width = '0%';
        
        try {
            let completed = 0;
            const totalFiles = files.length;
            
            for (let file of files) {
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
                const progress = (completed / totalFiles) * 100;
                progressBarInner.style.width = `${progress}%`;
                progressBarInner.setAttribute('aria-valuenow', progress);
            }
            
            this.reset();
            setTimeout(() => {
                progressBar.classList.add('d-none');
                progressBarInner.style.width = '0%';
            }, 1000);
        } catch (error) {
            alert('Error uploading files: ' + error.message);
            progressBar.classList.add('d-none');
        }
    });
    
    // Handle export
    exportBtn.addEventListener('click', function() {
        window.location.href = '/export';
    });

    // Handle cell editing with Save button
    tableBody.addEventListener('dblclick', function(e) {
        const cell = e.target.closest('td');
        if (!cell) return;
        
        const row = cell.parentElement;
        const columnIndex = Array.from(row.cells).indexOf(cell);
        
        // Make category (index 0), description (index 3) and hashtags (index 4) editable
        if (columnIndex !== 0 && columnIndex !== 3 && columnIndex !== 4) return;
        
        const currentText = cell.textContent.trim();
        const inputGroup = document.createElement('div');
        inputGroup.className = 'input-group';
        
        const input = document.createElement('textarea');
        input.value = currentText;
        input.className = 'form-control';
        input.style.width = '100%';
        input.style.minHeight = '60px';
        
        // For category field, use a regular input instead of textarea
        if (columnIndex === 0) {
            input.style.minHeight = 'auto';
        }
        
        const saveButton = document.createElement('button');
        saveButton.className = 'btn btn-success';
        saveButton.innerHTML = '<i class="bi bi-check"></i> Save';
        saveButton.style.height = 'fit-content';
        
        inputGroup.appendChild(input);
        inputGroup.appendChild(saveButton);
        
        // Replace cell content with input group
        const originalContent = cell.innerHTML;
        cell.innerHTML = '';
        cell.appendChild(inputGroup);
        input.focus();

        async function saveChanges() {
            const newValue = input.value.trim();
            if (!newValue) {
                alert('Field cannot be empty');
                return;
            }
            
            if (newValue === currentText) {
                cell.innerHTML = originalContent;
                return;
            }

            const imageId = row.dataset.imageId;
            const field = columnIndex === 0 ? 'category' : 
                         columnIndex === 3 ? 'description' : 'hashtags';
            
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
                
                // Show success message
                const toast = new bootstrap.Toast(document.createElement('div'));
                toast.element.className = 'toast position-fixed bottom-0 end-0 m-3';
                toast.element.innerHTML = `
                    <div class="toast-header bg-success text-white">
                        <strong class="me-auto">Success</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        Content updated successfully
                    </div>
                `;
                document.body.appendChild(toast.element);
                toast.show();
                setTimeout(() => toast.element.remove(), 3000);
                
            } catch (error) {
                alert('Error updating: ' + error.message);
                cell.innerHTML = originalContent;
            }
        }

        saveButton.addEventListener('click', saveChanges);
        input.addEventListener('keydown', function(e) {
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
        const target = e.target;
        const row = target.closest('tr');
        if (!row) return;

        if (target.classList.contains('generate-content-btn')) {
            const categoryCell = row.cells[0];
            const category = categoryCell.textContent.trim();
            const imageId = row.dataset.imageId;
            
            if (!category) {
                alert('Please set a category first before generating content');
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
                    result.images.forEach(img => {
                        updateTableContent(img);
                        // Show the feedback button after generating content
                        const imgRow = document.querySelector(`tr[data-image-id="${img.id}"]`);
                        if (imgRow) {
                            const feedbackBtn = imgRow.querySelector('.feedback-btn');
                            if (feedbackBtn) {
                                feedbackBtn.style.display = 'inline-block';
                            }
                        }
                    });
                }
            } catch (error) {
                alert('Error generating content: ' + error.message);
            } finally {
                target.disabled = false;
                target.innerHTML = '<i class="bi bi-lightbulb"></i> Generate Content';
            }
        } else if (target.classList.contains('feedback-btn')) {
            const imageId = row.dataset.imageId;
            const description = row.querySelector('td:nth-child(4)').textContent;
            const hashtags = row.querySelector('td:nth-child(5)').textContent;
            
            // Show feedback modal
            document.getElementById('generatedDescription').textContent = description;
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
                    
                    // Show success message
                    const toast = new bootstrap.Toast(document.createElement('div'));
                    toast.element.className = 'toast position-fixed bottom-0 end-0 m-3';
                    toast.element.innerHTML = `
                        <div class="toast-header bg-success text-white">
                            <strong class="me-auto">Success</strong>
                            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                        </div>
                        <div class="toast-body">
                            Entry removed successfully
                        </div>
                    `;
                    document.body.appendChild(toast.element);
                    toast.show();
                    setTimeout(() => toast.element.remove(), 3000);
                    
                } catch (error) {
                    alert('Error removing entry: ' + error.message);
                    target.disabled = false;
                    target.innerHTML = '<i class="bi bi-trash"></i> Remove';
                }
            }
        }
    });
    
    function setupFeedbackButtons(imageId) {
        const acceptBtn = document.getElementById('acceptContent');
        const refineBtn = document.getElementById('refineContent');
        const restartBtn = document.getElementById('restartContent');
        
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
            // Update UI to show content is accepted
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
            const feedback = document.getElementById('feedbackText').value.trim();
            if (!feedback) {
                alert('Please provide feedback for refinement');
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
                
                // Show success message
                const toast = new bootstrap.Toast(document.createElement('div'));
                toast.element.className = 'toast position-fixed bottom-0 end-0 m-3';
                toast.element.innerHTML = `
                    <div class="toast-header bg-success text-white">
                        <strong class="me-auto">Success</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        Content refined successfully
                    </div>
                `;
                document.body.appendChild(toast.element);
                toast.show();
                setTimeout(() => toast.element.remove(), 3000);
                
            } catch (error) {
                alert('Error refining content: ' + error.message);
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
                    let errorMessage = 'Failed to reset content';
                    
                    // Handle specific error cases
                    switch (error.code) {
                        case 'NOT_FOUND':
                            errorMessage = 'Image not found';
                            break;
                        case 'NO_CONTENT':
                            errorMessage = 'No content to reset';
                            break;
                        case 'NO_CATEGORY':
                            errorMessage = 'Please set a category before resetting content';
                            break;
                        case 'RATE_LIMIT':
                            errorMessage = 'Rate limit exceeded. Please try again later';
                            break;
                        default:
                            errorMessage = error.error || errorMessage;
                    }
                    throw new Error(errorMessage);
                }
                
                const resetImage = await response.json();
                if (resetImage.success) {
                    updateTableContent(resetImage);
                    feedbackModal.hide();
                    
                    // Reset feedback button style
                    const row = document.querySelector(`tr[data-image-id="${imageId}"]`);
                    if (row) {
                        const feedbackBtn = row.querySelector('.feedback-btn');
                        if (feedbackBtn) {
                            feedbackBtn.classList.remove('btn-outline-success');
                            feedbackBtn.classList.add('btn-outline-info');
                        }
                    }
                    
                    // Show success message
                    const toast = new bootstrap.Toast(document.createElement('div'));
                    toast.element.className = 'toast position-fixed bottom-0 end-0 m-3';
                    toast.element.innerHTML = `
                        <div class="toast-header bg-success text-white">
                            <strong class="me-auto">Success</strong>
                            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                        </div>
                        <div class="toast-body">
                            Content reset successfully
                        </div>
                    `;
                    document.body.appendChild(toast.element);
                    toast.show();
                    setTimeout(() => toast.element.remove(), 3000);
                }
            } catch (error) {
                alert(error.message);
            } finally {
                newRestartBtn.disabled = false;
                newRestartBtn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Delete & Restart';
            }
        });
    }
    
    function updateTableContent(image) {
        const row = document.querySelector(`tr[data-image-id="${image.id}"]`);
        if (row) {
            // Update description and hashtags
            const descriptionCell = row.querySelector('td:nth-child(4)');
            const hashtagsCell = row.querySelector('td:nth-child(5)');
            
            if (descriptionCell && hashtagsCell) {
                descriptionCell.textContent = image.description || '';
                hashtagsCell.textContent = image.hashtags || '';
            }
            
            // Show feedback button if content exists
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
                const error = await response.json();
                throw new Error(error.error || 'Failed to load images');
            }
            const images = await response.json();
            images.forEach(image => addImageToTable(image));
        } catch (error) {
            console.error('Error loading images:', error);
            alert('Failed to load images. Please refresh the page.');
        }
    }
    
    function addImageToTable(image) {
        const row = document.createElement('tr');
        row.dataset.imageId = image.id;
        row.innerHTML = `
            <td>${image.category || ''}</td>
            <td>
                <img src="/static/uploads/${image.stored_filename}" 
                     alt="${image.original_filename}"
                     class="img-thumbnail"
                     style="max-width: 100px;">
            </td>
            <td>${image.original_filename}</td>
            <td>${image.description || ''}</td>
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
        
        // Reinitialize tooltips for the new row
        const tooltips = row.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));
    }
});
