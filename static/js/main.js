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
    let allCollections = [];

    async function initializeApp() {
        await loadCollections();
        await loadImages();
        loadCalendars();
    }
    
    initializeApp();
    
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

    async function loadCollections() {
        try {
            const response = await fetch('/collections');
            const collections = await response.json();
            allCollections = collections;
            updateCollectionSelect();
            return collections;
        } catch (error) {
            console.error('Error loading collections:', error);
            return [];
        }
    }

    function updateCollectionSelect(selectedId = null) {
        const collectionSelect = document.getElementById('collectionSelect');
        if (!collectionSelect) return;
        
        const currentValue = selectedId || collectionSelect.value;
        
        collectionSelect.innerHTML = '<option value="">No Collection</option>';
        allCollections.forEach(collection => {
            const option = document.createElement('option');
            option.value = collection.id;
            option.textContent = `${collection.name} (${collection.image_count} items)`;
            collectionSelect.appendChild(option);
        });
        
        if (currentValue) {
            collectionSelect.value = currentValue;
        }
        
        updateCollectionInfo();
    }
    
    function updateCollectionInfo() {
        const collectionSelect = document.getElementById('collectionSelect');
        const collectionInfo = document.getElementById('collectionInfo');
        const collectionInfoName = document.getElementById('collectionInfoName');
        const collectionInfoDetails = document.getElementById('collectionInfoDetails');
        
        if (!collectionSelect || !collectionInfo) return;
        
        const selectedId = collectionSelect.value;
        
        if (selectedId) {
            const collection = allCollections.find(c => c.id == selectedId);
            if (collection) {
                collectionInfoName.textContent = collection.name;
                const details = [];
                if (collection.materials) details.push(`Materials: ${collection.materials}`);
                if (collection.size) details.push(`Size: ${collection.size}`);
                collectionInfoDetails.textContent = details.join(' | ') || 'No details added yet';
                collectionInfo.classList.remove('d-none');
            } else {
                collectionInfo.classList.add('d-none');
            }
        } else {
            collectionInfo.classList.add('d-none');
        }
    }

    const createCollectionBtn = document.getElementById('createCollectionBtn');
    const newCollectionForm = document.getElementById('newCollectionForm');
    const saveNewCollection = document.getElementById('saveNewCollection');
    const cancelNewCollection = document.getElementById('cancelNewCollection');
    const collectionSelect = document.getElementById('collectionSelect');
    
    // Update collection info when dropdown changes
    if (collectionSelect) {
        collectionSelect.addEventListener('change', updateCollectionInfo);
    }

    if (createCollectionBtn) {
        createCollectionBtn.addEventListener('click', function() {
            newCollectionForm.classList.remove('d-none');
            createCollectionBtn.classList.add('d-none');
        });
    }

    if (cancelNewCollection) {
        cancelNewCollection.addEventListener('click', function() {
            newCollectionForm.classList.add('d-none');
            createCollectionBtn.classList.remove('d-none');
            document.getElementById('newCollectionName').value = '';
            document.getElementById('newCollectionDesc').value = '';
        });
    }

    if (saveNewCollection) {
        saveNewCollection.addEventListener('click', async function() {
            const name = document.getElementById('newCollectionName').value.trim();
            const description = document.getElementById('newCollectionDesc').value.trim();
            const materials = document.getElementById('newCollectionMaterials').value.trim();
            const size = document.getElementById('newCollectionSize').value.trim();
            const artist_note = document.getElementById('newCollectionArtistNote').value.trim();
            
            if (!name) {
                showMessage('Please enter a collection name', 'warning');
                return;
            }
            
            try {
                const response = await fetch('/collections', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name, description, materials, size, artist_note })
                });
                
                if (response.ok) {
                    const newCollection = await response.json();
                    showMessage(`Collection "${name}" created! Ready to upload images.`);
                    
                    // Reload collections and auto-select the new one
                    await loadCollections();
                    updateCollectionSelect(newCollection.id);
                    
                    await loadImages();
                    
                    // Hide form and clear fields
                    newCollectionForm.classList.add('d-none');
                    createCollectionBtn.classList.remove('d-none');
                    document.getElementById('newCollectionName').value = '';
                    document.getElementById('newCollectionDesc').value = '';
                    document.getElementById('newCollectionMaterials').value = '';
                    document.getElementById('newCollectionSize').value = '';
                    document.getElementById('newCollectionArtistNote').value = '';
                } else {
                    showMessage('Failed to create collection', 'danger');
                }
            } catch (error) {
                showMessage('Error creating collection: ' + error.message, 'danger');
            }
        });
    }

    async function loadImages() {
        try {
            const response = await fetch('/images');
            const images = await response.json();
            allImages = images;
            renderGroupedTable(images);
        } catch (error) {
            showMessage('Error loading images: ' + error.message, 'danger');
        }
    }

    function renderGroupedTable(images) {
        tableBody.innerHTML = '';
        
        const grouped = {};
        const noCollection = [];
        
        images.forEach(img => {
            if (img.collection_id) {
                if (!grouped[img.collection_id]) {
                    grouped[img.collection_id] = [];
                }
                grouped[img.collection_id].push(img);
            } else {
                noCollection.push(img);
            }
        });
        
        Object.keys(grouped).forEach(collectionId => {
            const collection = allCollections.find(c => c.id == collectionId);
            const collectionImages = grouped[collectionId];
            
            if (collection) {
                addCollectionHeader(collection, collectionImages.length);
                collectionImages.forEach(img => addImageRow(img, collectionId));
            }
        });
        
        if (noCollection.length > 0) {
            addCollectionHeader({id: 'none', name: 'No Collection', image_count: noCollection.length}, noCollection.length);
            noCollection.forEach(img => addImageRow(img, 'none'));
        }
    }

    function addCollectionHeader(collection, imageCount) {
        const headerRow = document.createElement('tr');
        headerRow.classList.add('collection-header', 'table-secondary');
        headerRow.dataset.collectionId = collection.id;
        
        let templateCount = 0;
        if (collection.mockup_template_ids && Array.isArray(collection.mockup_template_ids)) {
            templateCount = collection.mockup_template_ids.length;
        }
        const templateBadge = templateCount > 0 ? `<span class="badge bg-success ms-2">${templateCount} templates</span>` : '';
        
        headerRow.innerHTML = `
            <td colspan="9" class="py-2">
                <div class="d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center gap-3">
                        <button class="btn btn-sm btn-outline-light toggle-collection">
                            <i class="bi bi-chevron-down"></i>
                        </button>
                        <h6 class="mb-0">
                            <i class="bi bi-folder"></i> ${collection.name}
                            <span class="badge bg-primary ms-2">${imageCount} items</span>
                            ${templateBadge}
                        </h6>
                    </div>
                    <div class="btn-group">
                        ${collection.id !== 'none' ? `
                        <button class="btn btn-sm btn-outline-light" disabled title="Create mockups externally and upload them to your collection">
                            <i class="bi bi-images"></i> Mockup Templates (Coming Soon)
                        </button>
                        ` : ''}
                        <button class="btn btn-sm btn-success select-all-collection" data-collection-id="${collection.id}">
                            <i class="bi bi-check-square"></i> Select All
                        </button>
                        <button class="btn btn-sm btn-info generate-collection" data-collection-id="${collection.id}">
                            <i class="bi bi-stars"></i> Generate AI Content
                        </button>
                    </div>
                </div>
            </td>
        `;
        
        tableBody.appendChild(headerRow);
    }

    function addImageRow(image, collectionId) {
        const row = document.createElement('tr');
        row.classList.add('image-row');
        row.dataset.imageId = image.id;
        row.dataset.collectionGroup = collectionId;
        
        const fileExt = image.stored_filename.split('.').pop().toLowerCase();
        const isVideo = ['mp4', 'mov', 'avi', 'webm'].includes(fileExt);
        
        const mediaHtml = isVideo ? 
            `<video src="/static/uploads/${image.stored_filename}" style="width: 60px; height: 60px; object-fit: cover;"></video>` :
            `<img src="/static/uploads/${image.stored_filename}" class="img-thumbnail" style="width: 60px; height: 60px; object-fit: cover;">`;
        
        const instagramPreview = image.text ? 
            (image.text.length > 60 ? image.text.substring(0, 60) + '...' : image.text) : 
            '<span class="text-muted fst-italic">No content</span>';
        
        const pinterestPreview = image.pinterest_description ? 
            (image.pinterest_description.length > 60 ? image.pinterest_description.substring(0, 60) + '...' : image.pinterest_description) : 
            '<span class="text-muted fst-italic">No content</span>';
        
        row.innerHTML = `
            <td><input type="checkbox" class="row-select"></td>
            <td>${mediaHtml}</td>
            <td class="editable" data-field="painting_name">${image.painting_name || '<span class="text-muted fst-italic">No name</span>'}</td>
            <td class="editable small" data-field="materials">${image.materials || '<span class="text-muted fst-italic">-</span>'}</td>
            <td class="editable small" data-field="size">${image.size || '<span class="text-muted fst-italic">-</span>'}</td>
            <td class="small">${instagramPreview}</td>
            <td class="small">${pinterestPreview}</td>
            <td class="editable" data-field="status">${image.status || ''}</td>
            <td>
                <button class="btn btn-sm btn-success generate-ai-btn" data-image-id="${image.id}" title="Generate AI Content">
                    <i class="bi bi-stars"></i>
                </button>
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

    function addImageToTable(image) {
        loadImages();
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file');
            const collectionSelect = document.getElementById('collectionSelect');
            const files = fileInput.files;
            
            if (files.length === 0) return;
            
            const collectionId = collectionSelect ? collectionSelect.value : '';
            
            if (progressBar) progressBar.classList.remove('d-none');
            if (progressBarInner) progressBarInner.style.width = '0%';
            
            try {
                for (let i = 0; i < files.length; i++) {
                    const formData = new FormData();
                    formData.append('file', files[i]);
                    if (collectionId) {
                        formData.append('collection_id', collectionId);
                    }
                    
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
                
                showMessage('Files uploaded successfully');
                fileInput.value = '';
                await loadCollections();
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
            } else if (e.target.closest('.generate-ai-btn')) {
                const btn = e.target.closest('.generate-ai-btn');
                const originalHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
                
                try {
                    const response = await fetch(`/generate_content/${imageId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ platform: 'all' })
                    });
                    
                    if (response.ok) {
                        showMessage('AI content generated! Refresh to see updates.', 'success');
                        // Reload the table to show updated content
                        setTimeout(() => loadImages(), 1000);
                    } else {
                        const data = await response.json();
                        throw new Error(data.error || 'Generation failed');
                    }
                } catch (error) {
                    showMessage('AI generation failed: ' + error.message, 'danger');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = originalHtml;
                }
            } else if (e.target.closest('.toggle-collection')) {
                const headerRow = e.target.closest('.collection-header');
                const collectionId = headerRow.dataset.collectionId;
                const icon = e.target.querySelector('i') || e.target;
                const rows = document.querySelectorAll(`tr.image-row[data-collection-group="${collectionId}"]`);
                
                rows.forEach(row => {
                    row.classList.toggle('d-none');
                });
                
                if (icon.classList.contains('bi-chevron-down')) {
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-right');
                } else {
                    icon.classList.remove('bi-chevron-right');
                    icon.classList.add('bi-chevron-down');
                }
            } else if (e.target.closest('.select-all-collection')) {
                const btn = e.target.closest('.select-all-collection');
                const collectionId = btn.dataset.collectionId;
                const rows = document.querySelectorAll(`tr.image-row[data-collection-group="${collectionId}"]`);
                
                rows.forEach(row => {
                    const checkbox = row.querySelector('.row-select');
                    if (checkbox) checkbox.checked = true;
                });
                
                updateSelectedPreview();
                showMessage(`Selected all items in collection`);
            } else if (e.target.closest('.generate-collection')) {
                const btn = e.target.closest('.generate-collection');
                const collectionId = btn.dataset.collectionId;
                const rows = document.querySelectorAll(`tr.image-row[data-collection-group="${collectionId}"]`);
                
                const imageIds = [];
                rows.forEach(row => {
                    if (row.dataset.imageId) {
                        imageIds.push(parseInt(row.dataset.imageId));
                    }
                });
                
                if (imageIds.length === 0) {
                    showMessage('No images in this collection', 'warning');
                    return;
                }
                
                showMessage(`Generating AI content for ${imageIds.length} items...`, 'info');
                
                let successCount = 0;
                for (const imageId of imageIds) {
                    try {
                        const response = await fetch(`/generate_content/${imageId}`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({platform: 'all'})
                        });
                        
                        if (response.ok) {
                            successCount++;
                        }
                    } catch (error) {
                        console.error('Content generation failed for ' + imageId, error);
                    }
                }
                
                showMessage(`✅ Generated content for ${successCount}/${imageIds.length} items using Vision AI`);
                loadImages();
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
                if (calendarList) calendarList.innerHTML = '<p class="text-muted">No calendars loaded</p>';
                if (batchCalendarSelect) batchCalendarSelect.innerHTML = '<option value="">Select calendar...</option>';
                return;
            }
            
            if (calendarList) {
                calendarList.innerHTML = calendars.map(cal => `
                    <div class="card mb-2">
                        <div class="card-body py-2 d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${cal.calendar_name}</strong>
                                <br><small class="text-muted">${cal.event_count} events</small>
                            </div>
                            <button class="btn btn-sm btn-danger delete-calendar-btn" data-calendar-id="${cal.id}" title="Delete Calendar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            }
            
            if (batchCalendarSelect) {
                batchCalendarSelect.innerHTML = '<option value="">Select calendar...</option>' +
                    calendars.map(cal => `<option value="${cal.calendar_type}">${cal.calendar_name}</option>`).join('');
            }
            
        } catch (error) {
            console.error('Error loading calendars:', error);
        }
    }

    document.addEventListener('click', async function(e) {
        if (e.target.closest('.delete-calendar-btn')) {
            const btn = e.target.closest('.delete-calendar-btn');
            const calendarId = btn.dataset.calendarId;
            
            if (!confirm('Delete this calendar and all its events? This cannot be undone.')) {
                return;
            }
            
            try {
                const response = await fetch(`/calendar/${calendarId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    showMessage('Calendar deleted successfully');
                    loadCalendars();
                } else {
                    const data = await response.json();
                    throw new Error(data.error || 'Delete failed');
                }
            } catch (error) {
                showMessage('Failed to delete calendar: ' + error.message, 'danger');
            }
        }
    });

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

    const viewCalendarBtn = document.getElementById('viewCalendarBtn');
    const previewScheduleBtn = document.getElementById('previewScheduleBtn');
    const assignTimesSmartBtn = document.getElementById('assignTimesSmartBtn');
    const instagramLimit = document.getElementById('instagramLimit');
    const pinterestLimit = document.getElementById('pinterestLimit');
    const instagramLimitValue = document.getElementById('instagramLimitValue');
    const pinterestLimitValue = document.getElementById('pinterestLimitValue');
    
    if (instagramLimit) {
        instagramLimit.addEventListener('input', function() {
            instagramLimitValue.textContent = this.value;
        });
    }
    
    if (pinterestLimit) {
        pinterestLimit.addEventListener('input', function() {
            pinterestLimitValue.textContent = this.value;
        });
    }
    
    if (viewCalendarBtn) {
        viewCalendarBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/calendar_events_all');
                if (!response.ok) throw new Error('Failed to load calendar');
                
                const data = await response.json();
                
                const modal = new bootstrap.Modal(document.getElementById('calendarViewModal'));
                const content = document.getElementById('calendarViewContent');
                
                let html = '';
                
                ['AB', 'YP', 'POF'].forEach(calType => {
                    const cal = data[calType];
                    if (!cal.calendar_name) {
                        html += `
                            <div class="alert alert-warning">
                                <strong>${calType}</strong> calendar not imported yet
                            </div>
                        `;
                        return;
                    }
                    
                    html += `
                        <div class="mb-4">
                            <h5 class="border-bottom pb-2">
                                <span class="badge bg-${calType === 'AB' ? 'primary' : calType === 'YP' ? 'info' : 'secondary'}">${calType}</span>
                                ${cal.calendar_name}
                                <small class="text-muted">
                                    (${cal.total_events} total, 
                                    <span class="text-success">${cal.available} available</span>, 
                                    <span class="text-warning">${cal.assigned} assigned</span>)
                                </small>
                            </h5>
                            <div class="table-responsive">
                                <table class="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Time</th>
                                            <th>Event</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                    `;
                    
                    cal.events.forEach(event => {
                        const statusBadge = event.is_assigned 
                            ? `<span class="badge bg-warning">Assigned (${event.assigned_platform})</span>`
                            : `<span class="badge bg-success">Available</span>`;
                        
                        html += `
                            <tr class="${event.is_assigned ? 'table-secondary' : ''}">
                                <td>${event.date}</td>
                                <td><strong>${event.time}</strong></td>
                                <td>${event.summary || 'Event'}</td>
                                <td>${statusBadge}</td>
                            </tr>
                        `;
                    });
                    
                    html += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                });
                
                content.innerHTML = html;
                modal.show();
                
            } catch (error) {
                showMessage('Failed to load calendar: ' + error.message, 'danger');
            }
        });
    }
    
    if (previewScheduleBtn) {
        previewScheduleBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            
            if (selectedIds.length === 0) {
                showMessage('Select items first', 'warning');
                return;
            }
            
            const config = {
                instagram_limit: parseInt(document.getElementById('instagramLimit').value),
                pinterest_limit: parseInt(document.getElementById('pinterestLimit').value),
                strategy: document.getElementById('schedulingStrategy').value,
                min_spacing: parseInt(document.getElementById('minSpacing').value),
                preview: true
            };
            
            try {
                const response = await fetch('/assign_times_smart', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image_ids: selectedIds,
                        ...config
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const result = data.result;
                    
                    let message = `📅 Schedule Preview:\n\n`;
                    message += `✅ ${result.summary.total_assigned} will be scheduled\n`;
                    message += `❌ ${result.summary.total_unassigned} couldn't fit\n\n`;
                    message += `📊 By Calendar:\n`;
                    message += `  AB: ${result.summary.by_calendar.AB}\n`;
                    message += `  YP: ${result.summary.by_calendar.YP}\n`;
                    message += `  POF: ${result.summary.by_calendar.POF}\n\n`;
                    message += `📱 By Platform:\n`;
                    message += `  Instagram: ${result.summary.by_platform.Instagram}\n`;
                    message += `  Pinterest: ${result.summary.by_platform.Pinterest}`;
                    
                    alert(message);
                } else {
                    throw new Error('Preview failed');
                }
            } catch (error) {
                showMessage('Preview failed: ' + error.message, 'danger');
            }
        });
    }
    
    if (assignTimesSmartBtn) {
        assignTimesSmartBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            
            if (selectedIds.length === 0) {
                showMessage('Select items first', 'warning');
                return;
            }
            
            const config = {
                instagram_limit: parseInt(document.getElementById('instagramLimit').value),
                pinterest_limit: parseInt(document.getElementById('pinterestLimit').value),
                strategy: document.getElementById('schedulingStrategy').value,
                min_spacing: parseInt(document.getElementById('minSpacing').value),
                preview: false
            };
            
            try {
                const response = await fetch('/assign_times_smart', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image_ids: selectedIds,
                        ...config
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const result = data.result;
                    
                    showMessage(`✅ Smart Schedule Complete! ${result.summary.total_assigned} items scheduled (AB:${result.summary.by_calendar.AB} YP:${result.summary.by_calendar.YP} POF:${result.summary.by_calendar.POF})`, 'success');
                    loadImages();
                } else {
                    throw new Error('Smart scheduling failed');
                }
            } catch (error) {
                showMessage('Smart scheduling failed: ' + error.message, 'danger');
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
            const platform = document.getElementById('aiPlatform').value;
            
            if (selectedIds.length === 0) {
                showMessage('Select items first', 'warning');
                return;
            }
            
            const platformNames = {
                'all': 'ALL platforms',
                'instagram': 'Instagram',
                'pinterest': 'Pinterest',
                'etsy': 'Etsy'
            };
            
            showMessage(`Analyzing ${selectedIds.length} image(s) with Vision AI for ${platformNames[platform]}...`, 'info');
            
            let successCount = 0;
            for (const imageId of selectedIds) {
                try {
                    const response = await fetch(`/generate_content/${imageId}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({platform: platform})
                    });
                    
                    if (response.ok) {
                        successCount++;
                    }
                } catch (error) {
                    console.error('Content generation failed for ' + imageId, error);
                }
            }
            
            showMessage(`✅ Generated ${platformNames[platform]} content for ${successCount} item(s) using Vision AI`);
            loadImages();
            updateSelectedPreview();
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
                    <div class="col-md-6">
                        <label class="form-label">Size</label>
                        <input type="text" class="form-control" data-field="size" value="${image.size || ''}" placeholder="e.g., 18x24x1">
                    </div>
                    <div class="col-md-12">
                        <label class="form-label">Materials</label>
                        <input type="text" class="form-control" data-field="materials" value="${image.materials || ''}" placeholder="e.g., Acrylic Mixed Media, Acrylic pour">
                    </div>
                    <div class="col-md-12">
                        <label class="form-label">Artist Note</label>
                        <textarea class="form-control" rows="2" data-field="artist_note" placeholder="Personal story or context (e.g., 'Happy accident while experimenting...')">${image.artist_note || ''}</textarea>
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

    let currentCollectionForTemplates = null;
    let availableTemplates = [];
    let selectedTemplateIds = [];

    document.addEventListener('click', async function(e) {
        if (e.target.closest('.select-mockup-templates')) {
            const button = e.target.closest('.select-mockup-templates');
            currentCollectionForTemplates = button.dataset.collectionId;
            
            const collection = allCollections.find(c => c.id == currentCollectionForTemplates);
            if (!collection) return;
            
            selectedTemplateIds = (collection.mockup_template_ids && Array.isArray(collection.mockup_template_ids)) 
                ? collection.mockup_template_ids 
                : [];
            
            const modal = new bootstrap.Modal(document.getElementById('mockupTemplateModal'));
            modal.show();
            
            await loadMockupTemplates();
        }
    });

    async function loadMockupTemplates() {
        const templateGrid = document.getElementById('templateGrid');
        templateGrid.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"></div></div>';
        
        try {
            const response = await fetch('/mockup-templates');
            if (!response.ok) throw new Error('Failed to load templates');
            
            const data = await response.json();
            availableTemplates = data.templates;
            
            templateGrid.innerHTML = availableTemplates.map(template => {
                const isSelected = selectedTemplateIds.includes(template.id);
                return `
                    <div class="col-md-3">
                        <div class="card template-card ${isSelected ? 'border-primary' : ''}" data-template-id="${template.id}" style="cursor: pointer;">
                            <img src="${template.thumbnail}" class="card-img-top" alt="${template.name}" style="height: 200px; object-fit: cover;">
                            <div class="card-body">
                                <div class="form-check">
                                    <input class="form-check-input template-checkbox" type="checkbox" value="${template.id}" ${isSelected ? 'checked' : ''}>
                                    <label class="form-check-label">
                                        <strong>${template.name}</strong>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            document.querySelectorAll('.template-card').forEach(card => {
                card.addEventListener('click', function(e) {
                    if (e.target.type !== 'checkbox') {
                        const checkbox = this.querySelector('.template-checkbox');
                        checkbox.checked = !checkbox.checked;
                        this.classList.toggle('border-primary');
                    } else {
                        this.classList.toggle('border-primary');
                    }
                });
            });
            
        } catch (error) {
            showMessage('Error loading templates: ' + error.message, 'danger');
            templateGrid.innerHTML = '<div class="col-12"><p class="text-danger">Failed to load templates</p></div>';
        }
    }

    const saveTemplatesBtn = document.getElementById('saveTemplatesBtn');
    if (saveTemplatesBtn) {
        saveTemplatesBtn.addEventListener('click', async function() {
            const checkedBoxes = document.querySelectorAll('.template-checkbox:checked');
            const selectedIds = Array.from(checkedBoxes).map(cb => cb.value);
            
            try {
                const response = await fetch(`/collections/${currentCollectionForTemplates}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        mockup_template_ids: selectedIds
                    })
                });
                
                if (response.ok) {
                    showMessage(`${selectedIds.length} templates saved to collection`);
                    bootstrap.Modal.getInstance(document.getElementById('mockupTemplateModal')).hide();
                    await loadCollections();
                    loadImages();
                } else {
                    throw new Error('Failed to save templates');
                }
            } catch (error) {
                showMessage('Error saving templates: ' + error.message, 'danger');
            }
        });
    }

    const generateMockupsBtn = document.getElementById('generateMockupsBtn');
    if (generateMockupsBtn) {
        generateMockupsBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            
            if (selectedIds.length === 0) {
                showMessage('Select images first', 'warning');
                return;
            }
            
            try {
                const images = allImages.filter(img => selectedIds.includes(img.id));
                let successCount = 0;
                let errorCount = 0;
                
                showMessage(`Generating mockups for ${selectedIds.length} images...`, 'info');
                
                for (const imageId of selectedIds) {
                    const image = images.find(img => img.id === imageId);
                    if (!image || !image.collection_id) {
                        showMessage(`Image ${imageId} has no collection, skipping`, 'warning');
                        errorCount++;
                        continue;
                    }
                    
                    const collection = allCollections.find(c => c.id == image.collection_id);
                    if (!collection || !collection.mockup_template_ids) {
                        showMessage(`Collection has no templates, skipping image ${imageId}`, 'warning');
                        errorCount++;
                        continue;
                    }
                    
                    try {
                        const response = await fetch('/generate-mockups', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                image_id: imageId
                            })
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            successCount++;
                            showMessage(`Generated ${result.mockups.length} mockups for image ${imageId}`, 'success');
                        } else {
                            throw new Error('Mockup generation failed');
                        }
                    } catch (error) {
                        errorCount++;
                        showMessage(`Error generating mockups for image ${imageId}: ${error.message}`, 'danger');
                    }
                }
                
                showMessage(`Mockup generation complete: ${successCount} successful, ${errorCount} failed`, successCount > 0 ? 'success' : 'warning');
                loadImages();
                
            } catch (error) {
                showMessage('Mockup generation error: ' + error.message, 'danger');
            }
        });
    }

    const generateVideoBtn = document.getElementById('generateVideoBtn');
    if (generateVideoBtn) {
        generateVideoBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            const motionPrompt = document.getElementById('videoPrompt').value;
            
            if (selectedIds.length === 0) {
                showMessage('Select an image first', 'warning');
                return;
            }
            
            if (selectedIds.length > 1) {
                showMessage('Select only ONE image for video generation', 'warning');
                return;
            }
            
            if (!motionPrompt) {
                showMessage('Enter a motion prompt (e.g., "gentle camera pan")', 'warning');
                return;
            }
            
            try {
                const imageId = selectedIds[0];
                showMessage('Starting video generation with Pika AI...', 'info');
                
                const response = await fetch('/generate-video', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image_id: imageId,
                        motion_prompt: motionPrompt
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showMessage(`Video generation started! Job ID: ${result.job_id}. Polling for completion...`, 'info');
                    
                    pollVideoStatus(result.job_id, imageId);
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Video generation failed');
                }
            } catch (error) {
                showMessage('Video generation error: ' + error.message, 'danger');
            }
        });
    }

    async function pollVideoStatus(jobId, imageId) {
        const maxAttempts = 60;
        let attempts = 0;
        
        const poll = async () => {
            try {
                const response = await fetch(`/video-status/${jobId}`);
                const result = await response.json();
                
                if (result.status === 'COMPLETED') {
                    showMessage(`Video generation complete! Video saved for image ${imageId}`, 'success');
                    loadImages();
                } else if (result.status === 'FAILED') {
                    showMessage(`Video generation failed: ${result.error || 'Unknown error'}`, 'danger');
                } else if (result.status === 'IN_PROGRESS' || result.status === 'PENDING') {
                    attempts++;
                    if (attempts < maxAttempts) {
                        setTimeout(poll, 5000);
                    } else {
                        showMessage('Video generation timeout - check back later', 'warning');
                    }
                }
            } catch (error) {
                showMessage('Error checking video status: ' + error.message, 'danger');
            }
        };
        
        poll();
    }
});
