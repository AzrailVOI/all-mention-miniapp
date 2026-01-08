// Утилиты
import type { Chat } from './types';

/**
 * Экранирование HTML для предотвращения XSS
 */
export function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Получить иконку для типа чата
 */
export function getChatIcon(type: string): string {
    const icons: Record<string, string> = {
        'group': '<i data-lucide="users"></i>',
        'supergroup': '<i data-lucide="users-round"></i>',
        'private': '<i data-lucide="user"></i>',
        'channel': '<i data-lucide="megaphone"></i>'
    };
    return icons[type] || '<i data-lucide="message-square"></i>';
}

/**
 * Получить метку для типа чата
 */
export function getChatTypeLabel(type: string): string {
    const labels: Record<string, string> = {
        'group': 'Группа',
        'supergroup': 'Супергруппа',
        'private': 'Приватный',
        'channel': 'Канал'
    };
    return labels[type] || type;
}

/**
 * Показать toast уведомление
 */
export function showToast(message: string, type: 'info' | 'success' | 'error' | 'warning' = 'info'): void {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Анимация появления
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Показать ошибку
 */
export function showError(message: string): void {
    const chatsContainer = document.querySelector('.chat-list');
    if (chatsContainer) {
        chatsContainer.innerHTML = `
            <div class="error">
                <strong>Ошибка:</strong> ${escapeHtml(message)}
            </div>
            <button class="refresh-btn" id="refresh-error-btn" type="button">Обновить</button>
        `;
        
        // Добавляем обработчик для кнопки обновления
        const refreshBtn = chatsContainer.querySelector('#refresh-error-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                location.reload();
            });
        }
        
        // Инициализируем иконки
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
}
