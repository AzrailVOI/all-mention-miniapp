// Главный файл приложения
import { loadChats } from './api.js';
import { initLoadingElements } from './loading.js';
import { initModalHandlers } from './modal.js';
import { initStatsContainer, toggleStats } from './stats.js';
import { initTheme } from './theme.js';

/**
 * Инициализация приложения
 */
async function init(): Promise<void> {
    // Инициализируем иконки Lucide
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    const tg = window.Telegram?.WebApp;
    if (!tg) {
        console.error('Telegram WebApp не найден');
        return;
    }
    
    // Инициализация WebApp
    tg.ready();
    tg.expand();
    
    // На главной странице скрываем кнопку назад (если она есть)
    if (tg.BackButton) {
        tg.BackButton.hide();
    }
    
    // Обработка нативной кнопки "назад" на главной странице
    window.addEventListener('popstate', (event) => {
        // На главной странице при нажатии назад закрываем миниапп
        if (window.location.pathname === '/' || window.location.pathname === '') {
            tg.close();
        }
    });
    
    // Инициализация элементов
    initStatsContainer();
    initLoadingElements();
    
    // Удаляем loading элемент, если он есть (используем только skeleton)
    const loadingElement = document.querySelector('.loading');
    if (loadingElement) {
        loadingElement.remove();
    }
    
    // Изначально статистика скрыта
    const statsContainer = document.querySelector('.stats');
    if (statsContainer) {
        (statsContainer as HTMLElement).style.display = 'none';
    }

    // Тоггл статистики
    const statsToggle = document.querySelector('.stats-toggle');
    if (statsToggle && statsContainer) {
        statsToggle.addEventListener('click', () => {
            toggleStats();
        });
        // Начальный текст
        statsToggle.textContent = 'Статистика';
    }

    // Обработчик кнопки обновления в шапке
    const refreshBtnHeader = document.querySelector('.refresh-btn-header');
    if (refreshBtnHeader) {
        refreshBtnHeader.addEventListener('click', async () => {
            const icon = refreshBtnHeader.querySelector('i');
            if (icon) {
                (icon as HTMLElement).style.animation = 'spin 1s linear infinite';
            }
            await loadChats();
            if (icon) {
                (icon as HTMLElement).style.animation = '';
            }
        });
    }
    
    // Обработчик кнопки фильтров
    const filtersBtn = document.querySelector('.filters-btn');
    if (filtersBtn) {
        filtersBtn.addEventListener('click', () => {
            if (window.openFiltersModal) {
                window.openFiltersModal();
            }
        });
    }
    
    // Обработчик кнопки переключения темы
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            if (window.toggleTheme) {
                window.toggleTheme();
            }
        });
    }
    
    // Обработчик поиска по Enter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e: KeyboardEvent) => {
            if (e.key === 'Enter') {
                if (window.performSearch) {
                    window.performSearch();
                }
            }
        });
    }
    
    // Обработчик кнопки поиска в модальном окне
    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            if (window.performSearch) {
                window.performSearch();
            }
        });
    }
    
    // Обработчики изменения фильтров
    const filterType = document.getElementById('filterType');
    const sortBy = document.getElementById('sortBy');
    const sortOrder = document.getElementById('sortOrder');
    
    if (filterType) {
        filterType.addEventListener('change', () => {
            if (window.applyFilters) {
                window.applyFilters();
            }
        });
    }
    
    if (sortBy) {
        sortBy.addEventListener('change', () => {
            if (window.applyFilters) {
                window.applyFilters();
            }
        });
    }
    
    if (sortOrder) {
        sortOrder.addEventListener('change', () => {
            if (window.applyFilters) {
                window.applyFilters();
            }
        });
    }
    
    // Инициализация модального окна
    initModalHandlers();
    
    // Инициализация темы
    initTheme();
    
    // Загрузка чатов
    await loadChats();
}

// Запуск приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', init);
