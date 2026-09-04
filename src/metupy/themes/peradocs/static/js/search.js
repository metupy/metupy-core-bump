/**
 * Peradocs Search - Search Modal Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchModal = document.getElementById('metu-search-modal');
    const desktopSearchTrigger = document.getElementById('metu-search-modal-trigger');
    const mobileSearchTrigger = document.getElementById('metu-mobile-search-trigger');
    const closeSearchModalBtn = document.getElementById('metu-close-search-modal');
    const modalSearchInput = document.getElementById('metu-modal-search-input');
    const searchPlaceholder = document.getElementById('metu-search-placeholder');
    const searchResults = document.getElementById('metu-search-results');

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

    if (searchModal) {
        searchModal.addEventListener('click', (e) => {
            if (e.target === searchModal) closeSearchModal();
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        }
        if (e.key === 'Escape' && searchModal && searchModal.classList.contains('metu-active')) {
            closeSearchModal();
        }
    });

    // Search functionality
    if (modalSearchInput) {
        modalSearchInput.addEventListener('input', async () => {
            const query = modalSearchInput.value.trim();

            if (query.length < 2) {
                if (searchPlaceholder) searchPlaceholder.style.display = 'block';
                if (searchResults) searchResults.style.display = 'none';
                return;
            }

            try {
                const response = await fetch('/search-index.json');
                const index = await response.json();

                const results = index.filter(item => {
                    return (
                        item.title.toLowerCase().includes(query.toLowerCase()) ||
                        item.content.toLowerCase().includes(query.toLowerCase()) ||
                        item.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
                    );
                }).slice(0, 10);

                if (searchPlaceholder) searchPlaceholder.style.display = 'none';
                if (searchResults) {
                    searchResults.style.display = 'block';
                    searchResults.innerHTML = results.map(item => `
                        <a href="${item.url}">
                            <div class="metu-search-title">${item.title}</div>
                            <div class="metu-search-desc">${item.description || ''}</div>
                        </a>
                    `).join('');
                }
            } catch (error) {
                console.error('Search error:', error);
            }
        });
    }
});