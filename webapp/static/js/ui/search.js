/**
 * Логика поиска чатов
 */

/**
 * Выполняет поиск чатов по названию
 * @param {string} searchTerm - Поисковый запрос
 * @param {Function} onEmptySearch - Функция, вызываемая при пустом поиске
 */
function performSearch(searchTerm, onEmptySearch) {
    if (!searchTerm || !searchTerm.trim()) {
        if (onEmptySearch) {
            onEmptySearch();
        }
        return;
    }
    
    const term = searchTerm.toLowerCase().trim();
    
    // Фильтруем уже загруженные чаты
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        const chatName = item.querySelector('.chat-name')?.textContent.toLowerCase() || '';
        if (chatName.includes(term)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Search = {
        performSearch
    };
}
