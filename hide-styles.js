// Create a style element
const styleTag = document.createElement('style');

// Set its content to our CSS overrides
styleTag.textContent = `
/* Override style section */
.style-categories h3,
.style-grid,
.style-categories > h3,
.style-categories .style-grid {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Add compact button instead */
.style-categories:before {
  content: 'Choose a Style';
  display: inline-block !important;
  background: #ff4081 !important;
  color: white !important;
  border: none !important;
  border-radius: 30px !important;
  padding: 10px 20px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  margin: 10px 0 !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
  text-align: center !important;
  max-width: 200px !important;
}
`;

// Add it to the document head
document.head.appendChild(styleTag);

// Alternative approach: directly hide elements when found
document.addEventListener('DOMContentLoaded', function() {
  // Hide the style grid section
  const styleGrids = document.querySelectorAll('.style-grid');
  const styleHeadings = document.querySelectorAll('.style-categories h3');
  
  styleGrids.forEach(grid => {
    grid.style.display = 'none';
  });
  
  styleHeadings.forEach(heading => {
    heading.style.display = 'none';
  });
  
  // Add a button if it doesn't exist
  const styleCategories = document.querySelector('.style-categories');
  if (styleCategories && !document.querySelector('.style-toggle-btn')) {
    const button = document.createElement('button');
    button.className = 'style-toggle-btn';
    button.textContent = 'Choose a Style';
    button.style.display = 'inline-block';
    button.style.background = '#ff4081';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '30px';
    button.style.padding = '10px 20px';
    button.style.fontSize = '16px';
    button.style.fontWeight = '600';
    button.style.cursor = 'pointer';
    button.style.margin = '10px 0';
    button.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    
    // Insert at beginning of style-categories
    styleCategories.insertBefore(button, styleCategories.firstChild);
  }
}); 