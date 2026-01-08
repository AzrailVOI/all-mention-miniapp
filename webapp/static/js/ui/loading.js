/**
 * Управление состоянием загрузки
 */

/**
 * Показывает индикатор загрузки
 * @param {HTMLElement} loadingElement - Элемент индикатора загрузки
 * @param {HTMLElement} contentContainer - Контейнер контента (опционально)
 */
function showLoading(loadingElement, contentContainer = null) {
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
    if (contentContainer) {
        contentContainer.innerHTML = '';
    }
}

/**
 * Скрывает индикатор загрузки
 * @param {HTMLElement} loadingElement - Элемент индикатора загрузки
 */
function hideLoading(loadingElement) {
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Loading = {
        show: showLoading,
        hide: hideLoading
    };
}
