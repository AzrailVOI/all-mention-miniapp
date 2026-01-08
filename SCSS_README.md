# SCSS структура проекта

Проект использует SCSS для стилей с модульной архитектурой.

## Структура файлов

```
webapp/static/scss/
├── _variables.scss    # Переменные (цвета, шрифты, размеры)
├── _mixins.scss      # Миксины (переиспользуемые стили)
├── _base.scss        # Базовые стили (reset, body, container)
├── _layout.scss      # Layout компоненты (header, sections)
├── _components.scss  # UI компоненты (кнопки, карточки, формы)
├── _responsive.scss  # Адаптивные стили (медиа-запросы)
└── style.scss        # Главный файл (импортирует все модули)
```

## Компиляция SCSS

### Автоматическая компиляция

SCSS автоматически компилируется при запуске Flask приложения (если `COMPILE_SCSS=true` или `FLASK_ENV=development`).

### Ручная компиляция

```bash
# Компиляция один раз
python compile_scss.py

# Компиляция в сжатом виде (для продакшена)
python compile_scss.py compressed

# Отслеживание изменений (автоматическая компиляция при изменении файлов)
python compile_scss.py watch
```

### Использование в коде

```python
from webapp.utils.scss_compiler import compile_scss

# Компиляция с настройками по умолчанию
compile_scss()

# Компиляция в сжатом виде
compile_scss(output_style='compressed')

# Компиляция с source map
compile_scss(source_map=True)
```

## Переменные

Все переменные определены в `_variables.scss`:

- **Цвета**: `$color-primary`, `$color-background`, `$color-white`, и т.д.
- **Шрифты**: `$font-family-base`, `$font-size-*`, `$font-weight-*`
- **Размеры**: `$spacing-*`, `$border-radius-*`
- **Переходы**: `$transition-*`
- **Breakpoints**: `$breakpoint-mobile`

## Миксины

Полезные миксины в `_mixins.scss`:

- `@mixin button-base` - базовые стили кнопки
- `@mixin button-icon($size)` - кнопка-иконка
- `@mixin flex-center` - flex-центрирование
- `@mixin avatar($size)` - стили аватара
- `@mixin mobile` - медиа-запрос для мобильных устройств

## Добавление новых стилей

1. Определите переменные в `_variables.scss` (если нужны)
2. Создайте миксины в `_mixins.scss` (если нужны)
3. Добавьте стили в соответствующий модуль:
   - Layout → `_layout.scss`
   - Компоненты → `_components.scss`
   - Адаптивные → `_responsive.scss`
4. Скомпилируйте SCSS

## Пример использования

```scss
// В _components.scss
.my-component {
    background: $color-white;
    padding: $spacing-lg;
    border: 1px solid $color-primary;
    
    @include transition-all();
    
    &:hover {
        background: $color-gray-light;
    }
    
    @include mobile {
        padding: $spacing-md;
    }
}
```

## Зависимости

- `libsass` - компилятор SCSS
- `watchdog` - для режима отслеживания изменений (опционально)

Установка:
```bash
pip install -r requirements.txt
```
