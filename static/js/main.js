document.addEventListener('DOMContentLoaded', function() {
    // ... [Previous code until line 244 remains unchanged]

    } else if (target.classList.contains('feedback-btn')) {
        const modalElement = document.getElementById('feedbackModal');
        if (!modalElement) {
            showErrorMessage('Feedback modal not found');
            return;
        }

        if (!feedbackModal) {
            showErrorMessage('Modal initialization failed');
            return;
        }

        try {
            const row = target.closest('tr');
            if (!row) {
                throw new Error('Row not found');
            }

            const imageId = row.dataset.imageId;
            if (!imageId) {
                throw new Error('Image ID not found');
            }

            // Safely get cell contents with error handling
            const postTitle = row.cells[3]?.textContent?.trim() || '';
            const description = row.cells[4]?.textContent?.trim() || '';
            const keyPoints = row.cells[5]?.textContent?.trim() || '';
            const hashtags = row.cells[6]?.textContent?.trim() || '';

            // Update modal content with null checks
            const titleElement = document.getElementById('generatedTitle');
            const descriptionElement = document.getElementById('generatedDescription');
            const keyPointsElement = document.getElementById('generatedKeyPoints');
            const hashtagsElement = document.getElementById('generatedHashtags');
            const feedbackTextElement = document.getElementById('feedbackText');

            if (!titleElement || !descriptionElement || !keyPointsElement || 
                !hashtagsElement || !feedbackTextElement) {
                throw new Error('Required modal elements not found');
            }

            titleElement.textContent = postTitle;
            descriptionElement.textContent = description;
            keyPointsElement.textContent = keyPoints;
            hashtagsElement.textContent = hashtags;
            feedbackTextElement.value = '';

            // Setup feedback buttons with error handling
            setupFeedbackButtons(imageId).catch(error => {
                showErrorMessage('Error setting up feedback buttons: ' + error.message);
                return;
            });

            feedbackModal.show();
        } catch (error) {
            console.error('Error showing feedback modal:', error);
            showErrorMessage('Error showing feedback dialog: ' + error.message);
        }
    } else if (target.classList.contains('remove-entry-btn')) {
        // ... [Remove button code remains unchanged]
    }
});

async function setupFeedbackButtons(imageId) {
    const modalButtons = {
        accept: document.getElementById('acceptContent'),
        refine: document.getElementById('refineContent'),
        restart: document.getElementById('restartContent')
    };

    // Validate all buttons exist
    for (const [key, button] of Object.entries(modalButtons)) {
        if (!button) {
            throw new Error(`${key} button not found in modal`);
        }
    }

    // Create new buttons with preserved attributes
    const newButtons = {};
    for (const [key, button] of Object.entries(modalButtons)) {
        newButtons[key] = button.cloneNode(true);
        button.parentNode.replaceChild(newButtons[key], button);
    }

    // Accept button handler
    newButtons.accept.addEventListener('click', async function() {
        try {
            feedbackModal.hide();
            const row = document.querySelector(`tr[data-image-id="${imageId}"]`);
            if (!row) {
                throw new Error('Row not found');
            }

            const feedbackBtn = row.querySelector('.feedback-btn');
            if (feedbackBtn) {
                feedbackBtn.classList.remove('btn-outline-info');
                feedbackBtn.classList.add('btn-outline-success');
            }
        } catch (error) {
            console.error('Error in accept button handler:', error);
            showErrorMessage('Error accepting content: ' + error.message);
        }
    });

    // Refine button handler
    newButtons.refine.addEventListener('click', async function() {
        const feedbackText = document.getElementById('feedbackText');
        if (!feedbackText) {
            showErrorMessage('Feedback text area not found');
            return;
        }

        const feedback = feedbackText.value.trim();
        if (!feedback) {
            showErrorMessage('Please provide feedback for refinement');
            return;
        }

        try {
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Refining...';

            const response = await fetch(`/refine_content/${imageId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ feedback: feedback })
            });

            if (!response.ok) {
                throw new Error(await response.text() || 'Failed to refine content');
            }

            const refinedImage = await response.json();
            updateTableContent(refinedImage);
            feedbackModal.hide();
            showSuccessMessage('Content refined successfully');

        } catch (error) {
            console.error('Error refining content:', error);
            showErrorMessage('Error refining content: ' + error.message);
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-pencil"></i> Refine';
        }
    });

    // Restart button handler
    newButtons.restart.addEventListener('click', async function() {
        try {
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Resetting...';

            const response = await fetch(`/reset_content/${imageId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to reset content');
            }

            const resetImage = await response.json();
            updateTableContent(resetImage);
            feedbackModal.hide();
            showSuccessMessage('Content reset successfully');

        } catch (error) {
            console.error('Error resetting content:', error);
            showErrorMessage('Error resetting content: ' + error.message);
        } finally {
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Delete & Restart';
        }
    });
}

// ... [Rest of the code remains unchanged]
