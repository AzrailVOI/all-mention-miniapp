/**
 * API для работы с участниками чата
 */

/**
 * Загружает список участников чата
 * @param {number} chatId - ID чата
 * @returns {Promise<{success: boolean, members: Array}>}
 */
async function loadMembers(chatId) {
    const tg = window.Telegram.WebApp;
    
    // Получаем данные пользователя из Telegram WebApp
    const user = tg.initDataUnsafe?.user;
    const userId = user?.id;
    
    if (!userId) {
        throw new Error('Не удалось получить ID пользователя из Telegram WebApp');
    }
    
    // Отправляем запрос на сервер
    const url = `/api/chats/${chatId}/members`;
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: userId
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
        throw new Error(data.error || 'Не удалось загрузить участников');
    }
    
    return data;
}

// Экспорт
if (typeof window !== 'undefined') {
    window.MembersAPI = {
        loadMembers
    };
}
