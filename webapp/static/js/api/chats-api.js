/**
 * API для работы с чатами
 */

const API_URL = '/api/chats';

/**
 * Загружает список чатов с сервера
 * @returns {Promise<{success: boolean, chats: Array, stats: Object, info?: string}>}
 */
async function loadChats() {
    const tg = window.Telegram.WebApp;
    
    // Получаем данные пользователя из Telegram WebApp
    const initData = tg.initData;
    const user = tg.initDataUnsafe?.user;
    
    // Отправляем запрос на сервер
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            init_data: initData,
            user_id: user?.id
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.error) {
        throw new Error(data.error);
    }
    
    return data;
}

// Экспорт
if (typeof window !== 'undefined') {
    window.ChatsAPI = {
        loadChats
    };
}
