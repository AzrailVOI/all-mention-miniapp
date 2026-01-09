/**
 * Модуль для отображения Skeleton Screens (скелетонов загрузки)
 */

/**
 * Создает skeleton элемент для чата
 * @returns {HTMLElement} Skeleton элемент
 */
function createChatSkeleton() {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-chat-item';
    skeleton.innerHTML = `
        <div class="skeleton-avatar"></div>
        <div class="skeleton-content">
            <div class="skeleton-line skeleton-title"></div>
            <div class="skeleton-line skeleton-subtitle"></div>
        </div>
        <div class="skeleton-arrow"></div>
    `;
    return skeleton;
}

/**
 * Создает skeleton элемент для участника
 * @returns {HTMLElement} Skeleton элемент
 */
function createMemberSkeleton() {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-member-item';
    skeleton.innerHTML = `
        <div class="skeleton-avatar"></div>
        <div class="skeleton-content">
            <div class="skeleton-line skeleton-title"></div>
            <div class="skeleton-line skeleton-subtitle"></div>
        </div>
    `;
    return skeleton;
}

/**
 * Создает skeleton элемент для статистики
 * @returns {HTMLElement} Skeleton элемент
 */
function createStatSkeleton() {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-stat-card';
    skeleton.innerHTML = `
        <div class="skeleton-icon"></div>
        <div class="skeleton-line skeleton-value"></div>
        <div class="skeleton-line skeleton-label"></div>
    `;
    return skeleton;
}

/**
 * Показывает skeleton screens для списка чатов
 * @param {HTMLElement} container - Контейнер для отображения
 * @param {number} count - Количество skeleton элементов (по умолчанию 5)
 */
function showChatsSkeleton(container, count = 5) {
    if (!container) return;
    
    container.innerHTML = '';
    container.classList.add('skeleton-container');
    
    for (let i = 0; i < count; i++) {
        const skeleton = createChatSkeleton();
        container.appendChild(skeleton);
    }
}

/**
 * Показывает skeleton screens для списка участников
 * @param {HTMLElement} container - Контейнер для отображения
 * @param {number} count - Количество skeleton элементов (по умолчанию 10)
 */
function showMembersSkeleton(container, count = 10) {
    if (!container) return;
    
    container.innerHTML = '';
    container.classList.add('skeleton-container');
    
    for (let i = 0; i < count; i++) {
        const skeleton = createMemberSkeleton();
        container.appendChild(skeleton);
    }
}

/**
 * Показывает skeleton screens для статистики
 * @param {HTMLElement} container - Контейнер для отображения
 * @param {number} count - Количество skeleton элементов (по умолчанию 3)
 */
function showStatsSkeleton(container, count = 3) {
    if (!container) return;
    
    container.innerHTML = '';
    container.classList.add('skeleton-container', 'skeleton-stats');
    
    for (let i = 0; i < count; i++) {
        const skeleton = createStatSkeleton();
        container.appendChild(skeleton);
    }
}

/**
 * Скрывает skeleton screens
 * @param {HTMLElement} container - Контейнер со skeleton элементами
 */
function hideSkeleton(container) {
    if (!container) return;
    
    container.classList.remove('skeleton-container', 'skeleton-stats');
    // Skeleton элементы будут заменены реальным контентом
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Skeleton = {
        showChats: showChatsSkeleton,
        showMembers: showMembersSkeleton,
        showStats: showStatsSkeleton,
        hide: hideSkeleton,
        createChat: createChatSkeleton,
        createMember: createMemberSkeleton,
        createStat: createStatSkeleton
    };
}
