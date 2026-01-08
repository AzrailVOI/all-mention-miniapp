/**
 * Управление сворачиванием/разворачиванием блоков
 */

let isExpanded = false;

/**
 * Переключает состояние всех блоков (сворачивает/разворачивает)
 * @param {boolean} forceState - Принудительное состояние (опционально)
 */
function toggleAllBlocks(forceState = null) {
    const statsSection = document.querySelector('.stats');
    const chatsSection = document.querySelector('.chats-section');
    const toggleBtn = document.getElementById('toggleAllBtn');
    const toggleIcon = toggleBtn?.querySelector('i');
    
    // Определяем новое состояние
    if (forceState !== null) {
        isExpanded = forceState;
    } else {
        isExpanded = !isExpanded;
    }
    
    // Применяем классы для анимации
    if (statsSection) {
        if (isExpanded) {
            statsSection.classList.remove('collapsed');
            statsSection.classList.add('expanded');
        } else {
            statsSection.classList.remove('expanded');
            statsSection.classList.add('collapsed');
        }
    }
    
    if (chatsSection) {
        if (isExpanded) {
            chatsSection.classList.remove('collapsed');
            chatsSection.classList.add('expanded');
        } else {
            chatsSection.classList.remove('expanded');
            chatsSection.classList.add('collapsed');
        }
    }
    
    // Обновляем иконку и текст кнопки
    if (toggleBtn) {
        const toggleText = toggleBtn.querySelector('.toggle-all-text');
        
        if (isExpanded) {
            if (toggleIcon) {
                toggleIcon.setAttribute('data-lucide', 'chevron-up');
            }
            toggleBtn.setAttribute('title', 'Свернуть все блоки');
            if (toggleText) {
                toggleText.textContent = 'Свернуть все';
            }
        } else {
            if (toggleIcon) {
                toggleIcon.setAttribute('data-lucide', 'chevron-down');
            }
            toggleBtn.setAttribute('title', 'Развернуть все блоки');
            if (toggleText) {
                toggleText.textContent = 'Развернуть все';
            }
        }
        
        // Переинициализируем иконку Lucide
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
}

/**
 * Инициализирует сворачивание блоков (по умолчанию все свернуты)
 */
function initCollapse() {
    // Сворачиваем все блоки по умолчанию
    toggleAllBlocks(false);
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Collapse = {
        toggle: toggleAllBlocks,
        init: initCollapse,
        isExpanded: () => isExpanded
    };
    
    // Для использования в HTML
    window.toggleAllBlocks = toggleAllBlocks;
}
