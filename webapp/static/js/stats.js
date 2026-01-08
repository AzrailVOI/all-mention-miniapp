// Управление статистикой

let statsContainer = null;

/**
 * Инициализация контейнера статистики
 */
function initStatsContainer() {
    statsContainer = document.querySelector('.stats');
}

/**
 * Отображение статистики
 */
function renderStats(stats) {
    if (!statsContainer) {
        initStatsContainer();
    }
    if (!statsContainer) return;
    
    if (!stats) {
        statsContainer.innerHTML = '';
        return;
    }
    
    statsContainer.innerHTML = `
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

/**
 * Показать/скрыть статистику
 */
function toggleStats() {
    if (!statsContainer) {
        initStatsContainer();
    }
    if (!statsContainer) return;
    
    const isVisible = statsContainer.style.display !== 'none';
    statsContainer.style.display = isVisible ? 'none' : '';
    
    const statsToggle = document.querySelector('.stats-toggle');
    if (statsToggle) {
        statsToggle.textContent = isVisible ? 'Статистика' : 'Скрыть статистику';
    }
}

// Экспорт в window
window.renderStats = renderStats;
window.toggleStats = toggleStats;
