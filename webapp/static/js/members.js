// Telegram WebApp API
const tg = window.Telegram.WebApp;

// Инициализация WebApp
tg.ready();
tg.expand();

// Элементы DOM
const membersList = document.getElementById('membersList');
const loadingElement = document.getElementById('loading');
const chatTitleElement = document.getElementById('chatTitle');
const paginationContainer = document.createElement('div');
paginationContainer.className = 'pagination';

// Состояние пагинации
let currentMembers = [];
let currentPage = 1;
const MEMBERS_PER_PAGE = 25;

// Получаем chat_id из URL параметров
const urlParams = new URLSearchParams(window.location.search);
const chatId = urlParams.get('chat_id');
const chatTitle = urlParams.get('title') || 'Участники чата';

// Устанавливаем заголовок
if (chatTitleElement) {
    chatTitleElement.textContent = chatTitle;
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем иконки Lucide
    lucide.createIcons();
    
    // Настраиваем кнопку "Назад" в Telegram WebApp
    if (tg.BackButton) {
        // Показываем кнопку назад
        tg.BackButton.show();
        
        // Обработчик нажатия на кнопку назад
        tg.BackButton.onClick(() => {
            goBack();
        });
    }
    
    // Вставляем контейнер пагинации после списка участников
    if (membersList && membersList.parentElement) {
        membersList.parentElement.appendChild(paginationContainer);
    }

    if (chatId) {
        await loadMembers(parseInt(chatId));
    } else {
        showError('ID чата не указан');
    }
});

// Загрузка участников
async function loadMembers(chatId) {
    try {
        showLoading();
        
        console.log(`[Members] Загрузка участников для чата: ${chatId}`);
        
        // Получаем данные пользователя из Telegram WebApp
        const user = tg.initDataUnsafe?.user;
        const userId = user?.id;
        
        console.log(`[Members] User ID: ${userId}`);
        
        if (!userId) {
            throw new Error('Не удалось получить ID пользователя из Telegram WebApp');
        }
        
        // Отправляем запрос на сервер
        const url = `/api/chats/${chatId}/members`;
        console.log(`[Members] Отправка запроса на: ${url}`);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        console.log(`[Members] Ответ получен: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            console.error(`[Members] Ошибка ответа:`, errorData);
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`[Members] Данные получены:`, data);
        
        if (!data.success) {
            throw new Error(data.error || 'Не удалось загрузить участников');
        }
        
        // Сохраняем всех участников для пагинации
        currentMembers = data.members || [];
        currentPage = 1;

        renderMembersPaginated();
        
    } catch (error) {
        console.error('[Members] Error loading members:', error);
        showError(error.message || 'Не удалось загрузить участников');
    } finally {
        hideLoading();
    }
}

// Отображение списка участников (одной страницы)
function renderMembers(members) {
    if (!membersList) return;
    
    if (!members || members.length === 0) {
        membersList.innerHTML = `
            <div class="empty-state">
                <i data-lucide="users" style="width: 64px; height: 64px; opacity: 0.3; margin-bottom: 20px;"></i>
                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 12px; color: #1a1a1a;">Участники не найдены</h3>
                <p style="color: #666; line-height: 1.6;">
                    Не удалось загрузить список участников. Возможно, у вас нет прав для просмотра участников этой группы.
                </p>
            </div>
        `;
        lucide.createIcons();
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
        
        console.log(`[Frontend] Обработка участника ${member.id} (${displayName}): profile_photo_url = ${member.profile_photo_url || 'отсутствует'}`);
        
        // Ленивая загрузка фото профиля - загружаем только при необходимости
        let avatarHtml = '';
        if (member.profile_photo_url) {
            // Проверяем тип файла по расширению
            const photoUrl = member.profile_photo_url;
            console.log(`[Frontend] Участник ${member.id}: есть profile_photo_url = ${photoUrl}`);
            
            const urlLower = photoUrl.toLowerCase();
            const isVideo = urlLower.includes('.mp4') || urlLower.includes('.mov') || urlLower.includes('video');
            const isGif = urlLower.includes('.gif');
            
            if (isVideo) {
                // Видео аватарка с автопроигрыванием
                console.log(`[Frontend] Участник ${member.id}: определяем как видео`);
                avatarHtml = `<video class="member-avatar-img" autoplay loop muted playsinline><source src="${escapeHtml(photoUrl)}" type="video/mp4"></video>`;
            } else {
                // Обычное фото или GIF (оба отображаются через img, GIF будет автопроигрываться)
                console.log(`[Frontend] Участник ${member.id}: определяем как фото/GIF`);
                // Используем loading="lazy" для ленивой загрузки
                avatarHtml = `<img class="member-avatar-img" src="${escapeHtml(photoUrl)}" alt="${escapeHtml(displayName)}" loading="lazy" onerror="console.error('[Frontend] Ошибка загрузки фото участника ${member.id}'); this.parentElement.innerHTML='<div class=\\'member-avatar-text\\'>${initials}</div>'" />`;
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
                    <div class="member-name">${escapeHtml(displayName)}</div>
                    <div class="member-details">
                        ${statusBadge}
                        ${member.username ? `<span>@${escapeHtml(member.username)}</span>` : ''}
                    </div>
                </div>
                <button class="member-profile-btn" onclick="openProfile('${escapeHtml(profileLink)}')" title="Открыть профиль">
                    <i data-lucide="external-link"></i>
                </button>
            </div>
        `;
    }).join('');
    
    // Инициализируем иконки
    lucide.createIcons();
}

// Отрисовка текущей страницы участников
function renderMembersPaginated() {
    if (!currentMembers || currentMembers.length === 0) {
        renderMembers([]);
        updatePaginationControls();
        return;
    }

    const totalPages = Math.max(1, Math.ceil(currentMembers.length / MEMBERS_PER_PAGE));
    if (currentPage > totalPages) {
        currentPage = totalPages;
    }

    const startIndex = (currentPage - 1) * MEMBERS_PER_PAGE;
    const endIndex = startIndex + MEMBERS_PER_PAGE;
    const pageMembers = currentMembers.slice(startIndex, endIndex);

    renderMembers(pageMembers);
    updatePaginationControls(totalPages);
}

// Обновление UI пагинации
function updatePaginationControls(totalPages = 1) {
    if (!paginationContainer) return;

    if (!currentMembers || currentMembers.length === 0) {
        paginationContainer.style.display = 'none';
        paginationContainer.innerHTML = '';
        return;
    }

    paginationContainer.style.display = 'flex';
    paginationContainer.innerHTML = `
        <button
            class="pagination-btn"
            onclick="changeMembersPage('prev')"
            ${currentPage <= 1 ? 'disabled' : ''}
        >
            <i data-lucide="chevron-left"></i>
            Предыдущая
        </button>
        <span class="pagination-info">
            Страница ${currentPage} из ${totalPages}
        </span>
        <button
            class="pagination-btn"
            onclick="changeMembersPage('next')"
            ${currentPage >= totalPages ? 'disabled' : ''}
        >
            Следующая
            <i data-lucide="chevron-right"></i>
        </button>
    `;

    lucide.createIcons();
}

// Смена страницы
function changeMembersPage(direction) {
    if (!currentMembers || currentMembers.length === 0) return;

    const totalPages = Math.max(1, Math.ceil(currentMembers.length / MEMBERS_PER_PAGE));

    if (direction === 'prev' && currentPage > 1) {
        currentPage -= 1;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage += 1;
    } else {
        return;
    }

    renderMembersPaginated();
}

// Показать ошибку
function showError(message) {
    if (membersList) {
        membersList.innerHTML = `
            <div class="error">
                <strong>Ошибка:</strong> ${escapeHtml(message)}
            </div>
        `;
    }
}

// Показать загрузку
function showLoading() {
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
    if (membersList) {
        // Показываем skeleton screens вместо пустого контейнера
        membersList.innerHTML = generateSkeletonMembers();
    }
}

// Генерация skeleton screens для участников
function generateSkeletonMembers() {
    const skeletonCount = 8;
    let html = '';
    for (let i = 0; i < skeletonCount; i++) {
        html += `
            <div class="skeleton-member-item">
                <div class="skeleton skeleton-member-avatar"></div>
                <div style="flex: 1;">
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text skeleton-text-short"></div>
                </div>
            </div>
        `;
    }
    return html;
}

// Скрыть загрузку
function hideLoading() {
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Назад
function goBack() {
    // Всегда возвращаемся на главную страницу
    window.location.href = '/';
}

// Обработка нативной кнопки "назад" на Android/iOS
// Это событие срабатывает при нажатии системной кнопки назад
window.addEventListener('popstate', (event) => {
    // При нажатии на системную кнопку назад возвращаемся на главную
    window.location.href = '/';
});

// При размонтировании страницы скрываем кнопку назад
window.addEventListener('beforeunload', () => {
    if (tg.BackButton) {
        tg.BackButton.hide();
    }
});

// Также скрываем кнопку назад при уходе со страницы через visibility API
document.addEventListener('visibilitychange', () => {
    if (document.hidden && tg.BackButton) {
        // Не скрываем, так как пользователь может вернуться
    }
});

// Открыть профиль пользователя
function openProfile(profileLink) {
    // Используем Telegram WebApp API для открытия профиля
    if (tg.openTelegramLink) {
        tg.openTelegramLink(profileLink);
    } else if (tg.openLink) {
        tg.openLink(profileLink);
    } else {
        // Fallback: открываем в новом окне
        window.open(profileLink, '_blank');
    }
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Управление темой (дублируем из app.js для members.js)
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

