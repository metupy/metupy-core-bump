/**
 * Peradocs TOC - Table of Contents Generation
 */

function initTableOfContents() {
    const articleContent = document.querySelector('.metu-docs-content');
    const tocList = document.getElementById('metu-toc-list');
    const tocToggleBtn = document.getElementById('metu-toc-toggle');
    const tocMenu = document.getElementById('metu-toc-menu');
    const navOverlay = document.getElementById('metu-nav-overlay');
    if (!tocToggleBtn || !tocMenu || window.__metupyTocInitialized) return;
    window.__metupyTocInitialized = true;

    if (articleContent && tocList) {
        const headings = articleContent.querySelectorAll('h2, h3');

        if (headings.length > 0) {
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

            // Highlight active TOC item on scroll
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

    // Mobile TOC toggle
    if (tocToggleBtn && tocMenu) {
        tocToggleBtn.onclick = (e) => {
            e.stopPropagation();
            const sidebar = document.querySelector('.metu-docs-sidebar');
            const navMenu = document.getElementById('metu-nav-menu');
            if (sidebar) sidebar.classList.remove('metu-mobile-sidebar-active');
            if (navMenu) navMenu.classList.remove('metu-active');
            tocMenu.classList.toggle('metu-mobile-toc-active');
            if (navOverlay) navOverlay.classList.toggle('metu-active', tocMenu.classList.contains('metu-mobile-toc-active'));
        };
        tocToggleBtn.ontouchend = (e) => {
            e.preventDefault();
            tocToggleBtn.onclick(e);
        };

        tocList.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                tocMenu.classList.remove('metu-mobile-toc-active');
                if (navOverlay) navOverlay.classList.remove('metu-active');
            });
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTableOfContents);
    setTimeout(initTableOfContents, 100);
} else {
    initTableOfContents();
}