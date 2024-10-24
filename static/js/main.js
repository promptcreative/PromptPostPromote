document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageTable = document.getElementById('imageTable');
    const tableBody = document.querySelector('#imageTable tbody');
    const exportBtn = document.getElementById('exportBtn');
    
    // Load existing images
    loadImages();
    
    // Handle file upload
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            
            const data = await response.json();
            addImageToTable(data);
            this.reset();
        } catch (error) {
            alert('Error uploading file: ' + error.message);
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
