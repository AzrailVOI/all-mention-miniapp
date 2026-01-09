/**
 * API для работы с чатами
 */

const API_URL = '/api/chats';

/**
 * Загружает список чатов с сервера
 * @param {boolean} forceRefresh - Принудительное обновление (инвалидация кэша)
 * @returns {Promise<{success: boolean, chats: Array, stats: Object, info?: string, cached?: boolean, warning?: string}>}
 */
async function loadChats(forceRefresh = false) {
    const tg = window.Telegram.WebApp;
    
    // Получаем данные пользователя из Telegram WebApp
    const initData = tg.initData;
    const user = tg.initDataUnsafe?.user;
    
    // Проверяем offline режим
    const isOffline = window.Offline && window.Offline.isOffline();
    
    // Если offline, пытаемся вернуть кэшированные данные
    if (isOffline && !forceRefresh) {
        const cached = window.Offline && window.Offline.getCachedChats();
        if (cached) {
            console.log('[ChatsAPI] Используем кэшированные данные (offline режим)');
            if (window.Offline) {
                window.Offline.showOfflineIndicator();
            }
            return {
                ...cached,
                cached: true,
                warning: 'Нет подключения к интернету. Показаны кэшированные данные.'
            };
        }
    }
    
    try {
        // Отправляем запрос на сервер
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                init_data: initData,
                user_id: user?.id,
                force_refresh: forceRefresh
            })
        });
        
        if (!response.ok) {
            // При ошибке сети пытаемся вернуть кэш
            if (!forceRefresh && window.Offline) {
                const cached = window.Offline.getCachedChats();
                if (cached) {
                    console.log('[ChatsAPI] Ошибка сети, используем кэшированные данные');
                    window.Offline.showOfflineIndicator();
                    return {
                        ...cached,
                        cached: true,
                        warning: 'Ошибка сети. Показаны кэшированные данные.'
                    };
                }
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            // При ошибке API пытаемся вернуть кэш
            if (!forceRefresh && window.Offline) {
                const cached = window.Offline.getCachedChats();
                if (cached) {
                    console.log('[ChatsAPI] Ошибка API, используем кэшированные данные');
                    window.Offline.showOfflineIndicator();
                    return {
                        ...cached,
                        cached: true,
                        warning: 'Ошибка сервера. Показаны кэшированные данные.'
                    };
                }
            }
            throw new Error(data.error);
        }
        
        // Сохраняем в кэш при успешном запросе
        if (window.Offline && data.success && data.chats) {
            window.Offline.cacheChats(data);
        }
        
        return data;
    } catch (error) {
        // При любой ошибке пытаемся вернуть кэш
        if (!forceRefresh && window.Offline) {
            const cached = window.Offline.getCachedChats();
            if (cached) {
                console.log('[ChatsAPI] Ошибка запроса, используем кэшированные данные:', error);
                window.Offline.showOfflineIndicator();
                return {
                    ...cached,
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
    window.ChatsAPI = {
        loadChats
    };
}
