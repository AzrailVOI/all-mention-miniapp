/**
 * Главный файл приложения для страницы участников чата
 * Использует модульную архитектуру
 */

// Telegram WebApp API
const tg = window.Telegram.WebApp;

// Инициализация WebApp
tg.ready();
tg.expand();

// Элементы DOM
const membersList = document.getElementById('membersList');
const loadingElement = document.getElementById('loading');
const chatTitleElement = document.getElementById('chatTitle');

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
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // Настраиваем кнопку "Назад" в Telegram WebApp
    if (tg.BackButton) {
        // Показываем кнопку назад
        tg.BackButton.show();
        
        // Обработчик нажатия на кнопку назад
        tg.BackButton.onClick(() => {
            if (window.Navigation) {
                window.Navigation.goBack();
            } else {
                window.location.href = '/';
            }
        });
    }
    
    if (chatId) {
        await loadMembersData(parseInt(chatId));
    } else {
        const errorMessage = 'ID чата не указан';
        if (window.Errors && membersList) {
            window.Errors.show(errorMessage, membersList);
        } else if (membersList) {
            membersList.innerHTML = `
                <div class="error">
                    <strong>Ошибка:</strong> ${window.escapeHtml ? window.escapeHtml(errorMessage) : errorMessage}
                </div>
            `;
        }
    }
});

/**
 * Загружает и отображает список участников чата
 * @param {number} chatId - ID чата
 */
async function loadMembersData(chatId) {
    try {
        console.log(`[Members] Загрузка участников для чата: ${chatId}`);
        
        // Показываем загрузку
        if (window.Loading) {
            window.Loading.show(loadingElement, membersList);
        } else {
            if (loadingElement) loadingElement.style.display = 'block';
            if (membersList) membersList.innerHTML = '';
        }
        
        // Загружаем данные через API
        const data = await window.MembersAPI.loadMembers(chatId);
        
        console.log(`[Members] Данные получены:`, data);
        
        // Отображаем участников
        if (window.MembersRender && membersList) {
            window.MembersRender.renderMembers(data.members, membersList);
        }
        
    } catch (error) {
        console.error('[Members] Error loading members:', error);
        
        // Показываем ошибку
        const errorMessage = error.message || 'Не удалось загрузить участников';
        if (window.Errors && membersList) {
            window.Errors.show(errorMessage, membersList);
        } else if (membersList) {
            membersList.innerHTML = `
                <div class="error">
                    <strong>Ошибка:</strong> ${window.escapeHtml ? window.escapeHtml(errorMessage) : errorMessage}
                </div>
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

// Обработка нативной кнопки "назад" на Android/iOS
// Это событие срабатывает при нажатии системной кнопки назад
window.addEventListener('popstate', (event) => {
    // При нажатии на системную кнопку назад возвращаемся на главную
    if (window.Navigation) {
        window.Navigation.goBack();
    } else {
        window.location.href = '/';
    }
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
