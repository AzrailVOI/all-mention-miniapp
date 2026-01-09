/**
 * Главный файл приложения для страницы списка чатов
 * Использует модульную архитектуру
 */

// Telegram WebApp API
const tg = window.Telegram.WebApp;

// Инициализация WebApp
tg.ready();
tg.expand();

// Элементы DOM (объявляем как let, чтобы избежать ошибок инициализации)
let statsContainer = null;
let chatsContainer = null;
let loadingElement = null;

// Состояние фильтрации и сортировки
let currentFilter = 'all';
let currentSort = 'title';
let allChats = []; // Сохраняем все чаты для фильтрации

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализируем элементы DOM после загрузки
    statsContainer = document.querySelector('.stats');
    chatsContainer = document.querySelector('.chat-list');
    loadingElement = document.querySelector('.loading');
    
    // Инициализируем обработчики offline режима
    if (window.Offline && window.Offline.initOfflineHandlers) {
        window.Offline.initOfflineHandlers();
    }
    
    // Инициализируем иконки Lucide
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // Инициализируем сворачивание блоков (по умолчанию все свернуты)
    if (window.Collapse) {
        window.Collapse.init();
    }
    
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
    
    await loadChatsData();
    
    // Обработчик поиска по Enter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearchHandler();
            }
        });
    }
});

/**
 * Загружает и отображает список чатов
 * @param {boolean} forceRefresh - Принудительное обновление (инвалидация кэша)
 */
async function loadChatsData(forceRefresh = false) {
    try {
        // Показываем skeleton screens вместо простого спиннера
        if (window.Skeleton) {
            if (statsContainer) {
                window.Skeleton.showStats(statsContainer, 3);
            }
            if (chatsContainer) {
                window.Skeleton.showChats(chatsContainer, 5);
            }
        } else if (window.Loading) {
            window.Loading.show(loadingElement, chatsContainer);
        } else {
            if (loadingElement) loadingElement.style.display = 'block';
            if (chatsContainer) chatsContainer.innerHTML = '';
        }
        
        // Загружаем данные через API
        const data = await window.ChatsAPI.loadChats(forceRefresh);
        
        // Показываем предупреждение, если данные из кэша
        if (data.cached && data.warning) {
            if (window.showToast) {
                window.showToast(data.warning, 'warning');
            }
        }
        
        // Отображаем статистику
        if (window.StatsRender && statsContainer) {
            window.StatsRender.renderStats(data.stats, statsContainer);
        }
        
        // Сохраняем все чаты для фильтрации
        allChats = data.chats || [];
        
        // Применяем фильтр и сортировку
        const filteredChats = applyFilter(allChats, currentFilter);
        const sortedChats = applySort(filteredChats, currentSort);
        
        // Отображаем список чатов
        if (window.ChatsRender && chatsContainer) {
            window.ChatsRender.renderChats(sortedChats, data.info, chatsContainer);
        }
        
    } catch (error) {
        console.error('Error loading chats:', error);
        
        // Показываем ошибку
        const errorMessage = error.message || 'Не удалось загрузить список чатов. Попробуйте обновить страницу.';
        if (window.Errors && chatsContainer) {
            window.Errors.show(errorMessage, chatsContainer);
        } else if (chatsContainer) {
            chatsContainer.innerHTML = `
                <div class="error">
                    <strong>Ошибка:</strong> ${window.escapeHtml ? window.escapeHtml(errorMessage) : errorMessage}
                </div>
                <button class="refresh-btn" onclick="location.reload()">Обновить</button>
            `;
        }
    } finally {
        // Скрываем загрузку
        if (window.Loading) {
            window.Loading.hide(loadingElement);
        } else {
            if (loadingElement) loadingElement.style.display = 'none';
        }
    }
}

/**
 * Обработчик поиска чатов
 */
function performSearchHandler() {
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput?.value;
    
    if (window.Search) {
        window.Search.performSearch(searchTerm, loadChatsData);
    } else {
        // Fallback
        if (!searchTerm || !searchTerm.trim()) {
            loadChatsData();
            return;
        }
        
        const term = searchTerm.toLowerCase().trim();
        const chatItems = document.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            const chatName = item.querySelector('.chat-name')?.textContent.toLowerCase() || '';
            if (chatName.includes(term)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
}

/**
 * Обновляет список чатов (с инвалидацией кэша)
 */
function refreshChats() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        const icon = refreshBtn.querySelector('i');
        if (icon) {
            icon.style.animation = 'spin 1s linear infinite';
        }
    }
    
    loadChatsData(true).then(() => {
        // Показываем Toast об успешном обновлении
        if (window.showToast) {
            window.showToast('Список чатов успешно обновлен', 'success');
        }
    }).catch((error) => {
        // Логируем ошибку для отладки
        console.error('[refreshChats] Ошибка при обновлении списка чатов:', error);
        
        // Показываем Toast об ошибке с деталями
        const errorMessage = error.message || 'Ошибка при обновлении списка чатов';
        if (window.showToast) {
            window.showToast(errorMessage, 'error');
        } else {
            // Fallback: показываем ошибку в консоли
            console.error('[refreshChats] Детали ошибки:', {
                message: error.message,
                stack: error.stack,
                error: error
            });
        }
    }).finally(() => {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            const icon = refreshBtn.querySelector('i');
            if (icon) {
                icon.style.animation = '';
            }
        }
    });
}

/**
 * Применяет фильтр к списку чатов
 * @param {Array} chats - Список чатов
 * @param {string} filterType - Тип фильтра ('all', 'group', 'supergroup')
 * @returns {Array} Отфильтрованный список чатов
 */
function applyFilter(chats, filterType) {
    if (filterType === 'all') {
        return chats;
    }
    return chats.filter(chat => chat.type === filterType);
}

/**
 * Фильтрует чаты по типу
 * @param {string} filterType - Тип фильтра ('all', 'group', 'supergroup')
 */
function filterChats(filterType) {
    currentFilter = filterType;
    
    // Обновляем активную кнопку
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.dataset.filter === filterType) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Применяем фильтр и сортировку
    const filteredChats = applyFilter(allChats, filterType);
    const sortedChats = applySort(filteredChats, currentSort);
    
    // Формируем сообщение для пустого состояния после фильтрации
    let emptyMessage = null;
    if (sortedChats.length === 0 && allChats.length > 0) {
        const filterLabels = {
            'all': 'всех',
            'group': 'групп',
            'supergroup': 'супергрупп'
        };
        emptyMessage = `Не найдено ${filterLabels[filterType] || 'чатов'} по выбранному фильтру.\n\nПопробуйте выбрать другой фильтр или обновить список чатов.`;
    }
    
    // Перерисовываем список чатов
    if (window.ChatsRender && chatsContainer) {
        window.ChatsRender.renderChats(sortedChats, emptyMessage, chatsContainer);
    }
}

/**
 * Сортирует чаты
 * @param {string} sortType - Тип сортировки ('title', 'members', 'type')
 */
function sortChats(sortType) {
    currentSort = sortType;
    
    // Применяем фильтр и сортировку
    const filteredChats = applyFilter(allChats, currentFilter);
    const sortedChats = applySort(filteredChats, currentSort);
    
    // Перерисовываем список чатов
    if (window.ChatsRender && chatsContainer) {
        window.ChatsRender.renderChats(sortedChats, null, chatsContainer);
    }
}

/**
 * Удаляет чат из списка с подтверждением
 * @param {number} chatId - ID чата
 * @param {string} chatTitle - Название чата
 */
async function deleteChat(chatId, chatTitle) {
    // Показываем подтверждение
    const confirmed = confirm(`Вы уверены, что хотите удалить чат "${chatTitle}" из списка?\n\nЭто действие нельзя отменить.`);
    
    if (!confirmed) {
        return;
    }
    
    try {
        const tg = window.Telegram.WebApp;
        const initData = tg.initData;
        const user = tg.initDataUnsafe?.user;
        
        const response = await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                init_data: initData,
                user_id: user?.id
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Не удалось удалить чат');
        }
        
        // Показываем уведомление об успехе
        if (window.showToast) {
            window.showToast(`Чат "${chatTitle}" успешно удален`, 'success');
        }
        
        // Удаляем чат из локального списка
        allChats = allChats.filter(chat => chat.id !== chatId);
        
        // Применяем фильтр и сортировку
        const filteredChats = applyFilter(allChats, currentFilter);
        const sortedChats = applySort(filteredChats, currentSort);
        
        // Перерисовываем список чатов
        if (window.ChatsRender && chatsContainer) {
            window.ChatsRender.renderChats(sortedChats, null, chatsContainer);
        }
        
        // Обновляем статистику
        if (window.StatsRender && statsContainer) {
            const stats = {
                total: allChats.length,
                groups: allChats.filter(c => c.type === 'group').length,
                supergroups: allChats.filter(c => c.type === 'supergroup').length,
                private: 0,
                channels: 0
            };
            window.StatsRender.renderStats(stats, statsContainer);
        }
        
    } catch (error) {
        console.error('[App] Ошибка при удалении чата:', error);
        
        // Показываем ошибку
        const errorMessage = error.message || 'Не удалось удалить чат';
        if (window.showToast) {
            window.showToast(errorMessage, 'error');
        }
    }
}

// Экспорт для использования в HTML (onclick)
window.performSearch = performSearchHandler;
window.refreshChats = refreshChats;
window.filterChats = filterChats;
window.sortChats = sortChats;
window.deleteChat = deleteChat;
