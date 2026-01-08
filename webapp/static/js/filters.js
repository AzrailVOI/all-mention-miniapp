// Фильтры и сортировка

let currentChats = [];
let currentStats = null;

/**
 * Установить текущие чаты и статистику
 */
function setCurrentChats(chats, stats) {
    currentChats = chats;
    currentStats = stats;
}

/**
 * Применить фильтры и сортировку
 */
function applyFilters() {
    if (!currentChats || currentChats.length === 0) {
        if (window.renderChats) {
            window.renderChats([], null);
        }
        return;
    }
    
    let filtered = [...currentChats];
    
    // Фильтр по типу
    const filterType = document.getElementById('filterType')?.value || 'all';
    if (filterType !== 'all') {
        filtered = filtered.filter(chat => chat.type === filterType);
    }
    
    // Поиск по названию
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput?.value.toLowerCase().trim() || '';
    if (searchTerm) {
        filtered = filtered.filter(chat => 
            (chat.title || '').toLowerCase().includes(searchTerm)
        );
    }
    
    // Сортировка
    const sortBy = document.getElementById('sortBy')?.value || 'title';
    const sortOrder = document.getElementById('sortOrder')?.value || 'asc';
    
    if (sortBy === 'title') {
        filtered.sort((a, b) => {
            const cmp = (a.title || '').toLowerCase().localeCompare((b.title || '').toLowerCase());
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    } else if (sortBy === 'members_count') {
        filtered.sort((a, b) => {
            const aCount = a.members_count || 0;
            const bCount = b.members_count || 0;
            const cmp = aCount - bCount;
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    } else if (sortBy === 'type') {
        filtered.sort((a, b) => {
            const cmp = a.type.localeCompare(b.type);
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    }
    
    // Отображаем отфильтрованные чаты
    if (window.renderChats) {
        window.renderChats(filtered, null);
    }
    
    // Обновляем статистику для отфильтрованных чатов
    if (currentStats && window.renderStats) {
        const filteredStats = {
            total: filtered.length,
            groups: filtered.filter(c => c.type === 'group').length,
            supergroups: filtered.filter(c => c.type === 'supergroup').length,
            private: 0,
            channels: 0
        };
        window.renderStats(filteredStats);
    }
}

/**
 * Поиск чатов
 */
function performSearch() {
    applyFilters();
}

/**
 * Сброс фильтров
 */
function resetFilters() {
    const searchInput = document.getElementById('searchInput');
    const filterType = document.getElementById('filterType');
    const sortBy = document.getElementById('sortBy');
    const sortOrder = document.getElementById('sortOrder');
    
    if (searchInput) searchInput.value = '';
    if (filterType) filterType.value = 'all';
    if (sortBy) sortBy.value = 'title';
    if (sortOrder) sortOrder.value = 'asc';
    
    applyFilters();
}

// Экспорт в window
window.setCurrentChats = setCurrentChats;
window.applyFilters = applyFilters;
window.performSearch = performSearch;
window.resetFilters = resetFilters;
