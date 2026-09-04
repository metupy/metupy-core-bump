/**
 * Peradocs Sidebar - Folder Dropdown Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const folderTriggers = document.querySelectorAll('.metu-folder-trigger');

    folderTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            const folder = trigger.closest('.metu-sidebar-folder');
            if (folder) {
                folder.classList.toggle('metu-folder-open');
            }
        });
    });

    // Auto-open folder containing active link
    const activeLink = document.querySelector('.metu-sidebar-group a.metu-active');
    if (activeLink) {
        const parentFolder = activeLink.closest('.metu-sidebar-folder');
        if (parentFolder) {
            parentFolder.classList.add('metu-folder-open');
        }
    }
});