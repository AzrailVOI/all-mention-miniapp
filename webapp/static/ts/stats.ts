// Управление статистикой
import type { ChatStats } from './types.js';

let statsContainer: HTMLElement | null = null;

/**
 * Инициализация контейнера статистики
 */
export function initStatsContainer(): void {
    statsContainer = document.querySelector('.stats');
}

/**
 * Отображение статистики
 */
export function renderStats(stats: ChatStats | null): void {
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
export function toggleStats(): void {
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
