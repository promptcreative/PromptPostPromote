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
        
        // Restore scheduler settings from localStorage
        const savedConfig = localStorage.getItem('schedulerConfig');
        if (savedConfig) {
            try {
                const config = JSON.parse(savedConfig);
                const startDateInput = document.getElementById('startDate');
                const endDateInput = document.getElementById('endDate');
                const excludeDatesInput = document.getElementById('excludeDates');
                const instagramLimitInput = document.getElementById('instagramLimit');
                const pinterestLimitInput = document.getElementById('pinterestLimit');
                const strategyInput = document.getElementById('schedulingStrategy');
                const minSpacingInput = document.getElementById('minSpacing');
                
                if (config.start_date && startDateInput) startDateInput.value = config.start_date;
                if (config.end_date && endDateInput) endDateInput.value = config.end_date;
                if (config.exclude_dates && excludeDatesInput) excludeDatesInput.value = config.exclude_dates.join(', ');
                if (config.instagram_limit && instagramLimitInput) instagramLimitInput.value = config.instagram_limit;
                if (config.pinterest_limit && pinterestLimitInput) pinterestLimitInput.value = config.pinterest_limit;
                if (config.strategy && strategyInput) strategyInput.value = config.strategy;
                if (config.min_spacing && minSpacingInput) minSpacingInput.value = config.min_spacing;
            } catch (e) {
                console.error('Failed to restore scheduler config:', e);
            }
        }
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
                            <div class="btn-group">
                                <a href="/export_calendar/${cal.id}" class="btn btn-sm btn-success" title="Export Calendar" download>
                                    <i class="bi bi-download"></i>
                                </a>
                                <button class="btn btn-sm btn-danger delete-calendar-btn" data-calendar-id="${cal.id}" title="Delete Calendar">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
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
    const generateCalendarBtn = document.getElementById('generateCalendarBtn');
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
    
    if (generateCalendarBtn) {
        generateCalendarBtn.addEventListener('click', async function() {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            if (!startDate || !endDate) {
                showMessage('Please select start and end dates', 'warning');
                return;
            }
            
            const excludeDatesInput = document.getElementById('excludeDates').value.trim();
            const excludedDates = excludeDatesInput ? excludeDatesInput.split(',').map(d => d.trim()) : [];
            
            const config = {
                start_date: startDate,
                end_date: endDate,
                exclude_dates: excludedDates,
                instagram_limit: parseInt(document.getElementById('instagramLimit').value),
                pinterest_limit: parseInt(document.getElementById('pinterestLimit').value),
                strategy: document.getElementById('schedulingStrategy').value,
                min_spacing: parseInt(document.getElementById('minSpacing').value)
            };
            
            // Save to localStorage
            localStorage.setItem('schedulerConfig', JSON.stringify(config));
            
            const btn = generateCalendarBtn;
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
            
            try {
                const response = await fetch('/generate_calendar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Display schedule preview modal
                    showSchedulePreview(data);
                    loadImages();
                } else if (response.status === 409) {
                    // Calendar exists - ask for confirmation
                    const error = await response.json();
                    const confirmed = confirm(`${error.message}\n\nClick OK to delete existing slots and generate new calendar, or Cancel to keep existing slots.`);
                    
                    if (confirmed) {
                        // Delete existing slots and regenerate
                        await fetch('/delete_empty_slots', { method: 'POST' });
                        
                        // Retry generation
                        const retryResponse = await fetch('/generate_calendar', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(config)
                        });
                        
                        if (retryResponse.ok) {
                            const data = await retryResponse.json();
                            showSchedulePreview(data);
                            loadImages();
                        } else {
                            throw new Error('Generation failed after deleting slots');
                        }
                    }
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Generation failed');
                }
            } catch (error) {
                showMessage('Calendar generation failed: ' + error.message, 'danger');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
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
                                            <th width="30">
                                                <input type="checkbox" class="form-check-input" id="selectAllEvents${calType}">
                                            </th>
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
                        
                        const checkbox = !event.is_assigned 
                            ? `<input type="checkbox" class="form-check-input event-checkbox" data-event-id="${event.id}" data-event-date="${event.date}">`
                            : `<input type="checkbox" class="form-check-input" disabled>`;
                        
                        html += `
                            <tr class="${event.is_assigned ? 'table-secondary' : ''}">
                                <td>${checkbox}</td>
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
                
                // Add event listeners for checkboxes
                content.querySelectorAll('.event-checkbox').forEach(checkbox => {
                    checkbox.addEventListener('change', updateSelectedEventsCount);
                });
                
                // Add select all functionality for each calendar
                ['AB', 'YP', 'POF'].forEach(calType => {
                    const selectAll = document.getElementById(`selectAllEvents${calType}`);
                    if (selectAll) {
                        selectAll.addEventListener('change', function() {
                            // Find the table containing this checkbox
                            const table = this.closest('table');
                            if (table) {
                                // Only toggle checkboxes within this specific table
                                const checkboxes = table.querySelectorAll('.event-checkbox');
                                checkboxes.forEach(cb => {
                                    cb.checked = this.checked;
                                });
                            }
                            updateSelectedEventsCount();
                        });
                    }
                });
                
                updateSelectedEventsCount();
                modal.show();
                
            } catch (error) {
                showMessage('Failed to load calendar: ' + error.message, 'danger');
            }
        });
    }
    
    function updateSelectedEventsCount() {
        const checkboxes = document.querySelectorAll('.event-checkbox:checked');
        const count = checkboxes.length;
        const badge = document.getElementById('selectedEventsCount');
        if (badge) {
            badge.textContent = `${count} selected`;
            badge.className = count > 0 ? 'badge bg-success' : 'badge bg-primary';
        }
    }
    
    const createFromSelectedBtn = document.getElementById('createFromSelectedBtn');
    if (createFromSelectedBtn) {
        createFromSelectedBtn.addEventListener('click', async function() {
            const checkboxes = document.querySelectorAll('.event-checkbox:checked');
            const eventIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.eventId));
            
            if (eventIds.length === 0) {
                showMessage('Select at least one event', 'warning');
                return;
            }
            
            const config = {
                event_ids: eventIds,
                instagram_limit: parseInt(document.getElementById('instagramLimit').value),
                pinterest_limit: parseInt(document.getElementById('pinterestLimit').value),
                strategy: document.getElementById('schedulingStrategy').value,
                min_spacing: parseInt(document.getElementById('minSpacing').value)
            };
            
            const btn = createFromSelectedBtn;
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Creating...';
            
            try {
                const response = await fetch('/generate_from_selected', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const summary = data.summary;
                    
                    showMessage(`✅ Created ${data.created_count} slots from selected events! (AB:${summary.by_calendar.AB} YP:${summary.by_calendar.YP} POF:${summary.by_calendar.POF})`, 'success');
                    
                    // Close modal and reload
                    const modal = bootstrap.Modal.getInstance(document.getElementById('calendarViewModal'));
                    if (modal) modal.hide();
                    loadImages();
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Generation failed');
                }
            } catch (error) {
                showMessage('Failed to create slots: ' + error.message, 'danger');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
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
    
    function showSchedulePreview(data) {
        const modal = new bootstrap.Modal(document.getElementById('schedulePreviewModal'));
        const content = document.getElementById('schedulePreviewContent');
        const stats = document.getElementById('scheduleStats');
        
        // Update stats
        const summary = data.summary;
        const statsHTML = `<strong>${data.created_count} slots created</strong> - Instagram: ${summary.Instagram || 0}, Pinterest: ${summary.Pinterest || 0} | AB: ${summary.AB || 0}, YP: ${summary.YP || 0}, POF: ${summary.POF || 0}, Optimal: ${summary.Optimal || 0}`;
        stats.innerHTML = statsHTML;
        
        // Build day-by-day schedule
        let html = '';
        data.schedule_by_day.forEach(day => {
            const dateObj = new Date(day.date + 'T00:00:00');
            const formattedDate = dateObj.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            html += `
                <div class="day-block mb-4 p-3 border rounded">
                    <h5 class="mb-3">${formattedDate}</h5>
                    <ul class="list-unstyled mb-0">
            `;
            
            day.slots.forEach(slot => {
                const platformEmoji = slot.platform === 'Instagram' ? '📸' : slot.platform === 'Pinterest' ? '📌' : '📱';
                const calendarBadge = `<span class="badge bg-${slot.calendar_source === 'AB' ? 'primary' : slot.calendar_source === 'YP' ? 'info' : slot.calendar_source === 'POF' ? 'warning' : 'secondary'}">${slot.calendar_source}</span>`;
                
                // Convert 24hr to 12hr format
                const [hours, minutes] = slot.time.split(':');
                const hour = parseInt(hours);
                const ampm = hour >= 12 ? 'PM' : 'AM';
                const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
                const timeFormatted = `${displayHour}:${minutes} ${ampm}`;
                
                html += `
                    <li class="mb-2">
                        <span class="text-muted">${timeFormatted}</span> - 
                        ${platformEmoji} <strong>${slot.platform}</strong> 
                        ${calendarBadge}
                    </li>
                `;
            });
            
            html += `
                    </ul>
                </div>
            `;
        });
        
        content.innerHTML = html;
        
        // Also populate the on-page calendar display
        const onPageDisplay = document.getElementById('generatedCalendarDisplay');
        const onPageStats = document.getElementById('calendarStats');
        const onPageList = document.getElementById('calendarDaysList');
        const onPageTotal = document.getElementById('calendarStatsTotal');
        
        if (onPageDisplay && onPageStats && onPageList && onPageTotal) {
            onPageTotal.textContent = `${data.created_count} slots`;
            onPageStats.innerHTML = `
                <div class="d-flex gap-3 flex-wrap">
                    <span><strong>Instagram:</strong> ${summary.Instagram || 0}</span>
                    <span><strong>Pinterest:</strong> ${summary.Pinterest || 0}</span>
                    <span class="text-muted">|</span>
                    <span class="badge bg-primary">AB: ${summary.AB || 0}</span>
                    <span class="badge bg-info">YP: ${summary.YP || 0}</span>
                    <span class="badge bg-warning">POF: ${summary.POF || 0}</span>
                    <span class="badge bg-secondary">Optimal: ${summary.Optimal || 0}</span>
                </div>
            `;
            onPageList.innerHTML = html;
            onPageDisplay.style.display = 'block';
        }
        
        // Store data for CSV export
        window.currentScheduleData = data;
        
        modal.show();
    }
    
    // Print button handler
    const printScheduleBtn = document.getElementById('printScheduleBtn');
    if (printScheduleBtn) {
        printScheduleBtn.addEventListener('click', function() {
            window.print();
        });
    }
    
    // CSV export button handler
    const exportScheduleCSVBtn = document.getElementById('exportScheduleCSVBtn');
    if (exportScheduleCSVBtn) {
        exportScheduleCSVBtn.addEventListener('click', function() {
            if (!window.currentScheduleData) return;
            
            const data = window.currentScheduleData;
            let csv = 'Date,Time,Platform,Calendar Source\n';
            
            data.schedule_by_day.forEach(day => {
                day.slots.forEach(slot => {
                    csv += `${day.date},${slot.time},${slot.platform},${slot.calendar_source}\n`;
                });
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `schedule_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }
    
    // Bulk delete selected items button handler
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', async function() {
            const selectedIds = getSelectedImageIds();
            
            if (selectedIds.length === 0) {
                showMessage('No items selected', 'warning');
                return;
            }
            
            if (!confirm(`Delete ${selectedIds.length} selected items?`)) {
                return;
            }
            
            const btn = this;
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Deleting...';
            
            try {
                const response = await fetch('/bulk_delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ids: selectedIds })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showMessage(`✅ ${data.message}`, 'success');
                    loadImages();
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Delete failed');
                }
            } catch (error) {
                showMessage('Delete failed: ' + error.message, 'danger');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }
    
    // Delete all empty slots button handler
    const deleteEmptySlotsBtn = document.getElementById('deleteEmptySlotsBtn');
    if (deleteEmptySlotsBtn) {
        deleteEmptySlotsBtn.addEventListener('click', async function() {
            if (!confirm('Delete all empty calendar slots? This will also reset your calendar events so you can regenerate.')) {
                return;
            }
            
            const btn = this;
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Deleting...';
            
            try {
                const response = await fetch('/delete_all_empty_slots', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showMessage(`✅ ${data.message}`, 'success');
                    loadImages();
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Delete failed');
                }
            } catch (error) {
                showMessage('Delete failed: ' + error.message, 'danger');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }
    
    // Reset calendar events button handler
    const resetCalendarEventsBtn = document.getElementById('resetCalendarEventsBtn');
    if (resetCalendarEventsBtn) {
        resetCalendarEventsBtn.addEventListener('click', async function() {
            if (!confirm('Reset all calendar events to unassigned state? This allows you to reuse them in new calendar generations.')) {
                return;
            }
            
            const btn = this;
            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Resetting...';
            
            try {
                const response = await fetch('/reset_calendar_events', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showMessage(`✅ ${data.message}`, 'success');
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Reset failed');
                }
            } catch (error) {
                showMessage('Reset failed: ' + error.message, 'danger');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }
    
    // Schedule Grid functionality
    let selectedEventIds = new Set();
    
    const loadScheduleBtn = document.getElementById('loadScheduleBtn');
    if (loadScheduleBtn) {
        loadScheduleBtn.addEventListener('click', () => {
            selectedEventIds.clear();
            loadScheduleGrid();
        });
    }
    
    // Publer API Test
    const testPublerBtn = document.getElementById('testPublerBtn');
    if (testPublerBtn) {
        testPublerBtn.addEventListener('click', testPublerAPI);
    }
    
    // Push to Publer
    const pushToPublerBtn = document.getElementById('pushToPublerBtn');
    if (pushToPublerBtn) {
        pushToPublerBtn.addEventListener('click', pushSelectedDaysToPubler);
    }
    
    // Export Selected to CSV
    const exportScheduleBtn = document.getElementById('exportScheduleBtn');
    if (exportScheduleBtn) {
        exportScheduleBtn.addEventListener('click', exportSelectedSlotsToCSV);
    }
    
    async function testPublerAPI() {
        const btn = testPublerBtn;
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Testing...';
        
        try {
            const response = await fetch('/api/publer/test');
            const data = await response.json();
            
            let resultHtml = '<div class="modal-body">';
            
            resultHtml += '<h5>Connection Test</h5>';
            if (data.connection.success) {
                resultHtml += '<div class="alert alert-success">✅ Connected successfully!</div>';
                resultHtml += '<pre class="bg-dark text-light p-2 rounded">' + JSON.stringify(data.connection.workspaces, null, 2) + '</pre>';
            } else {
                resultHtml += '<div class="alert alert-danger">❌ Connection failed: ' + data.connection.error + '</div>';
            }
            
            resultHtml += '<h5 class="mt-3">Social Media Accounts</h5>';
            if (data.accounts.success) {
                resultHtml += '<div class="alert alert-success">✅ Found ' + data.accounts.accounts.length + ' connected account(s)</div>';
                resultHtml += '<pre class="bg-dark text-light p-2 rounded" style="max-height: 300px; overflow-y: auto;">' + JSON.stringify(data.accounts.accounts, null, 2) + '</pre>';
            } else {
                resultHtml += '<div class="alert alert-danger">❌ Failed to fetch accounts: ' + data.accounts.error + '</div>';
            }
            
            resultHtml += '<h5 class="mt-3">Existing Drafts</h5>';
            if (data.drafts.success) {
                resultHtml += '<div class="alert alert-info">📄 Found ' + data.drafts.drafts.length + ' draft(s)</div>';
                resultHtml += '<pre class="bg-dark text-light p-2 rounded" style="max-height: 300px; overflow-y: auto;">' + JSON.stringify(data.drafts.drafts, null, 2) + '</pre>';
            } else {
                resultHtml += '<div class="alert alert-danger">❌ Failed to fetch drafts: ' + data.drafts.error + '</div>';
            }
            
            resultHtml += '</div>';
            
            const existingModal = document.getElementById('publerTestModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            const modalHtml = `
                <div class="modal fade" id="publerTestModal" tabindex="-1">
                    <div class="modal-dialog modal-lg modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title"><i class="bi bi-cloud-check"></i> Publer API Test Results</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            ${resultHtml}
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = new bootstrap.Modal(document.getElementById('publerTestModal'));
            modal.show();
            
            document.getElementById('publerTestModal').addEventListener('hidden.bs.modal', function () {
                this.remove();
            });
            
        } catch (error) {
            showMessage('API test failed: ' + error.message, 'danger');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }
    
    async function pushSelectedDaysToPubler() {
        const btn = pushToPublerBtn;
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Pushing to Publer...';
        
        try {
            const selectedDates = Array.from(document.querySelectorAll('.day-checkbox:checked'))
                .map(cb => cb.value);
            
            if (selectedDates.length === 0) {
                showMessage('Please select at least one day', 'warning');
                return;
            }
            
            const response = await fetch('/api/publer/push_days', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dates: selectedDates})
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                showMessage(`✅ Successfully created ${result.draft_count} draft${result.draft_count !== 1 ? 's' : ''} in Publer!`, 'success');
                
                // Show details modal
                let detailsHtml = '<div class="modal-body">';
                detailsHtml += `<div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> Created ${result.draft_count} draft${result.draft_count !== 1 ? 's' : ''} in Publer
                </div>`;
                
                if (result.results && result.results.length > 0) {
                    detailsHtml += '<h6>Details:</h6><ul class="list-group">';
                    for (const r of result.results) {
                        const icon = r.success ? '✅' : '❌';
                        const styleClass = r.success ? 'list-group-item-success' : 'list-group-item-danger';
                        detailsHtml += `<li class="list-group-item ${styleClass}">
                            ${icon} ${r.painting_name} - ${r.platform} (${r.scheduled_time})
                            ${r.error ? `<br><small class="text-danger">${r.error}</small>` : ''}
                        </li>`;
                    }
                    detailsHtml += '</ul>';
                }
                
                detailsHtml += '</div>';
                
                const modalHtml = `
                    <div class="modal fade" id="pushResultModal" tabindex="-1">
                        <div class="modal-dialog modal-lg modal-dialog-scrollable">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title"><i class="bi bi-cloud-upload"></i> Push to Publer Results</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                ${detailsHtml}
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                const existingModal = document.getElementById('pushResultModal');
                if (existingModal) existingModal.remove();
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                const modal = new bootstrap.Modal(document.getElementById('pushResultModal'));
                modal.show();
                
                document.getElementById('pushResultModal').addEventListener('hidden.bs.modal', function () {
                    this.remove();
                });
                
            } else {
                showMessage('Failed to push to Publer: ' + (result.error || 'Unknown error'), 'danger');
            }
            
        } catch (error) {
            showMessage('Push failed: ' + error.message, 'danger');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            updatePushButtonState();
        }
    }
    
    async function loadScheduleGrid() {
        try {
            const startDate = document.getElementById('scheduleStartDate').value;
            const endDate = document.getElementById('scheduleEndDate').value;
            const collectionId = document.getElementById('scheduleCollectionFilter').value;
            
            if (!startDate || !endDate) {
                showMessage('Please select start and end dates', 'warning');
                return;
            }
            
            const params = new URLSearchParams({
                start_date: startDate,
                end_date: endDate
            });
            
            if (collectionId) {
                params.append('collection_id', collectionId);
            }
            
            const response = await fetch(`/api/schedule_grid?${params}`);
            const data = await response.json();
            
            renderScheduleGrid(data);
            await loadUnassignedContent();
            
        } catch (error) {
            showMessage('Failed to load schedule: ' + error.message, 'danger');
        }
    }
    
    function renderScheduleGrid(scheduleData) {
        const gridContainer = document.getElementById('scheduleGrid');
        
        if (!scheduleData || scheduleData.length === 0) {
            gridContainer.innerHTML = '<p class="text-muted">No calendar events in this date range</p>';
            return;
        }
        
        let html = '<div class="schedule-calendar">';
        
        for (const day of scheduleData) {
            const date = new Date(day.date);
            const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
            const dateFormatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            
            html += `
                <div class="schedule-day-card mb-3 border rounded p-3">
                    <h6 class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input day-checkbox" type="checkbox" value="${day.date}" id="day-${day.date}">
                            <label class="form-check-label" for="day-${day.date}">
                                <i class="bi bi-calendar3"></i> ${dayName}, ${dateFormatted}
                            </label>
                        </div>
                    </h6>
                    <div class="row">
            `;
            
            for (const event of day.events) {
                const calendarBadge = getCalendarBadge(event.calendar_type);
                
                const hasAssignments = event.total_assignments > 0;
                const hasFilteredAssignments = event.assignments.length > 0;
                
                const isChecked = selectedEventIds.has(event.event_id);
                
                html += `
                    <div class="col-md-6 mb-3">
                        <div class="event-slot border rounded p-2 ${hasAssignments ? 'bg-light' : ''}" 
                             data-event-id="${event.event_id}">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div class="form-check form-check-inline mb-0">
                                    <input class="form-check-input event-checkbox" type="checkbox" 
                                           ${isChecked ? 'checked' : ''}
                                           data-event-id="${event.event_id}" 
                                           data-day="${day.date}"
                                           id="event-${event.event_id}">
                                    <label class="form-check-label" for="event-${event.event_id}">
                                        <strong>${event.time}</strong>
                                    </label>
                                </div>
                                ${calendarBadge}
                            </div>
                            <div class="text-muted small mb-2">${event.summary || 'Calendar Event'}</div>
                            <div class="assignments mb-2">
                `;
                
                if (event.assignments.length > 0) {
                    for (const assignment of event.assignments) {
                        const platformEmoji = getPlatformEmoji(assignment.platform);
                        html += `
                            <div class="assignment-item d-flex align-items-center gap-2 p-1 bg-white rounded mb-1">
                                <img src="/static/uploads/${assignment.stored_filename}" 
                                     style="width: 30px; height: 30px; object-fit: cover; border-radius: 4px;">
                                <span class="flex-grow-1 small">${platformEmoji} ${assignment.painting_name}</span>
                                <button class="btn btn-sm btn-danger unassign-btn" 
                                        data-assignment-id="${assignment.assignment_id}">
                                    <i class="bi bi-x"></i>
                                </button>
                            </div>
                        `;
                    }
                } else if (hasAssignments) {
                    const hiddenCount = event.total_assignments;
                    html += `<div class="text-muted small fst-italic">
                        ${hiddenCount} assignment${hiddenCount > 1 ? 's' : ''} (filtered out by collection)
                    </div>`;
                } else {
                    html += `<div class="text-muted small fst-italic">Click to assign content</div>`;
                }
                
                html += `
                            </div>
                            <div class="small text-muted mb-2">
                                <i class="bi bi-info-circle"></i> ${event.available_slots} slot${event.available_slots !== 1 ? 's' : ''} available
                            </div>
                            <button class="btn btn-sm btn-outline-primary w-100 assign-content-btn" 
                                    data-event-id="${event.event_id}">
                                <i class="bi bi-plus"></i> Assign Content
                            </button>
                        </div>
                    </div>
                `;
            }
            
            html += `
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        gridContainer.innerHTML = html;
        
        // Add click handlers
        document.querySelectorAll('.assign-content-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const eventId = e.target.closest('.assign-content-btn').dataset.eventId;
                showAssignmentModal(eventId);
            });
        });
        
        document.querySelectorAll('.unassign-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const assignmentId = e.target.closest('.unassign-btn').dataset.assignmentId;
                unassignContent(assignmentId);
            });
        });
        
        // Handle day checkbox changes for Publer push
        document.querySelectorAll('.day-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', updatePushButtonState);
        });
        
        updatePushButtonState();
        attachScheduleCheckboxHandlers();
        updateScheduleActions();
    }
    
    function attachScheduleCheckboxHandlers() {
        document.querySelectorAll('.event-checkbox').forEach(cb => {
            cb.addEventListener('change', () => {
                const eventId = Number(cb.dataset.eventId);
                const day = cb.dataset.day;
                if (cb.checked) {
                    selectedEventIds.add(eventId);
                } else {
                    selectedEventIds.delete(eventId);
                }
                syncDayCheckbox(day);
                updateScheduleActions();
            });
        });

        document.querySelectorAll('.day-checkbox').forEach(cb => {
            cb.addEventListener('change', () => {
                const day = cb.value;
                const childCbs = document.querySelectorAll(`.event-checkbox[data-day="${day}"]`);
                childCbs.forEach(child => {
                    child.checked = cb.checked;
                    const eventId = Number(child.dataset.eventId);
                    if (cb.checked) {
                        selectedEventIds.add(eventId);
                    } else {
                        selectedEventIds.delete(eventId);
                    }
                });
                updateScheduleActions();
            });
        });
    }

    function syncDayCheckbox(day) {
        const dayCb = document.querySelector(`.day-checkbox[value="${day}"]`);
        if (!dayCb) return;
        const children = Array.from(document.querySelectorAll(`.event-checkbox[data-day="${day}"]`));
        const checked = children.filter(cb => cb.checked).length;
        dayCb.checked = checked === children.length && checked > 0;
        dayCb.indeterminate = checked > 0 && checked < children.length;
    }
    
    function updateScheduleActions() {
        const exportBtn = document.getElementById('exportScheduleBtn');
        if (exportBtn) {
            const count = selectedEventIds.size;
            exportBtn.disabled = count === 0;
            const badge = document.getElementById('selectedSlotCount');
            if (badge) {
                badge.textContent = `${count} selected`;
            }
        }
    }
    
    async function exportSelectedSlotsToCSV() {
        if (selectedEventIds.size === 0) return;
        const btn = document.getElementById('exportScheduleBtn');
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Exporting...';
        try {
            const response = await fetch('/schedule/export_csv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_ids: Array.from(selectedEventIds) })
            });
            if (!response.ok) throw new Error('Export failed');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'publer_schedule.csv';
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            showMessage('CSV exported successfully!', 'success');
        } catch (error) {
            showMessage('Export failed: ' + error.message, 'danger');
        } finally {
            btn.disabled = selectedEventIds.size === 0;
            btn.innerHTML = originalHtml;
        }
    }
    
    function updatePushButtonState() {
        const checkboxes = document.querySelectorAll('.day-checkbox');
        const checkedCount = document.querySelectorAll('.day-checkbox:checked').length;
        const pushBtn = document.getElementById('pushToPublerBtn');
        
        if (pushBtn) {
            pushBtn.disabled = checkedCount === 0;
            pushBtn.innerHTML = `<i class="bi bi-cloud-upload"></i> Push ${checkedCount} Day${checkedCount !== 1 ? 's' : ''} to Publer`;
        }
    }
    
    async function loadUnassignedContent() {
        try {
            const collectionId = document.getElementById('scheduleCollectionFilter').value;
            const params = collectionId ? `?collection_id=${collectionId}` : '';
            
            const response = await fetch(`/api/unassigned_images${params}`);
            const images = await response.json();
            
            const container = document.getElementById('unassignedContent');
            
            if (!images || images.length === 0) {
                container.innerHTML = '<p class="text-muted">No unassigned content</p>';
                return;
            }
            
            let html = '<div class="row g-2">';
            for (const img of images) {
                html += `
                    <div class="col-12">
                        <div class="unassigned-item border rounded p-2 d-flex align-items-center gap-2" 
                             data-image-id="${img.id}">
                            <img src="/static/uploads/${img.stored_filename}" 
                                 style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">
                            <div class="flex-grow-1 small">
                                <div><strong>${img.painting_name}</strong></div>
                                <div class="text-muted">${img.status || 'Draft'}</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            html += '</div>';
            
            container.innerHTML = html;
            
        } catch (error) {
            console.error('Failed to load unassigned content:', error);
        }
    }
    
    function showAssignmentModal(eventId) {
        const platforms = ['Instagram', 'Pinterest', 'Facebook'];
        
        const modalHtml = `
            <div class="modal fade" id="assignModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Assign Content to Time Slot</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Select Content</label>
                                <div id="assignModalImages" style="max-height: 300px; overflow-y: auto;">
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Platforms</label>
                                <div class="mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="platformAll">
                                        <label class="form-check-label" for="platformAll">
                                            <strong>All Platforms</strong>
                                        </label>
                                    </div>
                                </div>
                                <div id="platformCheckboxes">
                                    ${platforms.map(p => `
                                        <div class="form-check">
                                            <input class="form-check-input platform-checkbox" type="checkbox" value="${p}" id="platform${p}">
                                            <label class="form-check-label" for="platform${p}">
                                                ${getPlatformEmoji(p)} ${p}
                                            </label>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirmAssignBtn">Assign</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const existingModal = document.getElementById('assignModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('assignModal'));
        
        loadUnassignedImagesForModal();
        
        const platformAllCheckbox = document.getElementById('platformAll');
        const platformCheckboxes = document.querySelectorAll('.platform-checkbox');
        
        platformAllCheckbox.addEventListener('change', () => {
            platformCheckboxes.forEach(cb => cb.checked = platformAllCheckbox.checked);
        });
        
        platformCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                const allChecked = Array.from(platformCheckboxes).every(checkbox => checkbox.checked);
                platformAllCheckbox.checked = allChecked;
            });
        });
        
        document.getElementById('confirmAssignBtn').addEventListener('click', async () => {
            const selectedImage = document.querySelector('input[name="assignImage"]:checked');
            if (!selectedImage) {
                showMessage('Please select an image', 'warning');
                return;
            }
            
            const selectedPlatforms = Array.from(platformCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            if (selectedPlatforms.length === 0) {
                showMessage('Please select at least one platform', 'warning');
                return;
            }
            
            const imageId = selectedImage.value;
            
            await assignContentToEvent(eventId, imageId, selectedPlatforms);
            modal.hide();
            loadScheduleGrid();
        });
        
        modal.show();
    }
    
    async function loadUnassignedImagesForModal() {
        try {
            const response = await fetch('/api/unassigned_images');
            const images = await response.json();
            
            const container = document.getElementById('assignModalImages');
            
            if (!images || images.length === 0) {
                container.innerHTML = '<p class="text-muted">No unassigned images available</p>';
                return;
            }
            
            let html = '<div class="list-group">';
            for (const img of images) {
                html += `
                    <label class="list-group-item d-flex align-items-center gap-2">
                        <input type="radio" name="assignImage" value="${img.id}" class="form-check-input me-2">
                        <img src="/static/uploads/${img.stored_filename}" 
                             style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;">
                        <span>${img.painting_name}</span>
                    </label>
                `;
            }
            html += '</div>';
            
            container.innerHTML = html;
            
        } catch (error) {
            console.error('Failed to load images for modal:', error);
        }
    }
    
    async function assignContentToEvent(eventId, imageId, platforms) {
        try {
            const response = await fetch('/api/assign', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    event_id: eventId,
                    image_id: imageId,
                    platforms: platforms
                })
            });
            
            if (response.ok) {
                const platformList = platforms.join(', ');
                showMessage(`Content assigned to ${platformList}`, 'success');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Assignment failed');
            }
            
        } catch (error) {
            showMessage('Assignment failed: ' + error.message, 'danger');
        }
    }
    
    async function unassignContent(assignmentId) {
        if (!confirm('Remove this assignment?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/assign/${assignmentId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showMessage('Assignment removed', 'success');
                loadScheduleGrid();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Unassign failed');
            }
            
        } catch (error) {
            showMessage('Unassign failed: ' + error.message, 'danger');
        }
    }
    
    function getCalendarBadge(calendarType) {
        const badges = {
            'AB': '<span class="badge bg-primary">AB</span>',
            'YP': '<span class="badge bg-success">YP</span>',
            'POF': '<span class="badge bg-warning text-dark">POF</span>'
        };
        return badges[calendarType] || '';
    }
    
    function getPlatformEmoji(platform) {
        const emojis = {
            'Instagram': '📸',
            'Pinterest': '📌',
            'Facebook': '📘',
            'Etsy': '🛍️'
        };
        return emojis[platform] || '📱';
    }
    
    // Set default dates
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    
    const startDateInput = document.getElementById('scheduleStartDate');
    const endDateInput = document.getElementById('scheduleEndDate');
    
    if (startDateInput && endDateInput) {
        startDateInput.value = today.toISOString().split('T')[0];
        endDateInput.value = nextWeek.toISOString().split('T')[0];
    }
    
    // Populate collection filter
    const scheduleCollectionFilter = document.getElementById('scheduleCollectionFilter');
    if (scheduleCollectionFilter) {
        loadCollections().then(collections => {
            scheduleCollectionFilter.innerHTML = '<option value="">All Collections</option>' +
                collections.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        });
    }
});
