/**
 * Модуль для работы с offline режимом и кэшированием данных
 */

const CACHE_PREFIX = 'all_mention_cache_';
const CACHE_KEYS = {
    CHATS: 'chats',
    MEMBERS: 'members',
    STATS: 'stats'
};

/**
 * Проверяет, находится ли приложение в offline режиме
 * @returns {boolean} True, если приложение offline
 */
function isOffline() {
    return !navigator.onLine;
}

/**
 * Сохраняет данные в localStorage
 * @param {string} key - Ключ для сохранения
 * @param {*} data - Данные для сохранения
 * @param {number} ttl - Время жизни в миллисекундах (по умолчанию 5 минут)
 */
function saveToCache(key, data, ttl = 5 * 60 * 1000) {
    try {
        const cacheData = {
            data: data,
            timestamp: Date.now(),
            ttl: ttl
        };
        localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(cacheData));
    } catch (error) {
        console.warn('[Offline] Не удалось сохранить в кэш:', error);
    }
}

/**
 * Получает данные из localStorage
 * @param {string} key - Ключ для получения
 * @returns {*|null} Данные или null, если кэш истек или отсутствует
 */
function getFromCache(key) {
    try {
        const cached = localStorage.getItem(CACHE_PREFIX + key);
        if (!cached) {
            return null;
        }
        
        const cacheData = JSON.parse(cached);
        const now = Date.now();
        
        // Проверяем, не истек ли кэш
        if (now - cacheData.timestamp > cacheData.ttl) {
            localStorage.removeItem(CACHE_PREFIX + key);
            return null;
        }
        
        return cacheData.data;
    } catch (error) {
        console.warn('[Offline] Не удалось получить из кэша:', error);
        return null;
    }
}

/**
 * Очищает кэш
 * @param {string} key - Ключ для очистки (если не указан, очищает весь кэш)
 */
function clearCache(key = null) {
    try {
        if (key) {
            localStorage.removeItem(CACHE_PREFIX + key);
        } else {
            // Очищаем весь кэш приложения
            Object.keys(localStorage).forEach(k => {
                if (k.startsWith(CACHE_PREFIX)) {
                    localStorage.removeItem(k);
                }
            });
        }
    } catch (error) {
        console.warn('[Offline] Не удалось очистить кэш:', error);
    }
}

/**
 * Сохраняет список чатов в кэш
 * @param {Object} data - Данные чатов (chats, stats, info)
 */
function cacheChats(data) {
    saveToCache(CACHE_KEYS.CHATS, data, 10 * 60 * 1000); // 10 минут
}

/**
 * Получает список чатов из кэша
 * @returns {Object|null} Данные чатов или null
 */
function getCachedChats() {
    return getFromCache(CACHE_KEYS.CHATS);
}

/**
 * Сохраняет список участников в кэш
 * @param {number} chatId - ID чата
 * @param {Array} members - Список участников
 */
function cacheMembers(chatId, members) {
    saveToCache(`${CACHE_KEYS.MEMBERS}_${chatId}`, members, 30 * 60 * 1000); // 30 минут
}

/**
 * Получает список участников из кэша
 * @param {number} chatId - ID чата
 * @returns {Array|null} Список участников или null
 */
function getCachedMembers(chatId) {
    return getFromCache(`${CACHE_KEYS.MEMBERS}_${chatId}`);
}

/**
 * Показывает индикатор offline режима
 */
function showOfflineIndicator() {
    if (window.showToast) {
        window.showToast('Нет подключения к интернету. Показаны кэшированные данные.', 'warning', 5000);
    }
}

/**
 * Показывает индикатор восстановления соединения
 */
function showOnlineIndicator() {
    if (window.showToast) {
        window.showToast('Подключение восстановлено', 'success', 3000);
    }
}

/**
 * Инициализирует обработчики событий online/offline
 */
function initOfflineHandlers() {
    window.addEventListener('online', () => {
        console.log('[Offline] Подключение восстановлено');
        showOnlineIndicator();
    });
    
    window.addEventListener('offline', () => {
        console.log('[Offline] Потеряно подключение к интернету');
        if (window.showToast) {
            window.showToast('Нет подключения к интернету', 'error', 5000);
        }
    });
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Offline = {
        isOffline,
        saveToCache,
        getFromCache,
        clearCache,
        cacheChats,
        getCachedChats,
        cacheMembers,
        getCachedMembers,
        showOfflineIndicator,
        showOnlineIndicator,
        initOfflineHandlers
    };
}
