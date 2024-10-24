document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = document.querySelector('#imageTable tbody');
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    const generateCategoryBtn = document.getElementById('generateCategoryContent');
    
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

    // Handle Generate Content for Category
    generateCategoryBtn.addEventListener('click', async function() {
        const selectedCategory = prompt('Enter category name to generate content for:');
        if (!selectedCategory) return;

        try {
            const response = await fetch('/generate_category_content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ category: selectedCategory })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate content');
            }

            const result = await response.json();
            
            // Update the table with new content
            result.images.forEach(updatedImage => {
                const row = document.querySelector(`tr[data-image-id="${updatedImage.id}"]`);
                if (row) {
                    row.querySelector('td:nth-child(4)').textContent = updatedImage.description;
                    row.querySelector('td:nth-child(5)').textContent = updatedImage.hashtags;
                }
            });

            alert('Content generated successfully for category: ' + selectedCategory);
        } catch (error) {
            alert(error.message);
        }
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
            <td>${image.description}</td>
            <td>${image.hashtags}</td>
            <td>${new Date(image.created_at).toLocaleString()}</td>
        `;
        
        tableBody.insertBefore(row, tableBody.firstChild);
    }
});
