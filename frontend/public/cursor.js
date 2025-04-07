// Custom cursor tooltip effect
document.addEventListener('DOMContentLoaded', () => {
  // Create tooltip element
  const tooltip = document.createElement('div');
  tooltip.className = 'custom-cursor-tooltip';
  document.body.appendChild(tooltip);

  // Add styles to the head
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    .custom-cursor-tooltip {
      position: fixed;
      background-color: rgba(255, 0, 122, 0.9);
      color: white;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
      pointer-events: none;
      z-index: 9999;
      opacity: 0;
      transform: translate(-50%, -100%) translateY(-10px);
      transition: opacity 0.2s ease, transform 0.2s ease;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
      white-space: nowrap;
      max-width: 250px;
      overflow: hidden;
      text-overflow: ellipsis;
      font-family: 'Inter', sans-serif;
      backdrop-filter: blur(3px);
    }

    .custom-cursor-tooltip::after {
      content: '';
      position: absolute;
      bottom: -4px;
      left: 50%;
      transform: translateX(-50%);
      width: 0;
      height: 0;
      border-left: 5px solid transparent;
      border-right: 5px solid transparent;
      border-top: 5px solid rgba(255, 0, 122, 0.9);
    }

    [data-tooltip] {
      cursor: pointer;
      position: relative;
    }

    [data-tooltip]::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 1;
    }
  `;
  document.head.appendChild(styleSheet);

  // Mouse move event to position the tooltip
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX;
    const y = e.clientY;
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
  });

  // Detect elements with tooltip and show/hide on hover
  document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (target) {
      const tooltipText = target.getAttribute('data-tooltip');
      tooltip.textContent = tooltipText;
      tooltip.style.opacity = '1';
      tooltip.style.transform = 'translate(-50%, -100%) translateY(-20px)';
    }
  });

  document.addEventListener('mouseout', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (target) {
      tooltip.style.opacity = '0';
      tooltip.style.transform = 'translate(-50%, -100%) translateY(-10px)';
    }
  });

  // Add data-tooltip attributes to key elements
  function addTooltipsToElements() {
    // Apply to style tiles
    const styleTiles = document.querySelectorAll('.style-tile');
    styleTiles.forEach(tile => {
      if (!tile.hasAttribute('data-tooltip')) {
        const styleName = tile.querySelector('.style-name')?.textContent;
        if (styleName) {
          tile.setAttribute('data-tooltip', `Browse ${styleName} style outfits`);
        }
      }
    });

    // Apply to generate button
    const generateButton = document.querySelector('.generate-button');
    if (generateButton && !generateButton.hasAttribute('data-tooltip')) {
      generateButton.setAttribute('data-tooltip', 'Create your custom AI outfit');
    }

    // Apply to photo upload button
    const photoButton = document.querySelector('.photo-upload-button');
    if (photoButton && !photoButton.hasAttribute('data-tooltip')) {
      photoButton.setAttribute('data-tooltip', 'Upload your photo for virtual try-on');
    }

    // Apply to nav items
    const navItems = document.querySelectorAll('.menu-item a');
    navItems.forEach(item => {
      if (!item.hasAttribute('data-tooltip') && item.textContent) {
        item.setAttribute('data-tooltip', `Go to ${item.textContent}`);
      }
    });
  }

  // Initial tooltips
  setTimeout(addTooltipsToElements, 1000);

  // Reapply tooltips when DOM changes (for React apps)
  const observer = new MutationObserver((mutations) => {
    addTooltipsToElements();
  });

  // Observe DOM changes
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}); 