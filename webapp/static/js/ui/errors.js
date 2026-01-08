/**
 * Обработка и отображение ошибок
 */

/**
 * Показывает сообщение об ошибке
 * @param {string} message - Текст ошибки
 * @param {HTMLElement} container - Контейнер для отображения ошибки
 */
function showError(message, container) {
    if (!container) return;
    
    const escapedMessage = window.escapeHtml ? window.escapeHtml(message) : message;
    
    container.innerHTML = `
        <div class="error">
            <strong>Ошибка:</strong> ${escapedMessage}
        </div>
        <button class="refresh-btn" onclick="location.reload()">Обновить</button>
    `;
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Errors = {
        show: showError
    };
}
