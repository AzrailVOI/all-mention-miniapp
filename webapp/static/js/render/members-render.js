/**
 * Рендеринг списка участников чата
 */

/**
 * Отображает список участников чата
 * @param {Array} members - Массив участников
 * @param {HTMLElement} container - Контейнер для отображения
 */
function renderMembers(members, container) {
    if (!container) return;
    
    if (!members || members.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i data-lucide="users"></i>
                </div>
                <h3 class="empty-state-title">Участники не найдены</h3>
                <p class="empty-state-description">
                    В этом чате нет участников или они недоступны.<br>
                    Убедитесь, что бот является администратором чата.
                </p>
                <div class="empty-state-actions">
                    <button class="refresh-btn" onclick="location.reload()">
                        <i data-lucide="refresh-cw"></i>
                        <span>Обновить</span>
                    </button>
                </div>
            </div>
        `;
        
        if (window.lucide) {
            window.lucide.createIcons();
        }
        return;
    }
    
    // Сортируем: сначала создатель, потом администраторы, потом остальные
    const sortedMembers = [...members].sort((a, b) => {
        if (a.status === 'creator') return -1;
        if (b.status === 'creator') return 1;
        if (a.status === 'administrator') return -1;
        if (b.status === 'administrator') return 1;
        return 0;
    });
    
    container.innerHTML = sortedMembers.map(member => {
        const name = member.first_name + (member.last_name ? ' ' + member.last_name : '');
        const displayName = name || member.username || `User ${member.id}`;
        const initials = (member.first_name?.[0] || member.username?.[0] || 'U').toUpperCase();
        
        console.log(`[Frontend] Обработка участника ${member.id} (${displayName}): profile_photo_url = ${member.profile_photo_url || 'отсутствует'}`);
        
        // Формируем аватарку
        let avatarHtml = '';
        if (member.profile_photo_url) {
            // Проверяем тип файла по расширению
            const photoUrl = member.profile_photo_url;
            console.log(`[Frontend] Участник ${member.id}: есть profile_photo_url = ${photoUrl}`);
            
            const urlLower = photoUrl.toLowerCase();
            const isVideo = urlLower.includes('.mp4') || urlLower.includes('.mov') || urlLower.includes('video');
            
            if (isVideo) {
                // Видео аватарка с автопроигрыванием
                console.log(`[Frontend] Участник ${member.id}: определяем как видео`);
                avatarHtml = `<video class="member-avatar-img" autoplay loop muted playsinline><source src="${window.escapeHtml ? window.escapeHtml(photoUrl) : photoUrl}" type="video/mp4"></video>`;
            } else {
                // Обычное фото или GIF
                console.log(`[Frontend] Участник ${member.id}: определяем как фото/GIF`);
                avatarHtml = `<img class="member-avatar-img" src="${window.escapeHtml ? window.escapeHtml(photoUrl) : photoUrl}" alt="${window.escapeHtml ? window.escapeHtml(displayName) : displayName}" onerror="console.error('[Frontend] Ошибка загрузки фото участника ${member.id}'); this.parentElement.innerHTML='<div class=\\'member-avatar-text\\'>${initials}</div>'" />`;
            }
        } else {
            // Если нет фото, показываем инициалы
            console.log(`[Frontend] Участник ${member.id}: нет profile_photo_url, показываем инициалы`);
            avatarHtml = `<div class="member-avatar-text">${initials}</div>`;
        }
        
        let statusBadge = '';
        if (member.status === 'creator') {
            statusBadge = '<span class="member-badge creator">Создатель</span>';
        } else if (member.status === 'administrator') {
            statusBadge = '<span class="member-badge admin">Админ</span>';
        }
        
        if (member.is_bot) {
            statusBadge = '<span class="member-badge bot">Бот</span>';
        }
        
        // Формируем ссылку для открытия профиля
        let profileLink = '';
        if (member.username) {
            profileLink = `https://t.me/${member.username}`;
        } else {
            profileLink = `tg://user?id=${member.id}`;
        }
        
        return `
            <div class="member-item">
                <div class="member-avatar">
                    ${avatarHtml}
                </div>
                <div class="member-info">
                    <div class="member-name">${window.escapeHtml ? window.escapeHtml(displayName) : displayName}</div>
                    <div class="member-details">
                        ${statusBadge}
                        ${member.username ? `<span>@${window.escapeHtml ? window.escapeHtml(member.username) : member.username}</span>` : ''}
                    </div>
                </div>
                <button class="member-profile-btn" onclick="window.openProfile('${window.escapeHtml ? window.escapeHtml(profileLink) : profileLink}')" title="Открыть профиль">
                    <i data-lucide="external-link"></i>
                </button>
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
    window.MembersRender = {
        renderMembers
    };
}
