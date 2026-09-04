/**
 * Peradocs Theme - JavaScript
 * Handles dark mode, navigation, search modal, and TOC generation.
 */

// Dark mode logic
const themeToggleBtn = document.getElementById('metu-theme-toggle');
const themeIcon = document.getElementById('metu-theme-icon');

const savedTheme = localStorage.getItem('theme');
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
    if (themeIcon) themeIcon.classList.replace('bx-moon', 'bx-sun');
}

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        if (newTheme === 'dark') {
            themeIcon.classList.replace('bx-moon', 'bx-sun');
        } else {
            themeIcon.classList.replace('bx-sun', 'bx-moon');
        }

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

// Search modal
const searchModal = document.getElementById('metu-search-modal');
const desktopSearchTrigger = document.getElementById('metu-search-modal-trigger');
const mobileSearchTrigger = document.getElementById('metu-mobile-search-trigger');
const closeSearchModalBtn = document.getElementById('metu-close-search-modal');
const modalSearchInput = document.getElementById('metu-modal-search-input');

function openSearchModal() {
    if (searchModal) {
        searchModal.classList.add('metu-active');
        setTimeout(() => modalSearchInput && modalSearchInput.focus(), 100);
    }
}

function closeSearchModal() {
    if (searchModal) searchModal.classList.remove('metu-active');
}

if (desktopSearchTrigger) desktopSearchTrigger.addEventListener('click', openSearchModal);
if (mobileSearchTrigger) mobileSearchTrigger.addEventListener('click', openSearchModal);
if (closeSearchModalBtn) closeSearchModalBtn.addEventListener('click', closeSearchModal);

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openSearchModal();
    }
    if (e.key === 'Escape' && searchModal && searchModal.classList.contains('metu-active')) {
        closeSearchModal();
    }
});

// TOC generation and heading anchors
document.addEventListener('DOMContentLoaded', () => {
    const articleContent = document.querySelector('.metu-docs-content');
    const tocList = document.getElementById('metu-toc-list');
    const tocToggleBtn = document.getElementById('metu-toc-toggle');
    const tocMenu = document.getElementById('metu-toc-menu');

    if (articleContent) {
        const headings = articleContent.querySelectorAll('h2, h3');

        if (headings.length > 0 && tocList) {
            tocList.innerHTML = '';

            headings.forEach(heading => {
                const pureText = heading.textContent.replace(/#/g, '').trim();

                if (!heading.id) {
                    heading.id = pureText
                        .toLowerCase()
                        .replace(/[^a-z0-9\s-]/g, '')
                        .replace(/\s+/g, '-')
                        .replace(/-+/g, '-');
                }

                heading.classList.add('metu-heading-anchor');

                if (!heading.querySelector('.metu-heading-text')) {
                    const textSpan = document.createElement('span');
                    textSpan.className = 'metu-heading-text';
                    textSpan.innerHTML = heading.innerHTML;
                    heading.innerHTML = '';
                    heading.appendChild(textSpan);
                }

                if (!heading.querySelector('.header-anchor')) {
                    const anchor = document.createElement('a');
                    anchor.className = 'header-anchor';
                    anchor.href = '#' + heading.id;
                    anchor.setAttribute('aria-label', 'Permalink to ' + pureText);
                    anchor.textContent = '#';
                    heading.appendChild(anchor);
                }

                const tocItem = document.createElement('a');
                tocItem.href = '#' + heading.id;
                tocItem.textContent = pureText;
                tocItem.setAttribute('data-target', heading.id);

                if (heading.tagName === 'H3') {
                    tocItem.classList.add('metu-toc-sub');
                }

                tocList.appendChild(tocItem);
            });

            const observer = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const id = entry.target.getAttribute('id');
                        document.querySelectorAll('#metu-toc-list a').forEach(a => {
                            a.classList.toggle('metu-toc-active', a.getAttribute('data-target') === id);
                        });
                    }
                });
            }, { rootMargin: '-80px 0px -60% 0px' });

            headings.forEach(heading => observer.observe(heading));
        }
    }

});