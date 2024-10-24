document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = document.querySelector('#imageTable tbody');
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'));
    
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
                    throw new Error(`Upload failed for ${file.name}`);
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

    // Handle cell editing
    tableBody.addEventListener('dblclick', function(e) {
        const cell = e.target.closest('td');
        if (!cell) return;
        
        const row = cell.parentElement;
        const columnIndex = Array.from(row.cells).indexOf(cell);
        
        // Make category (index 0), description (index 3) and hashtags (index 4) editable
        if (columnIndex !== 0 && columnIndex !== 3 && columnIndex !== 4) return;
        
        const currentText = cell.textContent.trim();
        const input = document.createElement('textarea');
        input.value = currentText;
        input.className = 'form-control';
        input.style.width = '100%';
        input.style.minHeight = '60px';
        
        // For category field, use a regular input instead of textarea
        if (columnIndex === 0) {
            input.style.minHeight = 'auto';
        }
        
        // Replace cell content with input
        const originalContent = cell.innerHTML;
        cell.innerHTML = '';
        cell.appendChild(input);
        input.focus();

        async function saveChanges() {
            const newValue = input.value.trim();
            if (newValue === currentText) {
                cell.innerHTML = originalContent;
                return;
            }

            const imageId = row.dataset.imageId;
            const field = columnIndex === 0 ? 'category' : 
                         columnIndex === 3 ? 'description' : 'hashtags';

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
            } catch (error) {
                alert('Error updating: ' + error.message);
                cell.innerHTML = originalContent;
            }
        }

        // Save on blur or Enter key
        input.addEventListener('blur', saveChanges);
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                input.blur();
            }
            if (e.key === 'Escape') {
                cell.innerHTML = originalContent;
            }
        });
    });

    // Handle Generate Content button click with feedback
    tableBody.addEventListener('click', async function(e) {
        if (e.target.classList.contains('generate-content-btn')) {
            const row = e.target.closest('tr');
            const categoryCell = row.cells[0];
            const category = categoryCell.textContent.trim();
            const imageId = row.dataset.imageId;
            
            if (!category) {
                alert('Please set a category first before generating content');
                return;
            }

            try {
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
                
                // Show feedback modal for the generated content
                const image = result.images.find(img => img.id === parseInt(imageId));
                if (image) {
                    showFeedbackModal(image);
                }

            } catch (error) {
                alert(error.message);
            }
        }
    });
    
    function showFeedbackModal(image) {
        document.getElementById('generatedDescription').textContent = image.description;
        document.getElementById('generatedHashtags').textContent = image.hashtags;
        
        // Set up feedback buttons
        const acceptBtn = document.getElementById('acceptContent');
        const refineBtn = document.getElementById('refineContent');
        const restartBtn = document.getElementById('restartContent');
        const feedbackText = document.getElementById('feedbackText');
        
        // Remove existing event listeners
        acceptBtn.replaceWith(acceptBtn.cloneNode(true));
        refineBtn.replaceWith(refineBtn.cloneNode(true));
        restartBtn.replaceWith(restartBtn.cloneNode(true));
        
        // Add new event listeners
        document.getElementById('acceptContent').addEventListener('click', () => {
            feedbackModal.hide();
            updateTableContent(image);
        });
        
        document.getElementById('refineContent').addEventListener('click', async () => {
            const feedback = feedbackText.value.trim();
            if (!feedback) {
                alert('Please provide feedback for refinement');
                return;
            }
            
            try {
                const response = await fetch(`/refine_content/${image.id}`, {
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
                
            } catch (error) {
                alert('Error refining content: ' + error.message);
            }
        });
        
        document.getElementById('restartContent').addEventListener('click', async () => {
            try {
                const response = await fetch(`/reset_content/${image.id}`, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error('Failed to reset content');
                }
                
                const resetImage = await response.json();
                updateTableContent(resetImage);
                feedbackModal.hide();
                
            } catch (error) {
                alert('Error resetting content: ' + error.message);
            }
        });
        
        feedbackModal.show();
    }
    
    function updateTableContent(image) {
        const row = document.querySelector(`tr[data-image-id="${image.id}"]`);
        if (row) {
            row.querySelector('td:nth-child(4)').textContent = image.description;
            row.querySelector('td:nth-child(5)').textContent = image.hashtags;
        }
    }
    
    async function loadImages() {
        try {
            const response = await fetch('/images');
            const images = await response.json();
            
            images.forEach(image => addImageToTable(image));
        } catch (error) {
            console.error('Error loading images:', error);
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
                <button type="button" 
                        class="btn btn-sm btn-outline-info generate-content-btn" 
                        title="Generate content for all images in '${image.category || 'this'}' category">
                    Generate Content
                </button>
            </td>
        `;
        
        tableBody.insertBefore(row, tableBody.firstChild);
    }
});
