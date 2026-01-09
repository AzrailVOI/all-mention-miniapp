# Настройка CI/CD и запуск тестов

## Настройка GitHub Actions

### Предварительные требования

1. Убедитесь, что у вас есть репозиторий на GitHub
2. Убедитесь, что все файлы CI/CD находятся в репозитории:
   - `.github/workflows/tests.yml`
   - `pytest.ini`
   - `.flake8`
   - `pyproject.toml`

### Настройка переменных окружения (опционально)

Для загрузки покрытия в Codecov (опционально):

1. Зайдите в настройки репозитория на GitHub
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте секрет:
   - **Name**: `CODECOV_TOKEN`
   - **Value**: ваш токен Codecov (если используете)

### Как это работает

Workflow автоматически запускается при:
- Push в ветки `main`, `develop`, `master`
- Pull Request в ветки `main`, `develop`, `master`

### Jobs в workflow

1. **test** - Запускает все тесты с покрытием кода
   - Проверяет на Python 3.9, 3.10, 3.11, 3.12
   - Генерирует отчеты о покрытии (XML, HTML)
   - Загружает coverage в Codecov (для Python 3.11)
   - Выполняет проверку типов с mypy

2. **lint** - Проверяет качество кода
   - Форматирование кода (black)
   - Сортировка импортов (isort)
   - Линтинг (flake8)

3. **security** - Проверяет безопасность
   - Сканирование кода (Bandit)
   - Проверка уязвимостей (safety)

## Локальный запуск тестов

### Установка зависимостей для тестирования

```bash
pip install -r requirements.txt
```

Зависимости для тестирования уже включены в `requirements.txt`:
- `pytest>=7.4.0`
- `pytest-asyncio>=0.21.0`
- `pytest-mock>=3.11.0`
- `pytest-cov>=4.1.0`

### Запуск всех тестов

```bash
# Все тесты
pytest tests/

# С покрытием кода
pytest tests/ --cov=bot --cov=webapp --cov-report=term-missing --cov-report=html

# Только unit-тесты
pytest tests/test_chat_storage_service.py tests/test_chat_service.py tests/test_mention_service.py

# Только тесты обработчиков
pytest tests/test_commands.py tests/test_messages.py tests/test_chat_events.py

# Только integration-тесты
pytest tests/test_api_integration.py
```

### Запуск с маркерами

```bash
# Только unit-тесты (если добавлены маркеры)
pytest -m unit

# Только integration-тесты
pytest -m integration

# Исключить медленные тесты
pytest -m "not slow"
```

### Просмотр покрытия кода

```bash
# Генерировать HTML отчет
pytest tests/ --cov=bot --cov=webapp --cov-report=html

# Открыть отчет в браузере
# Windows
start htmlcov/index.html
# Linux/Mac
open htmlcov/index.html
```

## Проверка качества кода локально

### Установка инструментов

```bash
pip install black isort flake8 mypy bandit safety
```

### Форматирование кода

```bash
# Проверка форматирования
black --check bot webapp tests

# Автоматическое форматирование
black bot webapp tests
```

### Сортировка импортов

```bash
# Проверка сортировки
isort --check-only bot webapp tests

# Автоматическая сортировка
isort bot webapp tests
```

### Линтинг

```bash
# Запуск flake8
flake8 bot webapp tests

# С подробным выводом
flake8 bot webapp tests --statistics
```

### Проверка типов

```bash
# Запуск mypy
mypy bot webapp --config-file mypy.ini
```

### Проверка безопасности

```bash
# Запуск Bandit
bandit -r bot webapp

# С JSON отчетом
bandit -r bot webapp -f json -o bandit-report.json

# Проверка уязвимостей в зависимостях
safety check
```

## Настройка переменных окружения для тестов

Для локального запуска тестов создайте файл `.env` (или используйте переменные окружения):

```env
BOT_TOKEN=test_token_123456789
WEBAPP_URL=http://localhost:5000
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=5000
LOG_LEVEL=INFO
USE_JSON_LOGGING=false
COMPILE_SCSS=false
```

**Примечание**: В CI/CD переменные окружения настраиваются автоматически в workflow файле.

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Общие фикстуры для всех тестов
├── conftest_api.py          # Фикстуры для integration-тестов
├── test_chat_storage_service.py   # Unit-тесты для ChatStorageService
├── test_chat_service.py            # Unit-тесты для ChatService
├── test_mention_service.py         # Unit-тесты для MentionService
├── test_commands.py                # Unit-тесты для команд бота
├── test_messages.py                # Unit-тесты для обработки сообщений
├── test_chat_events.py             # Unit-тесты для событий чата
└── test_api_integration.py         # Integration-тесты для API endpoints
```

## Устранение проблем

### Тесты не запускаются

1. Убедитесь, что установлены все зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Проверьте, что pytest установлен:
   ```bash
   pytest --version
   ```

### Ошибки импорта в тестах

1. Убедитесь, что вы запускаете тесты из корневой директории проекта:
   ```bash
   cd /path/to/all-mention-miniapp
   pytest tests/
   ```

2. Проверьте, что `PYTHONPATH` настроен правильно (обычно не требуется)

### Ошибки с async тестами

1. Убедитесь, что установлен `pytest-asyncio`:
   ```bash
   pip install pytest-asyncio
   ```

2. Проверьте, что в `pytest.ini` указан `asyncio_mode = auto`

### Ошибки в GitHub Actions

1. Проверьте логи в разделе **Actions** на GitHub
2. Убедитесь, что все файлы в репозитории:
   - `.github/workflows/tests.yml`
   - `requirements.txt`
   - `pytest.ini`
3. Проверьте, что переменные окружения настроены правильно (если используются)

## Дополнительные возможности

### Pre-commit hooks (опционально)

Для автоматической проверки кода перед коммитом:

1. Установите pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Создайте файл `.pre-commit-config.yaml`:
   ```yaml
   repos:
     - repo: https://github.com/psf/black
       rev: 23.7.0
       hooks:
         - id: black
     - repo: https://github.com/pycqa/isort
       rev: 5.12.0
       hooks:
         - id: isort
     - repo: https://github.com/pycqa/flake8
       rev: 6.1.0
       hooks:
         - id: flake8
   ```

3. Установите hooks:
   ```bash
   pre-commit install
   ```

### Непрерывная интеграция с другими платформами

Если вы хотите использовать другие CI/CD платформы:

- **GitLab CI**: создайте `.gitlab-ci.yml`
- **Jenkins**: создайте `Jenkinsfile`
- **CircleCI**: создайте `.circleci/config.yml`
- **Travis CI**: создайте `.travis.yml`

## Полезные команды

```bash
# Запуск тестов с подробным выводом
pytest tests/ -v

# Запуск тестов с остановкой на первой ошибке
pytest tests/ -x

# Запуск только упавших тестов
pytest tests/ --lf

# Запуск тестов в параллель (требует pytest-xdist)
pytest tests/ -n auto

# Показать самую медленную N тестов
pytest tests/ --durations=10

# Запуск тестов с покрытием только для измененных файлов
pytest tests/ --cov=bot --cov=webapp --cov-report=term-missing --cov-branch
```
