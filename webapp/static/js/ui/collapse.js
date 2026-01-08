/**
 * Управление сворачиванием/разворачиванием блоков
 */

let isExpanded = false;

/**
 * Переключает состояние блока статистики (сворачивает/разворачивает)
 * Блок списка чатов всегда остается открытым
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
    
    // Применяем классы для анимации только к блоку статистики
    if (statsSection) {
        if (isExpanded) {
            statsSection.classList.remove('collapsed');
            statsSection.classList.add('expanded');
        } else {
            statsSection.classList.remove('expanded');
            statsSection.classList.add('collapsed');
        }
    }
    
    // Блок списка чатов всегда открыт
    if (chatsSection) {
        chatsSection.classList.remove('collapsed');
        chatsSection.classList.add('expanded');
    }
    
    // Обновляем иконку и текст кнопки
    if (toggleBtn) {
        const toggleText = toggleBtn.querySelector('.toggle-all-text');
        
        if (isExpanded) {
            if (toggleIcon) {
                toggleIcon.setAttribute('data-lucide', 'chevron-up');
            }
            toggleBtn.setAttribute('title', 'Свернуть статистику');
            if (toggleText) {
                toggleText.textContent = 'Свернуть статистику';
            }
        } else {
            if (toggleIcon) {
                toggleIcon.setAttribute('data-lucide', 'chevron-down');
            }
            toggleBtn.setAttribute('title', 'Развернуть статистику');
            if (toggleText) {
                toggleText.textContent = 'Развернуть статистику';
            }
        }
        
        // Переинициализируем иконку Lucide
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
}

/**
 * Инициализирует сворачивание блоков
 * По умолчанию сворачивается только блок статистики, список чатов всегда открыт
 */
function initCollapse() {
    // Сворачиваем только блок статистики по умолчанию
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
