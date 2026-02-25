// File: animated-nav.js
// Purpose: Drives the sliding pill indicator in the glassmorphism navbar

document.addEventListener('DOMContentLoaded', function() {
    const navContainer = document.querySelector('.animated-nav-container');
    if (!navContainer) return;

    const navItems = navContainer.querySelectorAll('.animated-nav-item');
    const pill = navContainer.querySelector('.border-effect');

    const PADDING = 6; // extra horizontal padding around the pill

    function updatePillPosition(targetItem) {
        // Pill is hidden on mobile — skip measurement to avoid layout thrash
        if (window.innerWidth < 992) return;

        const itemRect = targetItem.getBoundingClientRect();
        const containerRect = navContainer.getBoundingClientRect();

        const left = itemRect.left - containerRect.left - PADDING;
        const width = itemRect.width + PADDING * 2;

        pill.style.left = left + 'px';
        pill.style.width = width + 'px';
    }

    function hidePill() {
        pill.style.width = '0';
        pill.style.opacity = '0';
    }

    function showPill() {
        pill.style.opacity = '1';
    }

    function setActiveFromCurrentPage() {
        const currentPath = window.location.pathname;
        let activeFound = false;

        navItems.forEach((item) => {
            item.classList.remove('active');

            // Check direct link
            const link = item.querySelector(':scope > a');
            if (link && link.getAttribute('href') === currentPath) {
                item.classList.add('active');
                showPill();
                updatePillPosition(item);
                activeFound = true;
                return;
            }

            // Check dropdown items
            const dropdownLinks = item.querySelectorAll('.dropdown-menu a');
            dropdownLinks.forEach((dropLink) => {
                dropLink.classList.remove('active');
                if (dropLink.getAttribute('href') === currentPath) {
                    dropLink.classList.add('active');
                    item.classList.add('active');
                    showPill();
                    updatePillPosition(item);
                    activeFound = true;
                }
            });
        });

        if (!activeFound) {
            hidePill();
        }
    }

    navItems.forEach((item) => {
        item.addEventListener('mouseenter', () => { showPill(); updatePillPosition(item); });

        item.addEventListener('mouseleave', () => {
            const activeItem = navContainer.querySelector('.animated-nav-item.active');
            if (activeItem) {
                showPill();
                updatePillPosition(activeItem);
            } else {
                hidePill();
            }
        });
    });

    // Small delay to let layout settle before measuring positions
    setTimeout(setActiveFromCurrentPage, 100);

    window.addEventListener('resize', () => {
        const activeItem = navContainer.querySelector('.animated-nav-item.active');
        if (activeItem) updatePillPosition(activeItem);
    });
});
