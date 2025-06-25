// Force browser reload Mon Apr  7 17:38:51 PDT 2025

// Block placeholder images and fallbacks
(function() {
  // Create an observer to replace placeholder images
  const placeholderDomains = ['via.placeholder.com', 'placeholder.com', 'images.unsplash.com'];
  
  // Intercept image errors and prevent default handling
  document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
      const src = e.target.src || '';
      if (placeholderDomains.some(domain => src.includes(domain))) {
        console.log('Blocked loading placeholder image:', src);
        e.preventDefault();
        e.stopPropagation();
        
        // Hide the image element
        e.target.style.display = 'none';
        
        // Add a class to the parent for styling
        if (e.target.parentNode) {
          e.target.parentNode.classList.add('image-load-error');
          
          // Create an error message element if it doesn't exist
          if (!e.target.parentNode.querySelector('.missing-image-note')) {
            const errorNote = document.createElement('div');
            errorNote.className = 'missing-image-note';
            errorNote.innerText = 'Image unavailable';
            e.target.parentNode.appendChild(errorNote);
          }
        }
      }
    }
  }, true);
  
  // Override fetch and XMLHttpRequest for placeholder domains
  const originalFetch = window.fetch;
  window.fetch = function(...args) {
    const url = args[0]?.url || args[0];
    if (typeof url === 'string' && placeholderDomains.some(domain => url.includes(domain))) {
      console.log('Blocking fetch to placeholder domain:', url);
      return Promise.reject(new Error('Blocked placeholder domain'));
    }
    return originalFetch.apply(this, args);
  };
  
  const originalXHROpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(...args) {
    const url = args[1];
    if (typeof url === 'string' && placeholderDomains.some(domain => url.includes(domain))) {
      console.log('Blocking XHR to placeholder domain:', url);
      this.abort();
      return;
    }
    return originalXHROpen.apply(this, args);
  };
  
  // Add CSS for error state
  const style = document.createElement('style');
  style.textContent = `
    .image-load-error {
      position: relative;
      background-color: #f8f8f8;
      min-height: 150px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .missing-image-note {
      color: #666;
      font-size: 0.85rem;
      font-style: italic;
      text-align: center;
      padding: 10px;
    }
  `;
  document.head.appendChild(style);
})();
