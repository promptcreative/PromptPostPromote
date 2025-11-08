document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = document.getElementById('imageTableBody');
    const exportBtn = document.getElementById('exportBtn');
    const selectAllCheckbox = document.getElementById('selectAll');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar?.querySelector('.progress-bar');
    
    const calendarImportForm = document.getElementById('calendarImportForm');
    const assignTimesBtn = document.getElementById('assignTimesBtn');
    const batchUpdateBtn = document.getElementById('batchUpdateBtn');
    const generateContentBtn = document.getElementById('generateContentBtn');

    let allImages = [];

    loadImages();
    loadCalendars();
    
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(button => {
        button.addEventListener('shown.bs.tab', function(e) {
            if (e.target.id === 'batch-tab') {
                updateSelectedPreview();
            }
        });
    });

    function showMessage(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 4000);
    }

    async function loadImages() {
        try {
            const response = await fetch('/images');
            const images = await response.json();
            allImages = images;
            tableBody.innerHTML = '';
            images.forEach(addImageToTable);
        } catch (error) {
            showMessage('Error loading images: ' + error.message, 'danger');
        }
    }

    function addImageToTable(image) {
        const row = document.createElement('tr');
        row.dataset.imageId = image.id;
        
        row.innerHTML = `
            <td><input type="checkbox" class="row-select"></td>
            <td><img src="/static/uploads/${image.stored_filename}" class="img-thumbnail" style="width: 60px; height: 60px; object-fit: cover;"></td>
            <td class="editable" data-field="painting_name">${image.painting_name || ''}</td>
            <td class="editable" data-field="platform">${image.platform || ''}</td>
            <td class="editable" data-field="post_subtype">${image.post_subtype || ''}</td>
            <td class="editable" data-field="date">${image.date || ''}</td>
            <td class="editable" data-field="time">${image.time || ''}</td>
            <td class="editable" data-field="status">${image.status || ''}</td>
            <td><span class="badge bg-info">${image.calendar_selection || 'None'}</span></td>
            <td>
                <button class="btn btn-sm btn-primary edit-details-btn" title="Edit Details">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger remove-btn" title="Remove">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file');
            const files = fileInput.files;
            
            if (files.length === 0) return;
            
            if (progressBar) progressBar.classList.remove('d-none');
            if (progressBarInner) progressBarInner.style.width = '0%';
            
            try {
                for (let i = 0; i < files.length; i++) {
                    const formData = new FormData();
                    formData.append('file', files[i]);
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const imageData = await response.json();
                        addImageToTable(imageData);
                    }
                    
                    if (progressBarInner) {
                        const progress = ((i + 1) / files.length) * 100;
                        progressBarInner.style.width = `${progress}%`;
                    }
                }
                
                showMessage('Images uploaded successfully');
                fileInput.value = '';
                setTimeout(() => progressBar?.classList.add('d-none'), 1000);
            } catch (error) {
                showMessage('Upload failed: ' + error.message, 'danger');
                progressBar?.classList.add('d-none');
            }
        });
    }

    if (tableBody) {
        tableBody.addEventListener('dblclick', async function(e) {
            const cell = e.target.closest('td.editable');
            if (!cell) return;
            
            const currentText = cell.textContent.trim();
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control form-control-sm';
            input.value = currentText;
            
            const originalContent = cell.innerHTML;
            cell.innerHTML = '';
            cell.appendChild(input);
            input.focus();
            
            async function saveChanges() {
                const newValue = input.value.trim();
                const row = cell.closest('tr');
                const imageId = row.dataset.imageId;
                const field = cell.dataset.field;
                
                if (newValue !== currentText) {
                    try {
                        const response = await fetch(`/update/${imageId}`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({field, value: newValue})
                        });
                        
                        if (response.ok) {
                            cell.textContent = newValue;
                            showMessage('Updated successfully');
                        } else {
                            throw new Error('Update failed');
                        }
                    } catch (error) {
                        showMessage('Update failed: ' + error.message, 'danger');
                        cell.innerHTML = originalContent;
                    }
                } else {
                    cell.innerHTML = originalContent;
                }
            }
            
            input.addEventListener('blur', saveChanges);
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    saveChanges();
                } else if (e.key === 'Escape') {
                    cell.innerHTML = originalContent;
                }
            });
        });
        
        tableBody.addEventListener('click', async function(e) {
            const row = e.target.closest('tr');
            if (!row) return;
            
            const imageId = row.dataset.imageId;
            
            if (e.target.closest('.remove-btn')) {
                if (confirm('Remove this image?')) {
                    try {
                        const response = await fetch(`/remove_image/${imageId}`, {
                            method: 'POST'
                        });
                        if (response.ok) {
                            row.remove();
                            showMessage('Image removed');
                        }
                    } catch (error) {
                        showMessage('Remove failed: ' + error.message, 'danger');
                    }
                }
            } else if (e.target.closest('.edit-details-btn')) {
                openDetailModal(imageId);
            }
        });
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            document.querySelectorAll('.row-select').forEach(cb => {
                cb.checked = this.checked;
            });
            updateSelectedPreview();
        });
    }
    
    if (tableBody) {
        tableBody.addEventListener('change', function(e) {
            if (e.target.classList.contains('row-select')) {
                updateSelectedPreview();
            }
        });
    }
    
    function updateSelectedPreview() {
        const selectedIds = getSelectedImageIds();
        const selectedCount = document.getElementById('selectedCount');
        const selectedPreview = document.getElementById('selectedPreview');
        
        if (!selectedCount || !selectedPreview) return;
        
        selectedCount.textContent = selectedIds.length;
        
        if (selectedIds.length === 0) {
            selectedPreview.innerHTML = '<p class="text-muted w-100">No items selected. Go to Content tab and check items to select.</p>';
            return;
        }
        
        const selectedImages = allImages.filter(img => selectedIds.includes(img.id));
        
        selectedPreview.innerHTML = selectedImages.map(img => {
            const missingContent = [];
            if (!img.text) missingContent.push('Text');
            if (!img.seo_tags) missingContent.push('SEO Tags');
            if (!img.etsy_description) missingContent.push('Etsy Desc');
            if (!img.pinterest_description) missingContent.push('Pinterest Desc');
            if (!img.instagram_first_comment) missingContent.push('IG Comment');
            
            const statusColor = missingContent.length > 0 ? 'warning' : 'success';
            const statusIcon = missingContent.length > 0 ? 'exclamation-circle' : 'check-circle';
            
            return `
                <div class="card" style="width: 200px;">
                    <img src="/static/uploads/${img.stored_filename}" class="card-img-top" style="height: 150px; object-fit: cover;">
                    <div class="card-body p-2">
                        <p class="card-text small mb-1"><strong>${img.painting_name || 'Untitled'}</strong></p>
                        <p class="small mb-1">${img.platform || 'No platform'}</p>
                        ${missingContent.length > 0 ? 
                            `<p class="small text-${statusColor} mb-0"><i class="bi bi-${statusIcon}"></i> Missing: ${missingContent.join(', ')}</p>` :
                            `<p class="small text-${statusColor} mb-0"><i class="bi bi-${statusIcon}"></i> Complete</p>`
                        }
                    </div>
                </div>
            `;
        }).join('');
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            window.location.href = '/export';
        });
    }

    if (calendarImportForm) {
        calendarImportForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('file', document.getElementById('calendarFile').files[0]);
            formData.append('calendar_type', document.getElementById('calendarType').value);
            formData.append('calendar_name', document.getElementById('calendarType').value + ' Calendar');
            
            try {
                const response = await fetch('/calendar/import', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showMessage(`Calendar imported: ${result.event_count} events`);
                    loadCalendars();
                    calendarImportForm.reset();
                } else {
                    throw new Error('Import failed');
                }
            } catch (error) {
                showMessage('Calendar import failed: ' + error.message, 'danger');
            }
        });
    }

    async function loadCalendars() {
        try {
            const response = await fetch('/calendars');
            const calendars = await response.json();
            
            const calendarList = document.getElementById('calendarList');
            const batchCalendarSelect = document.getElementById('batchCalendarSelect');
            
            if (calendars.length === 0) {
                calendarList.innerHTML = '<p class="text-muted">No calendars loaded</p>';
                batchCalendarSelect.innerHTML = '<option value="">Select calendar...</option>';
                return;
            }
            
            calendarList.innerHTML = calendars.map(cal => `
                <div class="card mb-2">
                    <div class="card-body py-2">
                        <strong>${cal.calendar_name}</strong>
                        <br><small class="text-muted">${cal.event_count} events</small>
                    </div>
                </div>
            `).join('');
            
            batchCalendarSelect.innerHTML = '<option value="">Select calendar...</option>' +
                calendars.map(cal => `<option value="${cal.calendar_type}">${cal.calendar_name}</option>`).join('');
            
        } catch (error) {
            console.error('Error loading calendars:', error);
        }
    }

    if (assignTimesBtn) {
        assignTimesBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            const calendarType = document.getElementById('batchCalendarSelect').value;
            
            if (selectedIds.length === 0) {
                showMessage('Select items first', 'warning');
                return;
            }
            
            if (!calendarType) {
                showMessage('Select a calendar', 'warning');
                return;
            }
            
            try {
                const response = await fetch('/assign_times', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image_ids: selectedIds,
                        calendar_type: calendarType
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showMessage(`Assigned ${result.assigned_count} time slots`);
                    loadImages();
                } else {
                    throw new Error('Assignment failed');
                }
            } catch (error) {
                showMessage('Time assignment failed: ' + error.message, 'danger');
            }
        });
    }

    if (batchUpdateBtn) {
        batchUpdateBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            const field = document.getElementById('batchField').value;
            const value = document.getElementById('batchValue').value;
            
            if (selectedIds.length === 0) {
                showMessage('Select items first', 'warning');
                return;
            }
            
            if (!value) {
                showMessage('Enter a value', 'warning');
                return;
            }
            
            try {
                const response = await fetch('/batch_update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image_ids: selectedIds,
                        updates: {[field]: value}
                    })
                });
                
                if (response.ok) {
                    showMessage('Batch update complete');
                    loadImages();
                } else {
                    throw new Error('Batch update failed');
                }
            } catch (error) {
                showMessage('Batch update failed: ' + error.message, 'danger');
            }
        });
    }

    if (generateContentBtn) {
        generateContentBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            const contentType = document.getElementById('contentType').value;
            
            if (selectedIds.length === 0) {
                showMessage('Select items first', 'warning');
                return;
            }
            
            showMessage('Generating content...', 'info');
            
            for (const imageId of selectedIds) {
                try {
                    await fetch(`/generate_content/${imageId}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({content_type: contentType})
                    });
                } catch (error) {
                    console.error('Content generation failed for ' + imageId, error);
                }
            }
            
            showMessage('Content generated');
            loadImages();
        });
    }

    function getSelectedImageIds() {
        const ids = [];
        document.querySelectorAll('.row-select:checked').forEach(cb => {
            const row = cb.closest('tr');
            ids.push(parseInt(row.dataset.imageId));
        });
        return ids;
    }

    async function openDetailModal(imageId) {
        try {
            const response = await fetch('/images');
            const images = await response.json();
            const image = images.find(img => img.id == imageId);
            
            if (!image) return;
            
            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" data-field="title" value="${image.title || ''}">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Painting Name</label>
                        <input type="text" class="form-control" data-field="painting_name" value="${image.painting_name || ''}">
                    </div>
                    <div class="col-md-12">
                        <label class="form-label">Text/Caption</label>
                        <textarea class="form-control" rows="3" data-field="text">${image.text || ''}</textarea>
                    </div>
                    <div class="col-md-12">
                        <label class="form-label">SEO Tags</label>
                        <textarea class="form-control" rows="2" data-field="seo_tags">${image.seo_tags || ''}</textarea>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Pinterest Description</label>
                        <textarea class="form-control" rows="2" data-field="pinterest_description">${image.pinterest_description || ''}</textarea>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Instagram First Comment</label>
                        <textarea class="form-control" rows="2" data-field="instagram_first_comment">${image.instagram_first_comment || ''}</textarea>
                    </div>
                </div>
            `;
            
            const modal = new bootstrap.Modal(document.getElementById('detailModal'));
            modal.show();
            
            document.getElementById('saveDetailsBtn').onclick = async function() {
                const updates = {};
                modalContent.querySelectorAll('[data-field]').forEach(input => {
                    updates[input.dataset.field] = input.value;
                });
                
                try {
                    await fetch(`/batch_update`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            image_ids: [imageId],
                            updates: updates
                        })
                    });
                    
                    showMessage('Details saved');
                    modal.hide();
                    loadImages();
                } catch (error) {
                    showMessage('Save failed: ' + error.message, 'danger');
                }
            };
        } catch (error) {
            showMessage('Error loading details: ' + error.message, 'danger');
        }
    }
});
