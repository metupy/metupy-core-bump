/**
 * Peradocs TOC - Table of Contents Generation
 */

document.addEventListener('DOMContentLoaded', () => {
    const articleContent = document.querySelector('.metu-docs-content');
    const tocList = document.getElementById('metu-toc-list');
    const tocToggleBtn = document.getElementById('metu-toc-toggle');
    const tocMenu = document.getElementById('metu-toc-menu');

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
        tocToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            tocMenu.classList.toggle('metu-mobile-toc-active');
        });

        document.addEventListener('click', (e) => {
            if (!tocMenu.contains(e.target) && !tocToggleBtn.contains(e.target)) {
                tocMenu.classList.remove('metu-mobile-toc-active');
            }
        });
    }
});