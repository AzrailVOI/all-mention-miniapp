/**
 * Рендеринг статистики чатов
 */

/**
 * Отображает статистику чатов
 * @param {Object} stats - Объект со статистикой
 * @param {HTMLElement} container - Контейнер для отображения
 */
function renderStats(stats, container) {
    if (!container) return;
    
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon"><i data-lucide="message-square"></i></div>
            <div class="stat-value">${stats.total || 0}</div>
            <div class="stat-label">Всего чатов</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i data-lucide="users"></i></div>
            <div class="stat-value">${stats.groups || 0}</div>
            <div class="stat-label">Группы</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i data-lucide="users-round"></i></div>
            <div class="stat-value">${stats.supergroups || 0}</div>
            <div class="stat-label">Супергруппы</div>
        </div>
    `;
    
    // Инициализируем иконки
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// Экспорт
if (typeof window !== 'undefined') {
    window.StatsRender = {
        renderStats
    };
}
