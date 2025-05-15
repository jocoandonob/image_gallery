document.addEventListener('DOMContentLoaded', function() {
    // Handle tag filter change
    const tagSelect = document.querySelector('.filter-select');
    if (tagSelect) {
        tagSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    // Handle tag clicks in gallery
    const tagLinks = document.querySelectorAll('.gallery-tag');
    if (tagLinks) {
        tagLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Let the href handle navigation
            });
        });
    }
});