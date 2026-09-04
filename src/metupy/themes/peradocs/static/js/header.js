/**
 * Peradocs Header - Mobile Navigation & Dropdown
 */

function initMobileNavigation() {
    const menuToggleBtn = document.getElementById('metu-menu-toggle');
    const menuIcon = document.getElementById('metu-menu-icon');
    const navMenu = document.getElementById('metu-nav-menu');
    const navOverlay = document.getElementById('metu-nav-overlay');
    const docsSidebar = document.querySelector('.metu-docs-sidebar');
    if (!menuToggleBtn || window.__metupyNavigationInitialized) return;
    window.__metupyNavigationInitialized = true;

    function closeMobileMenu() {
        if (navMenu) navMenu.classList.remove('metu-active');
        if (docsSidebar) docsSidebar.classList.remove('metu-mobile-sidebar-active');
        if (navOverlay) navOverlay.classList.remove('metu-active');
        if (menuIcon) menuIcon.classList.replace('bx-x', 'bx-menu');
    }

    function toggleMobileMenu() {
        const activeMenu = docsSidebar || navMenu;
        const activeClass = docsSidebar ? 'metu-mobile-sidebar-active' : 'metu-active';
        const isOpen = activeMenu && activeMenu.classList.contains(activeClass);
        if (isOpen) {
            closeMobileMenu();
            return;
        }
        if (docsSidebar) {
            docsSidebar.classList.add('metu-mobile-sidebar-active');
        } else if (navMenu) {
            navMenu.classList.add('metu-active');
        }
        if (navOverlay) navOverlay.classList.add('metu-active');

        if (menuIcon) menuIcon.classList.replace('bx-menu', 'bx-x');
    }

    menuToggleBtn.onclick = toggleMobileMenu;
    menuToggleBtn.ontouchend = (event) => {
        event.preventDefault();
        toggleMobileMenu();
    };
    if (navOverlay) navOverlay.onclick = () => {
        closeMobileMenu();
        const tocMenu = document.getElementById('metu-toc-menu');
        if (tocMenu) tocMenu.classList.remove('metu-mobile-toc-active');
    };

    if (docsSidebar) {
        docsSidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                closeMobileMenu();
            });
        });
    }

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
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileNavigation);
    setTimeout(initMobileNavigation, 100);
} else {
    initMobileNavigation();
}