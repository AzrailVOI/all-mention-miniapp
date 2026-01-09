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
    const initData = tg.initData;
    const user = tg.initDataUnsafe?.user;
    const userId = user?.id;
    
    if (!userId) {
        throw new Error('Не удалось получить ID пользователя из Telegram WebApp');
    }
    
    // Проверяем offline режим
    const isOffline = window.Offline && window.Offline.isOffline();
    
    // Если offline, пытаемся вернуть кэшированные данные
    if (isOffline) {
        const cached = window.Offline && window.Offline.getCachedMembers(chatId);
        if (cached) {
            console.log('[MembersAPI] Используем кэшированные данные (offline режим)');
            if (window.Offline) {
                window.Offline.showOfflineIndicator();
            }
            return {
                success: true,
                members: cached,
                cached: true,
                warning: 'Нет подключения к интернету. Показаны кэшированные данные.'
            };
        }
    }
    
    try {
        // Отправляем запрос на сервер
        const url = `/api/chats/${chatId}/members`;
        
        const response = await fetch(url, {
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
            // При ошибке сети пытаемся вернуть кэш
            if (window.Offline) {
                const cached = window.Offline.getCachedMembers(chatId);
                if (cached) {
                    console.log('[MembersAPI] Ошибка сети, используем кэшированные данные');
                    window.Offline.showOfflineIndicator();
                    return {
                        success: true,
                        members: cached,
                        cached: true,
                        warning: 'Ошибка сети. Показаны кэшированные данные.'
                    };
                }
            }
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            // При ошибке API пытаемся вернуть кэш
            if (window.Offline) {
                const cached = window.Offline.getCachedMembers(chatId);
                if (cached) {
                    console.log('[MembersAPI] Ошибка API, используем кэшированные данные');
                    window.Offline.showOfflineIndicator();
                    return {
                        success: true,
                        members: cached,
                        cached: true,
                        warning: 'Ошибка сервера. Показаны кэшированные данные.'
                    };
                }
            }
            throw new Error(data.error || 'Не удалось загрузить участников');
        }
        
        // Сохраняем в кэш при успешном запросе
        if (window.Offline && data.success && data.members) {
            window.Offline.cacheMembers(chatId, data.members);
        }
        
        return data;
    } catch (error) {
        // При любой ошибке пытаемся вернуть кэш
        if (window.Offline) {
            const cached = window.Offline.getCachedMembers(chatId);
            if (cached) {
                console.log('[MembersAPI] Ошибка запроса, используем кэшированные данные:', error);
                window.Offline.showOfflineIndicator();
                return {
                    success: true,
                    members: cached,
                    cached: true,
                    warning: 'Ошибка загрузки данных. Показаны кэшированные данные.'
                };
            }
        }
        throw error;
    }
}

// Экспорт
if (typeof window !== 'undefined') {
    window.MembersAPI = {
        loadMembers
    };
}
