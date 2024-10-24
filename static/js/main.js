document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = document.querySelector('#imageTable tbody');
    const exportBtn = document.getElementById('exportBtn');
    const progressBar = document.querySelector('#uploadProgress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    
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
        row.innerHTML = `
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
