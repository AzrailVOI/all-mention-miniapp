
# Настройка TypeScript компиляции

## Установка TypeScript

Для компиляции TypeScript файлов необходимо установить TypeScript компилятор.

### Вариант 1: Глобальная установка (рекомендуется)

```bash
npm install -g typescript
```

### Вариант 2: Локальная установка в проект

```bash
npm install --save-dev typescript
```

После установки TypeScript будет автоматически компилироваться при запуске Flask приложения.

## Структура файлов

- `webapp/static/ts/` - исходные TypeScript файлы
- `webapp/static/js/` - скомпилированные JavaScript файлы
- `tsconfig.json` - конфигурация TypeScript

## Модули

Код разбит на следующие модули:

- `types.ts` - типы и интерфейсы
- `utils.ts` - утилиты (escapeHtml, showToast, и т.д.)
- `modal.ts` - управление модальным окном фильтров
- `filters.ts` - фильтры и сортировка
- `api.ts` - API запросы
- `render.ts` - рендеринг чатов
- `stats.ts` - статистика
- `loading.ts` - состояние загрузки
- `theme.ts` - управление темой
- `app.ts` - главный файл приложения

## Компиляция

Компиляция происходит автоматически при старте Flask приложения через `webapp/utils/ts_compiler.py`.

Для ручной компиляции:

```bash
tsc --project tsconfig.json
```

Или через Python:

```python
from webapp.utils.ts_compiler import compile_typescript
compile_typescript()
```
