/**
 * Навигация и переходы между страницами
 */

/**
 * Открывает страницу участников чата
 * @param {number} chatId - ID чата
 * @param {string} chatTitle - Название чата
 */
function openChat(chatId, chatTitle) {
    // Переходим на отдельную страницу участников
    const encodedTitle = encodeURIComponent(chatTitle || 'Участники чата');
    // Используем pushState для правильной работы кнопки назад
    window.history.pushState({ page: 'members', chatId, chatTitle }, '', `/members?chat_id=${chatId}&title=${encodedTitle}`);
    window.location.href = `/members?chat_id=${chatId}&title=${encodedTitle}`;
}

/**
 * Возвращается на главную страницу
 */
function goBack() {
    // Всегда возвращаемся на главную страницу
    window.location.href = '/';
}

/**
 * Открывает профиль пользователя в Telegram
 * @param {string} profileLink - Ссылка на профиль
 */
function openProfile(profileLink) {
    const tg = window.Telegram.WebApp;
    
    // Используем Telegram WebApp API для открытия профиля
    if (tg.openTelegramLink) {
        tg.openTelegramLink(profileLink);
    } else if (tg.openLink) {
        tg.openLink(profileLink);
    } else {
        // Fallback: открываем в новом окне
        window.open(profileLink, '_blank');
    }
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Navigation = {
        openChat,
        goBack,
        openProfile
    };
    
    // Для обратной совместимости
    window.openChat = openChat;
    window.goBack = goBack;
    window.openProfile = openProfile;
}
