// API запросы

const API_URL = '/api/chats';

/**
 * Загрузка списка чатов
 */
async function loadChats() {
    try {
        if (window.showLoading) {
            window.showLoading();
        }
        
        const tg = window.Telegram?.WebApp;
        if (!tg) {
            throw new Error('Telegram WebApp не инициализирован');
        }
        
        // Получаем данные пользователя из Telegram WebApp
        // initData может быть пустым при разработке или прямом открытии в браузере
        const initData = tg.initData || '';
        const user = tg.initDataUnsafe?.user;
        const userId = user?.id;
        
        // Проверяем, что у нас есть хотя бы user_id
        if (!userId) {
            console.warn('[API] User ID не найден, возможно страница открыта не через Telegram WebApp');
            // Показываем понятное сообщение пользователю
            if (window.showError) {
                window.showError('Страница должна быть открыта через Telegram Mini App');
            }
            return;
        }
        
        // Отправляем запрос на сервер
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                init_data: initData,
                user_id: userId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            if (window.showError) {
                window.showError(data.error || 'Не удалось загрузить список чатов');
            }
            return;
        }
        
        // Показываем предупреждение, если данные из кэша
        if (data.cached && data.warning) {
            if (window.showToast) {
                window.showToast(data.warning, 'warning');
            }
        }
        
        // Сохраняем данные для фильтрации
        if (window.setCurrentChats) {
            window.setCurrentChats(data.chats || [], data.stats);
        }
        
        if (window.renderStats) {
            window.renderStats(data.stats);
        }
        
        // Применяем фильтры (которые отобразят чаты)
        if (window.applyFilters) {
            window.applyFilters();
        }
        
    } catch (error) {
        console.error('Error loading chats:', error);
        if (window.showError) {
            window.showError('Не удалось загрузить список чатов. Попробуйте обновить страницу.');
        }
    } finally {
        if (window.hideLoading) {
            window.hideLoading();
        }
    }
}

/**
 * Удаление чата из списка
 */
async function deleteChat(chatId, chatTitle) {
    if (!confirm(`Вы уверены, что хотите удалить чат "${chatTitle}" из списка?`)) {
        return;
    }
    
    try {
        const tg = window.Telegram?.WebApp;
        if (!tg) {
            throw new Error('Telegram WebApp не инициализирован');
        }
        
        // Отправляем запрос на удаление
        const response = await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: tg.initDataUnsafe?.user?.id
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка при удалении чата');
        }
        
        const data = await response.json();
        
        if (data.success) {
            if (window.showToast) {
                window.showToast('Чат успешно удален из списка', 'success');
            }
            // Обновляем список чатов
            await loadChats();
        } else {
            if (window.showToast) {
                window.showToast(data.error || 'Не удалось удалить чат', 'error');
            }
        }
    } catch (error) {
        console.error('Error deleting chat:', error);
        if (window.showToast) {
            window.showToast('Ошибка при удалении чата', 'error');
        }
    }
}

/**
 * Открыть страницу участников чата
 */
function openChat(chatId, chatTitle) {
    const encodedTitle = encodeURIComponent(chatTitle || 'Участники чата');
    window.history.pushState({ page: 'members', chatId, chatTitle }, '', `/members?chat_id=${chatId}&title=${encodedTitle}`);
    window.location.href = `/members?chat_id=${chatId}&title=${encodedTitle}`;
}

// Экспорт в window
window.loadChats = loadChats;
window.deleteChat = deleteChat;
window.openChat = openChat;
