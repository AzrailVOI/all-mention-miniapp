// Главный файл инициализации

// Telegram WebApp API
const tg = window.Telegram?.WebApp;

// Инициализация WebApp (только если доступен)
if (tg) {
    tg.ready();
    tg.expand();
} else {
    console.warn('[App] Telegram WebApp не доступен, возможно страница открыта не через Telegram');
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем иконки Lucide
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // На главной странице скрываем кнопку назад (если она есть)
    if (tg && tg.BackButton) {
        tg.BackButton.hide();
    }
    
    // Обработка нативной кнопки "назад" на главной странице
    window.addEventListener('popstate', (event) => {
        // На главной странице при нажатии назад закрываем миниапп
        if (tg && (window.location.pathname === '/' || window.location.pathname === '')) {
            tg.close();
        }
    });
    
    // Изначально статистика скрыта
    const statsContainer = document.querySelector('.stats');
    if (statsContainer) {
        statsContainer.style.display = 'none';
    }

    // Тоггл статистики
    const statsToggle = document.querySelector('.stats-toggle');
    if (statsToggle && statsContainer) {
        statsToggle.addEventListener('click', () => {
            if (window.toggleStats) {
                window.toggleStats();
            }
        });
    }
    
    // Инициализация темы
    if (window.initTheme) {
        window.initTheme();
    }
    
    // Инициализация обработчиков модального окна
    if (window.initModalHandlers) {
        window.initModalHandlers();
    }
    
    // Обработчик кнопки обновления в шапке
    const refreshBtnHeader = document.querySelector('.refresh-btn-header');
    if (refreshBtnHeader) {
        refreshBtnHeader.addEventListener('click', async () => {
            const icon = refreshBtnHeader.querySelector('i');
            if (icon) {
                icon.style.animation = 'spin 1s linear infinite';
            }
            if (window.loadChats) {
                await window.loadChats();
            }
            if (icon) {
                icon.style.animation = '';
            }
        });
    }
    
    // Обработчик поиска по Enter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                if (window.performSearch) {
                    window.performSearch();
                }
            }
        });
    }
    
    // Загружаем чаты
    if (window.loadChats) {
        await window.loadChats();
    }
});
