// Главный файл приложения
import { loadChats } from './api';
import { initStatsContainer, toggleStats } from './stats';
import { initModalHandlers } from './modal';
import { initTheme } from './theme';
import { initLoadingElements } from './loading';

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
    
    // Инициализация модального окна
    initModalHandlers();
    
    // Инициализация темы
    initTheme();
    
    // Загрузка чатов
    await loadChats();
}

// Запуск приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', init);
