// Image preview for upload form
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    
    if (imageInput && imagePreview) {
        // Set default image preview style
        imagePreview.style.display = 'none';
        
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                
                reader.onerror = function() {
                    console.error('Error reading file');
                    imagePreview.style.display = 'none';
                };
                
                reader.readAsDataURL(this.files[0]);
            } else {
                imagePreview.style.display = 'none';
            }
        });
    }
    
    // Image modal functionality
    const galleryItems = document.querySelectorAll('.gallery-item');
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const closeBtn = document.querySelector('.modal-close');
    
    if (galleryItems && modal && modalImg) {
        galleryItems.forEach(item => {
            item.addEventListener('click', function() {
                const imgSrc = this.querySelector('img').src;
                modal.style.display = 'block';
                modalImg.src = imgSrc;
            });
        });
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                modal.style.display = 'none';
            });
        }
        
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    // Tags autocomplete
    const tagsInput = document.getElementById('tags');
    if (tagsInput) {
        fetch('/api/tags')
            .then(response => response.json())
            .then(tags => {
                // Simple comma-separated input for now
                // Could be enhanced with a proper autocomplete library
            })
            .catch(error => console.error('Error fetching tags:', error));
    }
});