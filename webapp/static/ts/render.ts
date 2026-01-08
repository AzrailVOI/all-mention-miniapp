// Рендеринг чатов
import type { Chat } from './types';
import { escapeHtml, getChatIcon, getChatTypeLabel } from './utils';

let chatsContainer: HTMLElement | null = null;

/**
 * Инициализация контейнера чатов
 */
export function initChatsContainer(): void {
    chatsContainer = document.querySelector('.chat-list');
}

/**
 * Отображение списка чатов
 */
export function renderChats(chats: Chat[] | null, infoMessage: string | null): void {
    if (!chatsContainer) {
        initChatsContainer();
    }
    if (!chatsContainer) return;
    
    if (!chats || chats.length === 0) {
        let emptyContent = `
            <div class="empty-state">
                <i data-lucide="message-square" style="width: 64px; height: 64px; opacity: 0.3; margin-bottom: 20px;"></i>
                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 12px; color: #1a1a1a;">Чаты не найдены</h3>
                <p style="color: #666; margin-bottom: 20px; line-height: 1.6;">
                    Бот еще не добавлен ни в один чат или у вас нет доступа к чатам.
                </p>
        `;
        
        if (infoMessage) {
            emptyContent += `
                <div class="info-box" style="margin-top: 20px; padding: 20px; background: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 8px; text-align: left; font-size: 14px; line-height: 1.7; color: #555;">
                    <strong style="display: block; margin-bottom: 12px; color: #1a1a1a;">ℹ️ Информация:</strong>
                    ${escapeHtml(infoMessage).replace(/\n/g, '<br>')}
                </div>
            `;
        }
        
        emptyContent += `
            <div style="margin-top: 24px;">
                <button class="refresh-btn" id="refresh-empty-btn" type="button" style="margin: 0 auto;">
                    <i data-lucide="refresh-cw" style="width: 16px; height: 16px; margin-right: 8px;"></i>
                    Обновить список
                </button>
            </div>
        </div>`;
        chatsContainer.innerHTML = emptyContent;
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
        // Добавляем обработчик для кнопки обновления
        const refreshBtn = chatsContainer.querySelector('#refresh-empty-btn');
        if (refreshBtn && window.loadChats) {
            refreshBtn.addEventListener('click', () => {
                window.loadChats();
            });
        }
        
        return;
    }
    
    chatsContainer.innerHTML = chats.map(chat => {
        const chatTitle = escapeHtml(chat.title || 'Без названия');
        const chatInitials = chatTitle.substring(0, 2).toUpperCase();
        
        // Формируем аватарку чата
        let avatarHtml = '';
        if (chat.photo_url) {
            const photoUrl = chat.photo_url;
            const urlLower = photoUrl.toLowerCase();
            const isVideo = urlLower.includes('.mp4') || urlLower.includes('.mov') || urlLower.includes('video');
            
            if (isVideo) {
                avatarHtml = `<video class="chat-avatar-img" autoplay loop muted playsinline><source src="${escapeHtml(photoUrl)}" type="video/mp4"></video>`;
            } else {
                avatarHtml = `<img class="chat-avatar-img" src="${escapeHtml(photoUrl)}" alt="${chatTitle}" onerror="console.error('[Frontend] Ошибка загрузки фото чата ${chat.id}'); this.parentElement.innerHTML='<div class=\\'chat-avatar-text\\'>${chatInitials}</div>'" />`;
            }
        } else {
            avatarHtml = `<div class="chat-avatar-icon">${getChatIcon(chat.type)}</div>`;
        }
        
        const escapedTitle = escapeHtml(chatTitle);
        return `
        <div class="chat-item" data-chat-id="${chat.id}" data-chat-title="${escapedTitle}">
            <div class="chat-avatar">
                ${avatarHtml}
            </div>
            <div class="chat-info">
                <div class="chat-name">${escapeHtml(chat.title || 'Без названия')}</div>
                <div class="chat-details">
                    <span class="chat-type ${chat.type}">${getChatTypeLabel(chat.type)}</span>
                    ${chat.members_count ? `<span><i data-lucide="user" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle;"></i> ${chat.members_count}</span>` : ''}
                </div>
            </div>
            <div class="chat-actions">
                <button class="chat-delete-btn" data-chat-id="${chat.id}" data-chat-title="${escapedTitle}" title="Удалить чат из списка">
                    <i data-lucide="trash-2"></i>
                </button>
                <i data-lucide="chevron-right" class="chat-arrow"></i>
            </div>
        </div>
    `;
    }).join('');
    
    // Инициализируем иконки
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // Добавляем обработчики событий для чатов
    setTimeout(() => {
        const chatItems = chatsContainer.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            const chatIdAttr = item.getAttribute('data-chat-id');
            const chatTitleAttr = item.getAttribute('data-chat-title');
            if (!chatIdAttr || !chatTitleAttr) return;
            
            const chatId = parseInt(chatIdAttr);
            const chatTitle = decodeURIComponent(chatTitleAttr);
            
            // Обработчик клика по элементу чата
            item.addEventListener('click', (e) => {
                // Не открываем чат, если клик был по кнопке удаления
                if ((e.target as HTMLElement).closest('.chat-delete-btn')) {
                    return;
                }
                if (window.openChat) {
                    window.openChat(chatId, chatTitle);
                }
            });
            
            // Обработчик кнопки удаления
            const deleteBtn = item.querySelector('.chat-delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (window.deleteChat) {
                        await window.deleteChat(chatId, chatTitle);
                    }
                });
            }
        });
    }, 0);
}
