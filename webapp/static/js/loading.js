// Управление состоянием загрузки

let chatsContainer = null;

/**
 * Инициализация элементов загрузки
 */
function initLoadingElements() {
    chatsContainer = document.querySelector('.chat-list');
}

/**
 * Генерация skeleton screens для чатов
 */
function generateSkeletonChats() {
    const skeletonCount = 5;
    let html = '';
    for (let i = 0; i < skeletonCount; i++) {
        html += `
            <div class="skeleton-chat-item">
                <div class="skeleton skeleton-avatar"></div>
                <div style="flex: 1;">
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text skeleton-text-short"></div>
                </div>
            </div>
        `;
    }
    return html;
}

/**
 * Показать загрузку (только skeleton screens)
 */
function showLoading() {
    if (!chatsContainer) {
        initLoadingElements();
    }
    if (chatsContainer) {
        // Показываем только skeleton screens
        chatsContainer.innerHTML = generateSkeletonChats();
    }
}

/**
 * Скрыть загрузку (пустая функция, skeleton просто заменяется контентом)
 */
function hideLoading() {
    // Skeleton автоматически заменяется контентом при рендеринге
    // Ничего не делаем
}

// Экспорт в window
window.showLoading = showLoading;
window.hideLoading = hideLoading;
