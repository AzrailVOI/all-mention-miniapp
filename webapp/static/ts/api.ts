// API запросы
import { applyFilters, setCurrentChats } from './filters.js';
import { hideLoading, showLoading } from './loading.js';
import { renderStats } from './stats.js';
import type { ChatListResponse } from './types.js';
import { showError, showToast } from './utils.js';

const API_URL = '/api/chats';

/**
 * Загрузка списка чатов
 */
export async function loadChats(): Promise<void> {
    try {
        showLoading();
        
        const tg = window.Telegram?.WebApp;
        if (!tg) {
            throw new Error('Telegram WebApp не инициализирован');
        }
        
        // Получаем данные пользователя из Telegram WebApp
        const initData = tg.initData;
        const user = tg.initDataUnsafe?.user;
        
        // Отправляем запрос на сервер
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                init_data: initData,
                user_id: user?.id
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: ChatListResponse = await response.json();
        
        if (!data.success) {
            showError(data.error || 'Не удалось загрузить список чатов');
            return;
        }
        
        // Показываем предупреждение, если данные из кэша
        if (data.cached && data.warning) {
            showToast(data.warning, 'warning');
        }
        
        // Сохраняем данные для фильтрации
        setCurrentChats(data.chats || [], data.stats);
        
        renderStats(data.stats);
        // Применяем фильтры (которые отобразят чаты)
        applyFilters();
        
    } catch (error) {
        console.error('Error loading chats:', error);
        showError('Не удалось загрузить список чатов. Попробуйте обновить страницу.');
    } finally {
        hideLoading();
    }
}

/**
 * Удаление чата из списка
 */
export async function deleteChat(chatId: number, chatTitle: string): Promise<void> {
    if (!confirm(`Вы уверены, что хотите удалить чат "${chatTitle}" из списка?`)) {
        return;
    }
    
    try {
        const tg = window.Telegram?.WebApp;
        if (!tg) {
            throw new Error('Telegram WebApp не инициализирован');
        }
        
        // Отправляем запрос на удаление
        const response = await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: tg.initDataUnsafe?.user?.id
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка при удалении чата');
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Чат успешно удален из списка', 'success');
            // Обновляем список чатов
            await loadChats();
        } else {
            showToast(data.error || 'Не удалось удалить чат', 'error');
        }
    } catch (error) {
        console.error('Error deleting chat:', error);
        showToast('Ошибка при удалении чата', 'error');
    }
}

/**
 * Открыть страницу участников чата
 */
export function openChat(chatId: number, chatTitle: string): void {
    const encodedTitle = encodeURIComponent(chatTitle || 'Участники чата');
    window.history.pushState({ page: 'members', chatId, chatTitle }, '', `/members?chat_id=${chatId}&title=${encodedTitle}`);
    window.location.href = `/members?chat_id=${chatId}&title=${encodedTitle}`;
}

// Экспортируем функции в глобальную область для использования в HTML
declare global {
    interface Window {
        loadChats: () => Promise<void>;
        deleteChat: (chatId: number, chatTitle: string) => Promise<void>;
        openChat: (chatId: number, chatTitle: string) => void;
    }
}

window.loadChats = loadChats;
window.deleteChat = deleteChat;
window.openChat = openChat;
