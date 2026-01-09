"""
Конфигурация pytest для integration-тестов API.
Содержит фикстуры для Flask test client.
"""
import pytest
import hmac
import hashlib
import urllib.parse
from unittest.mock import patch, MagicMock, AsyncMock
from flask import Flask

from webapp.app import app, get_bot
from bot.config import Config


@pytest.fixture
def client():
    """Создает Flask test client."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Отключаем CSRF для тестов
    
    # Отключаем rate limiting в тестах (если возможно)
    app.config['RATELIMIT_ENABLED'] = False
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_init_data():
    """Создает валидные init_data для Telegram WebApp."""
    # Генерируем валидные init_data с правильной подписью
    test_data = {
        'query_id': 'test_query_id',
        'user': '{"id":123456789,"first_name":"Test","last_name":"User","username":"testuser"}',
        'auth_date': str(int(__import__('time').time())),
        'hash': ''  # Будет вычислен ниже
    }
    
    # Создаем строку для проверки
    data_check_string_parts = []
    for key in sorted(test_data.keys()):
        if key == 'hash':
            continue
        data_check_string_parts.append(f"{key}={test_data[key]}")
    
    data_check_string = '\n'.join(data_check_string_parts)
    
    # Получаем секретный ключ
    secret_key = Config.get_webapp_secret_key()
    
    # Вычисляем HMAC-SHA256
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    test_data['hash'] = calculated_hash
    
    # Формируем query string
    return urllib.parse.urlencode(test_data)


@pytest.fixture
def invalid_init_data():
    """Создает невалидные init_data для Telegram WebApp."""
    return "invalid_data=test&hash=invalid_hash"


@pytest.fixture
def sample_user_id():
    """Возвращает тестовый user_id."""
    return 123456789


@pytest.fixture
def sample_chat_id():
    """Возвращает тестовый chat_id."""
    return -1001234567890


@pytest.fixture
def mock_bot_for_api():
    """Мокает Bot для API тестов."""
    with patch('webapp.app.get_bot') as mock_get_bot:
        bot = MagicMock()
        bot.id = 123456789
        bot.username = "test_bot"
        bot.initialize = AsyncMock()
        bot.get_me = AsyncMock(return_value=MagicMock(id=bot.id, username=bot.username))
        mock_get_bot.return_value = bot
        yield bot
