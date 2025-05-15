document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            // Basic validation
            if (!imageInput.files || !imageInput.files[0]) {
                e.preventDefault();
                alert('Please select an image file');
                return false;
            }
            
            const titleInput = document.getElementById('title');
            if (!titleInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a title');
                return false;
            }
            
            // Form is valid, let it submit
            return true;
        });
    }
    
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
});