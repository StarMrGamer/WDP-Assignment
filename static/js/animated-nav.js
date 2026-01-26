// File: animated-nav.js
// Purpose: Dynamic centering and animation for the prominent slider bar

document.addEventListener('DOMContentLoaded', function() {
    const navContainer = document.querySelector('.animated-nav-container');
    if (!navContainer) return;

    const navItems = navContainer.querySelectorAll('.animated-nav-item');
    const border = navContainer.querySelector('.border-effect');
    
    function updateBorderPosition(targetItem) {
        const itemRect = targetItem.getBoundingClientRect();
        const containerRect = navContainer.getBoundingClientRect();
        
        // Calculate center of the item relative to the container
        const itemCenterX = itemRect.left - containerRect.left + (itemRect.width / 2);
        const borderWidth = 60; // Matches CSS width
        
        border.style.left = (itemCenterX - (borderWidth / 2)) + 'px';
    }

    function setActiveFromCurrentPage() {
        const currentPath = window.location.pathname;
        let activeFound = false;

        navItems.forEach((item) => {
            const link = item.querySelector('a');
            if (link && link.getAttribute('href') === currentPath) {
                navItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                updateBorderPosition(item);
                activeFound = true;
            }
        });

        if (!activeFound && navItems.length > 0) {
            navItems[0].classList.add('active');
            updateBorderPosition(navItems[0]);
        }
    }

    navItems.forEach((item) => {
        item.addEventListener('mouseenter', () => updateBorderPosition(item));
        
        item.addEventListener('mouseleave', () => {
            const activeItem = navContainer.querySelector('.animated-nav-item.active');
            if (activeItem) updateBorderPosition(activeItem);
        });
    });

    // Initialize position
    setTimeout(setActiveFromCurrentPage, 100);

    window.addEventListener('resize', () => {
        const activeItem = navContainer.querySelector('.animated-nav-item.active');
        if (activeItem) updateBorderPosition(activeItem);
    });
});
