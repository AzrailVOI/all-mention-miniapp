/**
 * Модуль для отображения Toast уведомлений
 */

/**
 * Показывает Toast уведомление
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип уведомления ('success', 'error', 'warning', 'info')
 * @param {number} duration - Длительность отображения в миллисекундах (по умолчанию 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    // Создаем контейнер для Toast, если его еще нет
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Создаем элемент Toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Иконка в зависимости от типа
    const icons = {
        'success': 'check-circle',
        'error': 'alert-circle',
        'warning': 'alert-triangle',
        'info': 'info'
    };
    
    const icon = icons[type] || 'info';
    
    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-icon">
                <i data-lucide="${icon}"></i>
            </div>
            <div class="toast-message">${window.escapeHtml ? window.escapeHtml(message) : message}</div>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                <i data-lucide="x"></i>
            </button>
        </div>
    `;
    
    // Добавляем Toast в контейнер
    toastContainer.appendChild(toast);
    
    // Инициализируем иконки Lucide
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // Анимация появления
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Автоматическое скрытие
    const hideTimeout = setTimeout(() => {
        hideToast(toast);
    }, duration);
    
    // Останавливаем таймер при наведении
    toast.addEventListener('mouseenter', () => {
        clearTimeout(hideTimeout);
    });
    
    // Возобновляем таймер при уходе курсора
    toast.addEventListener('mouseleave', () => {
        setTimeout(() => {
            hideToast(toast);
        }, 1000);
    });
}

/**
 * Скрывает Toast уведомление
 * @param {HTMLElement} toast - Элемент Toast для скрытия
 */
function hideToast(toast) {
    if (!toast) return;
    
    toast.classList.remove('show');
    toast.classList.add('hide');
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 300);
}

// Экспорт
if (typeof window !== 'undefined') {
    window.Toast = {
        show: showToast,
        hide: hideToast
    };
    // Глобальная функция для удобства
    window.showToast = showToast;
}
