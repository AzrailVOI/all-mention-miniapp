# Структура JavaScript модулей

Проект использует модульную архитектуру для удобства поддержки и масштабирования.

## Структура директорий

```
js/
├── api/                    # API модули для работы с сервером
│   ├── chats-api.js       # API для загрузки списка чатов
│   └── members-api.js     # API для загрузки участников чата
│
├── render/                 # Модули рендеринга UI
│   ├── stats-render.js    # Рендеринг статистики
│   ├── chats-render.js    # Рендеринг списка чатов
│   └── members-render.js # Рендеринг списка участников
│
├── ui/                     # UI модули (взаимодействие, состояние)
│   ├── loading.js         # Управление состоянием загрузки
│   ├── search.js          # Логика поиска
│   ├── navigation.js      # Навигация между страницами
│   └── errors.js          # Обработка и отображение ошибок
│
├── utils.js               # Общие утилиты
├── app.js                 # Главный файл для страницы списка чатов
└── members.js             # Главный файл для страницы участников
```

## Порядок загрузки модулей

Модули должны загружаться в следующем порядке:

1. **Базовые утилиты** (`utils.js`) - функции общего назначения
2. **API модули** - работа с сервером
3. **Render модули** - рендеринг UI компонентов
4. **UI модули** - управление состоянием и взаимодействием
5. **Основные файлы** (`app.js` или `members.js`) - инициализация приложения

## API модули

### `api/chats-api.js`
- `ChatsAPI.loadChats()` - загружает список чатов с сервера

### `api/members-api.js`
- `MembersAPI.loadMembers(chatId)` - загружает список участников чата

## Render модули

### `render/stats-render.js`
- `StatsRender.renderStats(stats, container)` - отображает статистику чатов

### `render/chats-render.js`
- `ChatsRender.renderChats(chats, infoMessage, container)` - отображает список чатов

### `render/members-render.js`
- `MembersRender.renderMembers(members, container)` - отображает список участников

## UI модули

### `ui/loading.js`
- `Loading.show(loadingElement, contentContainer)` - показывает индикатор загрузки
- `Loading.hide(loadingElement)` - скрывает индикатор загрузки

### `ui/search.js`
- `Search.performSearch(searchTerm, onEmptySearch)` - выполняет поиск чатов

### `ui/navigation.js`
- `Navigation.openChat(chatId, chatTitle)` - открывает страницу участников чата
- `Navigation.goBack()` - возвращается на главную страницу
- `Navigation.openProfile(profileLink)` - открывает профиль пользователя

Также экспортирует функции в `window` для использования в HTML:
- `window.openChat`
- `window.goBack`
- `window.openProfile`

### `ui/errors.js`
- `Errors.show(message, container)` - показывает сообщение об ошибке

## Утилиты

### `utils.js`
- `escapeHtml(text)` - экранирование HTML для предотвращения XSS
- `getChatIcon(type)` - получение иконки для типа чата
- `getChatTypeLabel(type)` - получение метки для типа чата
- `showToast(message, type)` - показ toast уведомления
- `showError(message)` - показ ошибки (legacy, используйте `Errors.show`)

Все функции экспортируются в `window` для глобального доступа.

## Основные файлы

### `app.js`
Главный файл для страницы списка чатов (`index.html`).

Инициализирует:
- Telegram WebApp API
- Обработчики событий
- Загрузку и отображение данных

### `members.js`
Главный файл для страницы участников (`members.html`).

Инициализирует:
- Telegram WebApp API
- Кнопку "Назад"
- Загрузку и отображение участников

## Использование модулей

Все модули экспортируют свои функции через объекты в `window`:

```javascript
// Использование API
const data = await window.ChatsAPI.loadChats();

// Использование Render
window.ChatsRender.renderChats(data.chats, data.info, container);

// Использование UI
window.Loading.show(loadingElement, contentContainer);
```

## Добавление новых модулей

1. Создайте файл в соответствующей директории (`api/`, `render/`, `ui/`)
2. Экспортируйте функции через объект в `window`:
   ```javascript
   window.MyModule = {
       myFunction: myFunction
   };
   ```
3. Добавьте скрипт в HTML файл в правильном порядке загрузки
4. Используйте модуль в основном файле приложения
