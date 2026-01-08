// Управление состоянием загрузки

let loadingElement: HTMLElement | null = null;
let chatsContainer: HTMLElement | null = null;

/**
 * Инициализация элементов загрузки
 */
export function initLoadingElements(): void {
    loadingElement = document.querySelector('.loading');
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
 * Показать загрузку
 */
export function showLoading(): void {
    if (!loadingElement) {
        initLoadingElements();
    }
    if (loadingElement) {
        loadingElement.style.display = 'flex';
    }
    if (chatsContainer) {
        // Показываем skeleton screens вместо пустого контейнера
        chatsContainer.innerHTML = generateSkeletonChats();
    }
}

/**
 * Скрыть загрузку
 */
export function hideLoading(): void {
    if (!loadingElement) {
        initLoadingElements();
    }
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}
