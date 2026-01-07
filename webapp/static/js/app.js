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
    await loadChats();
    
    // Обработчик кнопки обновления
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            await loadChats();
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
        renderChats(data.chats);
        
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
            <div class="stat-value">${stats.total || 0}</div>
            <div class="stat-label">Всего чатов</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.groups || 0}</div>
            <div class="stat-label">Группы</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.supergroups || 0}</div>
            <div class="stat-label">Супергруппы</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.private || 0}</div>
            <div class="stat-label">Приватные</div>
        </div>
    `;
}

// Отображение списка чатов
function renderChats(chats) {
    if (!chatsContainer) return;
    
    if (!chats || chats.length === 0) {
        chatsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <p>Бот еще не добавлен ни в один чат</p>
            </div>
        `;
        return;
    }
    
    chatsContainer.innerHTML = chats.map(chat => `
        <div class="chat-item" onclick="openChat(${chat.id})">
            <div class="chat-icon">
                ${getChatIcon(chat.type)}
            </div>
            <div class="chat-info">
                <div class="chat-name">${escapeHtml(chat.title || 'Без названия')}</div>
                <div class="chat-details">
                    <span class="chat-type ${chat.type}">${getChatTypeLabel(chat.type)}</span>
                    <span>ID: ${chat.id}</span>
                    ${chat.members_count ? `<span>Участников: ${chat.members_count}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// Получить иконку для типа чата
function getChatIcon(type) {
    const icons = {
        'group': '👥',
        'supergroup': '👥',
        'private': '👤',
        'channel': '📢'
    };
    return icons[type] || '💬';
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

// Открыть чат (можно расширить функционал)
function openChat(chatId) {
    tg.showAlert(`Чат ID: ${chatId}\n\nФункция открытия чата будет добавлена позже.`);
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

