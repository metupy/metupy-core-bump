/**
 * Peradocs Header - Mobile Navigation & Dropdown
 */

document.addEventListener('DOMContentLoaded', () => {
    const menuToggleBtn = document.getElementById('metu-menu-toggle');
    const menuIcon = document.getElementById('metu-menu-icon');
    const navMenu = document.getElementById('metu-nav-menu');
    const navOverlay = document.getElementById('metu-nav-overlay');

    function toggleMobileMenu() {
        if (navMenu) navMenu.classList.toggle('metu-active');
        if (navOverlay) navOverlay.classList.toggle('metu-active');

        if (navMenu && navMenu.classList.contains('metu-active')) {
            if (menuIcon) menuIcon.classList.replace('bx-menu', 'bx-x');
        } else {
            if (menuIcon) menuIcon.classList.replace('bx-x', 'bx-menu');
        }
    }

    if (menuToggleBtn) menuToggleBtn.addEventListener('click', toggleMobileMenu);
    if (navOverlay) navOverlay.addEventListener('click', toggleMobileMenu);

    // Mobile dropdown accordion
    const dropdowns = document.querySelectorAll('.metu-dropdown');
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.metu-dropdown-trigger');
        if (trigger) {
            trigger.addEventListener('click', (e) => {
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    dropdown.classList.toggle('metu-mobile-open');
                }
            });
        }
    });
});