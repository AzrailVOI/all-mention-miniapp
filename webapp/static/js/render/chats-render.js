/**
 * Рендеринг списка чатов
 */

/**
 * Отображает список чатов
 * @param {Array} chats - Массив чатов
 * @param {string} infoMessage - Информационное сообщение (опционально)
 * @param {HTMLElement} container - Контейнер для отображения
 */
function renderChats(chats, infoMessage, container) {
    if (!container) return;
    
    if (!chats || chats.length === 0) {
        let emptyContent = `
            <div class="empty-state">
                <i data-lucide="message-square" style="width: 48px; height: 48px; opacity: 0.3; margin-bottom: 16px;"></i>
                <p>Бот еще не добавлен ни в один чат</p>
        `;
        
        if (infoMessage) {
            emptyContent += `
                <div style="margin-top: 20px; padding: 16px; background: #fafafa; border: 1px solid #e0e0e0; text-align: left; font-size: 13px; line-height: 1.6;">
                    ${window.escapeHtml ? window.escapeHtml(infoMessage).replace(/\n/g, '<br>') : infoMessage.replace(/\n/g, '<br>')}
                </div>
            `;
        }
        
        emptyContent += `</div>`;
        container.innerHTML = emptyContent;
        
        if (window.lucide) {
            window.lucide.createIcons();
        }
        return;
    }
    
    container.innerHTML = chats.map(chat => {
        const chatTitle = window.escapeHtml ? window.escapeHtml(chat.title || 'Без названия') : (chat.title || 'Без названия');
        const chatInitials = chatTitle.substring(0, 2).toUpperCase();
        
        console.log(`[Frontend] Обработка чата ${chat.id} (${chatTitle}): photo_url = ${chat.photo_url || 'отсутствует'}`);
        
        // Формируем аватарку чата
        let avatarHtml = '';
        if (chat.photo_url) {
            const photoUrl = chat.photo_url;
            console.log(`[Frontend] Чат ${chat.id}: есть photo_url = ${photoUrl}`);
            
            const urlLower = photoUrl.toLowerCase();
            const isVideo = urlLower.includes('.mp4') || urlLower.includes('.mov') || urlLower.includes('video');
            
            if (isVideo) {
                // Видео аватарка
                console.log(`[Frontend] Чат ${chat.id}: определяем как видео`);
                avatarHtml = `<video class="chat-avatar-img" autoplay loop muted playsinline><source src="${window.escapeHtml ? window.escapeHtml(photoUrl) : photoUrl}" type="video/mp4"></video>`;
            } else {
                // Обычное фото или GIF
                console.log(`[Frontend] Чат ${chat.id}: определяем как фото/GIF`);
                avatarHtml = `<img class="chat-avatar-img" src="${window.escapeHtml ? window.escapeHtml(photoUrl) : photoUrl}" alt="${chatTitle}" onerror="console.error('[Frontend] Ошибка загрузки фото чата ${chat.id}'); this.parentElement.innerHTML='<div class=\\'chat-avatar-text\\'>${chatInitials}</div>'" />`;
            }
        } else {
            // Если нет фото, показываем иконку
            console.log(`[Frontend] Чат ${chat.id}: нет photo_url, показываем иконку`);
            avatarHtml = `<div class="chat-avatar-icon">${window.getChatIcon ? window.getChatIcon(chat.type) : ''}</div>`;
        }
        
        return `
        <div class="chat-item" onclick="window.openChat(${chat.id}, '${chatTitle.replace(/'/g, "\\'")}')">
            <div class="chat-avatar">
                ${avatarHtml}
            </div>
            <div class="chat-info">
                <div class="chat-name">${chatTitle}</div>
                <div class="chat-details">
                    <span class="chat-type ${chat.type}">${window.getChatTypeLabel ? window.getChatTypeLabel(chat.type) : chat.type}</span>
                    ${chat.members_count ? `<span><i data-lucide="user" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle;"></i> ${chat.members_count}</span>` : ''}
                </div>
            </div>
            <div class="chat-arrow">
                <i data-lucide="chevron-right"></i>
            </div>
        </div>
    `;
    }).join('');
    
    // Инициализируем иконки
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// Экспорт
if (typeof window !== 'undefined') {
    window.ChatsRender = {
        renderChats
    };
}
