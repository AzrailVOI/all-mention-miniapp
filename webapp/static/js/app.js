/**
 * Главный файл приложения для страницы списка чатов
 * Использует модульную архитектуру
 */

// Telegram WebApp API
const tg = window.Telegram.WebApp;

// Инициализация WebApp
tg.ready();
tg.expand();

// Элементы DOM
const statsContainer = document.querySelector('.stats');
const chatsContainer = document.querySelector('.chat-list');
const loadingElement = document.querySelector('.loading');

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем иконки Lucide
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // Инициализируем сворачивание блоков (по умолчанию все свернуты)
    if (window.Collapse) {
        window.Collapse.init();
    }
    
    // На главной странице скрываем кнопку назад (если она есть)
    if (tg.BackButton) {
        tg.BackButton.hide();
    }
    
    // Обработка нативной кнопки "назад" на главной странице
    // Если пользователь нажал назад на главной странице, закрываем миниапп
    window.addEventListener('popstate', (event) => {
        // На главной странице при нажатии назад закрываем миниапп
        if (window.location.pathname === '/' || window.location.pathname === '') {
            tg.close();
        }
    });
    
    await loadChatsData();
    
    // Обработчик кнопки обновления
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            await loadChatsData();
        });
    }
    
    // Обработчик поиска по Enter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearchHandler();
            }
        });
    }
});

/**
 * Загружает и отображает список чатов
 */
async function loadChatsData() {
    try {
        // Показываем загрузку
        if (window.Loading) {
            window.Loading.show(loadingElement, chatsContainer);
        } else {
            if (loadingElement) loadingElement.style.display = 'block';
            if (chatsContainer) chatsContainer.innerHTML = '';
        }
        
        // Загружаем данные через API
        const data = await window.ChatsAPI.loadChats();
        
        // Отображаем статистику
        if (window.StatsRender && statsContainer) {
            window.StatsRender.renderStats(data.stats, statsContainer);
        }
        
        // Отображаем список чатов
        if (window.ChatsRender && chatsContainer) {
            window.ChatsRender.renderChats(data.chats, data.info, chatsContainer);
        }
        
    } catch (error) {
        console.error('Error loading chats:', error);
        
        // Показываем ошибку
        const errorMessage = error.message || 'Не удалось загрузить список чатов. Попробуйте обновить страницу.';
        if (window.Errors && chatsContainer) {
            window.Errors.show(errorMessage, chatsContainer);
        } else if (chatsContainer) {
            chatsContainer.innerHTML = `
                <div class="error">
                    <strong>Ошибка:</strong> ${window.escapeHtml ? window.escapeHtml(errorMessage) : errorMessage}
                </div>
                <button class="refresh-btn" onclick="location.reload()">Обновить</button>
            `;
        }
    } finally {
        // Скрываем загрузку
        if (window.Loading) {
            window.Loading.hide(loadingElement);
        } else {
            if (loadingElement) loadingElement.style.display = 'none';
        }
    }
}

/**
 * Обработчик поиска чатов
 */
function performSearchHandler() {
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput?.value;
    
    if (window.Search) {
        window.Search.performSearch(searchTerm, loadChatsData);
    } else {
        // Fallback
        if (!searchTerm || !searchTerm.trim()) {
            loadChatsData();
            return;
        }
        
        const term = searchTerm.toLowerCase().trim();
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
}

// Экспорт для использования в HTML (onclick)
window.performSearch = performSearchHandler;
