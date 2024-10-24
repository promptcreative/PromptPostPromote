// ... [Previous code remains the same until line 118]

            // Make category, post title, description, key points, and hashtags editable
            if (![0, 2, 3, 4, 5].includes(columnIndex)) return;
            
            const currentText = cell.textContent.trim();
            const inputGroup = document.createElement('div');
            if (inputGroup) inputGroup.className = 'input-group';
            
            const input = document.createElement('textarea');
            if (input) {
                input.value = currentText;
                input.className = 'form-control';
                input.style.width = '100%';
                input.style.minHeight = [0, 2].includes(columnIndex) ? 'auto' : '60px';
            }
            
// ... [Previous code remains the same until line 164]

                    const field = columnIndex === 0 ? 'category' : 
                                columnIndex === 2 ? 'post_title' :
                                columnIndex === 3 ? 'description' :
                                columnIndex === 4 ? 'key_points' : 'hashtags';
                    
// ... [Previous code remains the same until line 273]
            } else if (target.classList.contains('feedback-btn') && feedbackModal) {
                const imageId = row.dataset.imageId;
                const postTitle = row.querySelector('td:nth-child(3)')?.textContent || '';
                const description = row.querySelector('td:nth-child(4)')?.textContent || '';
                const keyPoints = row.querySelector('td:nth-child(5)')?.textContent || '';
                const hashtags = row.querySelector('td:nth-child(6)')?.textContent || '';

// ... [Previous code remains the same until line 511]
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

// ... [Rest of the code remains the same]
