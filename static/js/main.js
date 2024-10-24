// Rest of the existing code remains the same until line 146
            const columnIndex = Array.from(row.cells).indexOf(cell);
            
            // Make only Post Title, Description, Key Details, and Hashtags editable
            if (![3, 4, 5, 6].includes(columnIndex)) return;
            
            const currentText = cell.textContent.trim();
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group';
            
            const textarea = document.createElement('textarea');
            textarea.value = currentText;
            textarea.className = 'form-control';
            textarea.style.width = '100%';
            textarea.style.minHeight = columnIndex === 3 ? 'auto' : '60px';
            
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
                const field = columnIndex === 3 ? 'post_title' :
                            columnIndex === 4 ? 'description' :
                            columnIndex === 5 ? 'key_points' : 'hashtags';
                
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

            // Rest of the event handlers remain the same

// Update the updateTableContent function
    function updateTableContent(image) {
        if (!image) return;
        
        const row = document.querySelector(`tr[data-image-id="${image.id}"]`);
        if (row) {
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
        }
    }

// Update the addImageToTable function
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
