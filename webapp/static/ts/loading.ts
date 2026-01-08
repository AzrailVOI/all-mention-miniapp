// Управление состоянием загрузки (только skeleton screens)

let chatsContainer: HTMLElement | null = null;

/**
 * Инициализация элементов загрузки
 */
export function initLoadingElements(): void {
    chatsContainer = document.querySelector('.chat-list');
}

/**
 * Генерация skeleton screens для чатов
 */
function generateSkeletonChats(): string {
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
export function showLoading(): void {
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
export function hideLoading(): void {
    // Skeleton автоматически заменяется контентом при рендеринге
    // Ничего не делаем
}
