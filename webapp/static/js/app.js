// Telegram WebApp API
const tg = window.Telegram.WebApp;

// Инициализация WebApp
tg.ready();
tg.expand();

// Элементы DOM
const statsContainer = document.querySelector('.stats');
const chatsContainer = document.querySelector('.chat-list');
const loadingElement = document.querySelector('.loading');

// API endpoint
const API_URL = '/api/chats';

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем иконки Lucide
    lucide.createIcons();
    
    await loadChats();
    
    // Обработчик кнопки обновления
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            await loadChats();
        });
    }
    
    // Обработчик поиска по Enter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // Закрытие модального окна при клике вне его
    const modal = document.getElementById('membersModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeMembersModal();
            }
        });
    }
});

// Загрузка списка чатов
async function loadChats() {
    try {
        showLoading();
        
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
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        renderStats(data.stats);
        renderChats(data.chats, data.info);
        
    } catch (error) {
        console.error('Error loading chats:', error);
        showError('Не удалось загрузить список чатов. Попробуйте обновить страницу.');
    } finally {
        hideLoading();
    }
}

// Отображение статистики
function renderStats(stats) {
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon"><i data-lucide="message-square"></i></div>
            <div class="stat-value">${stats.total || 0}</div>
            <div class="stat-label">Всего чатов</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i data-lucide="users"></i></div>
            <div class="stat-value">${stats.groups || 0}</div>
            <div class="stat-label">Группы</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i data-lucide="users-round"></i></div>
            <div class="stat-value">${stats.supergroups || 0}</div>
            <div class="stat-label">Супергруппы</div>
        </div>
    `;
    
    // Инициализируем иконки
    lucide.createIcons();
}

// Отображение списка чатов
function renderChats(chats, infoMessage) {
    if (!chatsContainer) return;
    
    if (!chats || chats.length === 0) {
        let emptyContent = `
            <div class="empty-state">
                <i data-lucide="message-square" style="width: 48px; height: 48px; opacity: 0.3; margin-bottom: 16px;"></i>
                <p>Бот еще не добавлен ни в один чат</p>
        `;
        
        if (infoMessage) {
            emptyContent += `
                <div style="margin-top: 20px; padding: 16px; background: #fafafa; border: 1px solid #e0e0e0; text-align: left; font-size: 13px; line-height: 1.6;">
                    ${escapeHtml(infoMessage).replace(/\n/g, '<br>')}
                </div>
            `;
        }
        
        emptyContent += `</div>`;
        chatsContainer.innerHTML = emptyContent;
        lucide.createIcons();
        return;
    }
    
    chatsContainer.innerHTML = chats.map(chat => `
        <div class="chat-item" onclick="openChat(${chat.id}, '${escapeHtml(chat.title || 'Без названия')}')">
            <div class="chat-icon">
                ${getChatIcon(chat.type)}
            </div>
            <div class="chat-info">
                <div class="chat-name">${escapeHtml(chat.title || 'Без названия')}</div>
                <div class="chat-details">
                    <span class="chat-type ${chat.type}">${getChatTypeLabel(chat.type)}</span>
                    ${chat.members_count ? `<span><i data-lucide="user" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle;"></i> ${chat.members_count}</span>` : ''}
                </div>
            </div>
            <div class="chat-arrow">
                <i data-lucide="chevron-right"></i>
            </div>
        </div>
    `).join('');
    
    // Инициализируем иконки
    lucide.createIcons();
}

// Получить иконку для типа чата
function getChatIcon(type) {
    const icons = {
        'group': '<i data-lucide="users"></i>',
        'supergroup': '<i data-lucide="users-round"></i>',
        'private': '<i data-lucide="user"></i>',
        'channel': '<i data-lucide="megaphone"></i>'
    };
    return icons[type] || '<i data-lucide="message-square"></i>';
}

// Получить метку для типа чата
function getChatTypeLabel(type) {
    const labels = {
        'group': 'Группа',
        'supergroup': 'Супергруппа',
        'private': 'Приватный',
        'channel': 'Канал'
    };
    return labels[type] || type;
}

// Открыть чат и показать участников
async function openChat(chatId, chatTitle) {
    const modal = document.getElementById('membersModal');
    const modalTitle = document.getElementById('modalTitle');
    const membersList = document.getElementById('membersList');
    const membersLoading = document.getElementById('membersLoading');
    
    if (!modal) return;
    
    // Устанавливаем заголовок
    modalTitle.textContent = chatTitle || 'Участники чата';
    
    // Показываем модальное окно
    modal.style.display = 'flex';
    
    // Показываем загрузку
    membersLoading.style.display = 'block';
    membersList.innerHTML = '';
    
    try {
        // Получаем данные пользователя
        const user = tg.initDataUnsafe?.user;
        
        // Загружаем участников
        const response = await fetch(`/api/chats/${chatId}/members`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: user?.id
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Не удалось загрузить участников');
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Ошибка при загрузке участников');
        }
        
        // Скрываем загрузку
        membersLoading.style.display = 'none';
        
        // Отображаем участников
        renderMembers(data.members);
        
    } catch (error) {
        console.error('Error loading members:', error);
        membersLoading.style.display = 'none';
        membersList.innerHTML = `
            <div class="error">
                <strong>Ошибка:</strong> ${escapeHtml(error.message || 'Не удалось загрузить участников')}
            </div>
        `;
    }
    
    // Инициализируем иконки
    lucide.createIcons();
}

// Закрыть модальное окно
function closeMembersModal() {
    const modal = document.getElementById('membersModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Отображение списка участников
function renderMembers(members) {
    const membersList = document.getElementById('membersList');
    if (!membersList) return;
    
    if (!members || members.length === 0) {
        membersList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">—</div>
                <p>Участники не найдены</p>
            </div>
        `;
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
    
    membersList.innerHTML = sortedMembers.map(member => {
        const name = member.first_name + (member.last_name ? ' ' + member.last_name : '');
        const displayName = name || member.username || `User ${member.id}`;
        const initials = (member.first_name?.[0] || member.username?.[0] || 'U').toUpperCase();
        
        let statusBadge = '';
        if (member.status === 'creator') {
            statusBadge = '<span class="member-badge creator">Создатель</span>';
        } else if (member.status === 'administrator') {
            statusBadge = '<span class="member-badge admin">Админ</span>';
        }
        
        if (member.is_bot) {
            statusBadge = '<span class="member-badge bot">Бот</span>';
        }
        
        return `
            <div class="member-item">
                <div class="member-avatar">${initials}</div>
                <div class="member-info">
                    <div class="member-name">${escapeHtml(displayName)}</div>
                    <div class="member-details">
                        ${statusBadge}
                        ${member.username ? `<span>@${escapeHtml(member.username)}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Инициализируем иконки
    lucide.createIcons();
}

// Поиск чатов
function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput?.value.toLowerCase().trim();
    
    if (!searchTerm) {
        loadChats();
        return;
    }
    
    // Фильтруем уже загруженные чаты
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        const chatName = item.querySelector('.chat-name')?.textContent.toLowerCase() || '';
        if (chatName.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Показать ошибку
function showError(message) {
    if (chatsContainer) {
        chatsContainer.innerHTML = `
            <div class="error">
                <strong>Ошибка:</strong> ${escapeHtml(message)}
            </div>
            <button class="refresh-btn" onclick="location.reload()">Обновить</button>
        `;
    }
}

// Показать загрузку
function showLoading() {
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
    if (chatsContainer) {
        chatsContainer.innerHTML = '';
    }
}

// Скрыть загрузку
function hideLoading() {
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

