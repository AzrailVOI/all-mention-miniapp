// Telegram WebApp API
const tg = window.Telegram.WebApp;

// Инициализация WebApp
tg.ready();
tg.expand();

// На главной странице скрываем кнопку закрыть (она не нужна)
if (tg.close) {
    // На главной странице можно закрыть миниапп
    // Но кнопка закрыть управляется автоматически Telegram
}

// Элементы DOM
const statsContainer = document.querySelector('.stats');
const chatsContainer = document.querySelector('.chat-list');
const loadingElement = document.querySelector('.loading');

// Состояние отображения статистики
let statsVisible = false;

// API endpoint
const API_URL = '/api/chats';

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем иконки Lucide
    lucide.createIcons();
    
    // На главной странице скрываем кнопку назад (если она есть)
    if (tg.BackButton) {
        tg.BackButton.hide();
    }
    
    // Обработка нативной кнопки "назад" на главной странице
    // Если пользователь нажал назад на главной странице, закрываем миниапп
    window.addEventListener('popstate', (event) => {
        // На главной странице при нажатии назад закрываем миниапп
        if (window.location.pathname === '/' || window.location.pathname === '') {
            tg.close();
        }
    });
    
    // Изначально статистика скрыта
    if (statsContainer) {
        statsContainer.style.display = 'none';
    }

    // Тоггл статистики
    const statsToggle = document.querySelector('.stats-toggle');
    if (statsToggle && statsContainer) {
        statsToggle.addEventListener('click', () => {
            statsVisible = !statsVisible;
            statsContainer.style.display = statsVisible ? '' : 'none';
            statsToggle.textContent = statsVisible ? 'Скрыть статистику' : 'Статистика';
        });
        // Начальный текст
        statsToggle.textContent = 'Статистика';
    }

    await loadChats();
    
    // Обработчик кнопки обновления в шапке
    const refreshBtnHeader = document.querySelector('.refresh-btn-header');
    if (refreshBtnHeader) {
        refreshBtnHeader.addEventListener('click', async () => {
            const icon = refreshBtnHeader.querySelector('i');
            if (icon) {
                icon.style.animation = 'spin 1s linear infinite';
            }
            await loadChats();
            if (icon) {
                icon.style.animation = '';
            }
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
        
        if (!data.success) {
            showError(data.error || 'Не удалось загрузить список чатов');
            return;
        }
        
        // Показываем предупреждение, если данные из кэша
        if (data.cached && data.warning) {
            showToast(data.warning, 'warning');
        }
        
        // Сохраняем данные для фильтрации
        currentChats = data.chats || [];
        currentStats = data.stats;
        
        renderStats(currentStats);
        applyFilters(); // Применяем фильтры и сортировку
        
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
                <button class="refresh-btn" onclick="loadChats()" style="margin: 0 auto;">
                    <i data-lucide="refresh-cw" style="width: 16px; height: 16px; margin-right: 8px;"></i>
                    Обновить список
                </button>
            </div>
        </div>`;
        chatsContainer.innerHTML = emptyContent;
        lucide.createIcons();
        return;
    }
    
    chatsContainer.innerHTML = chats.map(chat => {
        const chatTitle = escapeHtml(chat.title || 'Без названия');
        const chatInitials = chatTitle.substring(0, 2).toUpperCase();
        const chatId = chat.id;
        
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
                avatarHtml = `<video class="chat-avatar-img" autoplay loop muted playsinline><source src="${escapeHtml(photoUrl)}" type="video/mp4"></video>`;
            } else {
                // Обычное фото или GIF
                console.log(`[Frontend] Чат ${chat.id}: определяем как фото/GIF`);
                avatarHtml = `<img class="chat-avatar-img" src="${escapeHtml(photoUrl)}" alt="${chatTitle}" onerror="console.error('[Frontend] Ошибка загрузки фото чата ${chat.id}'); this.parentElement.innerHTML='<div class=\\'chat-avatar-text\\'>${chatInitials}</div>'" />`;
            }
        } else {
            // Если нет фото, показываем иконку
            console.log(`[Frontend] Чат ${chat.id}: нет photo_url, показываем иконку`);
            avatarHtml = `<div class="chat-avatar-icon">${getChatIcon(chat.type)}</div>`;
        }
        
        return `
        <div class="chat-item" onclick="openChat(${chat.id}, '${escapeHtml(chatTitle)}')">
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
                <button class="chat-delete-btn" onclick="event.stopPropagation(); deleteChat(${chat.id}, '${escapeHtml(chatTitle)}')" title="Удалить чат из списка">
                    <i data-lucide="trash-2"></i>
                </button>
                <i data-lucide="chevron-right" class="chat-arrow"></i>
            </div>
        </div>
    `;
    }).join('');
    
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

// Открыть страницу участников чата
function openChat(chatId, chatTitle) {
    // Переходим на отдельную страницу участников
    const encodedTitle = encodeURIComponent(chatTitle || 'Участники чата');
    // Используем pushState для правильной работы кнопки назад
    window.history.pushState({ page: 'members', chatId, chatTitle }, '', `/members?chat_id=${chatId}&title=${encodedTitle}`);
    window.location.href = `/members?chat_id=${chatId}&title=${encodedTitle}`;
}

// Применение фильтров и сортировки
function applyFilters() {
    if (!currentChats || currentChats.length === 0) {
        renderChats([], null);
        return;
    }
    
    let filtered = [...currentChats];
    
    // Фильтр по типу
    const filterType = document.getElementById('filterType')?.value || 'all';
    if (filterType !== 'all') {
        filtered = filtered.filter(chat => chat.type === filterType);
    }
    
    // Поиск по названию
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput?.value.toLowerCase().trim();
    if (searchTerm) {
        filtered = filtered.filter(chat => 
            (chat.title || '').toLowerCase().includes(searchTerm)
        );
    }
    
    // Сортировка
    const sortBy = document.getElementById('sortBy')?.value || 'title';
    const sortOrder = document.getElementById('sortOrder')?.value || 'asc';
    
    if (sortBy === 'title') {
        filtered.sort((a, b) => {
            const cmp = (a.title || '').toLowerCase().localeCompare((b.title || '').toLowerCase());
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    } else if (sortBy === 'members_count') {
        filtered.sort((a, b) => {
            const aCount = a.members_count || 0;
            const bCount = b.members_count || 0;
            const cmp = aCount - bCount;
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    } else if (sortBy === 'type') {
        filtered.sort((a, b) => {
            const cmp = a.type.localeCompare(b.type);
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    }
    
    // Отображаем отфильтрованные чаты
    renderChats(filtered, null);
    
    // Обновляем статистику для отфильтрованных чатов
    if (currentStats) {
        const filteredStats = {
            total: filtered.length,
            groups: filtered.filter(c => c.type === 'group').length,
            supergroups: filtered.filter(c => c.type === 'supergroup').length,
            private: 0,
            channels: 0
        };
        renderStats(filteredStats);
    }
}

// Поиск чатов
function performSearch() {
    applyFilters();
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

// Генерация skeleton screens для чатов
function generateSkeletonChats() {
    const skeletonCount = 5;
    let html = '';
    for (let i = 0; i < skeletonCount; i++) {
        html += `
            <div class="skeleton-chat-item">
                <div class="skeleton skeleton-avatar"></div>
                <div style="flex: 1;">
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text skeleton-text-short"></div>
                </div>
            </div>
        `;
    }
    return html;
}

// Показать загрузку
function showLoading() {
    if (loadingElement) {
        loadingElement.style.display = 'flex';
    }
    if (chatsContainer) {
        // Показываем skeleton screens вместо пустого контейнера
        chatsContainer.innerHTML = generateSkeletonChats();
    }
}

// Скрыть загрузку
function hideLoading() {
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Показать toast уведомление
function showToast(message, type = 'info') {
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

// Удаление чата из списка
async function deleteChat(chatId, chatTitle) {
    if (!confirm(`Вы уверены, что хотите удалить чат "${chatTitle}" из списка?`)) {
        return;
    }
    
    try {
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

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Управление темой
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.className = savedTheme === 'light' ? 'theme-light' : '';
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const isLight = document.body.classList.contains('theme-light');
    const newTheme = isLight ? 'dark' : 'light';
    document.body.className = newTheme === 'light' ? 'theme-light' : '';
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.setAttribute('data-lucide', theme === 'light' ? 'moon' : 'sun');
        lucide.createIcons();
    }
}

// Инициализация темы при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
});

