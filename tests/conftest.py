"""
Конфигурация pytest для всех тестов.
Содержит общие фикстуры и настройки.
"""
import pytest
import tempfile
import os
import hmac
import hashlib
import urllib.parse
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from telegram import Bot, User, Chat, ChatMember, ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember, Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType, ChatMemberStatus as TelegramChatMemberStatus
try:
    from flask import Flask
except ImportError:
    Flask = None

from bot.services.chat_storage_service import ChatStorageService
from bot.services.chat_service import ChatService
from bot.services.mention_service import MentionService
from bot.constants import ChatType as BotChatType
from bot.config import Config



@pytest.fixture
def temp_storage_file():
    """Создает временный файл для хранения чатов."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    yield temp_file
    # Удаляем временный файл после теста
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def chat_storage_service(temp_storage_file):
    """Создает экземпляр ChatStorageService с временным файлом."""
    return ChatStorageService(storage_file=temp_storage_file)


@pytest.fixture
def mock_bot():
    """Создает мок-объект Bot."""
    bot = Mock(spec=Bot)
    bot.id = 123456789
    bot.username = "test_bot"
    bot.get_me = AsyncMock(return_value=Mock(id=bot.id, username=bot.username))
    bot.initialize = AsyncMock()
    return bot


@pytest.fixture
def chat_service(mock_bot):
    """Создает экземпляр ChatService с мок-ботом."""
    return ChatService(bot=mock_bot)


@pytest.fixture
def mention_service(mock_bot):
    """Создает экземпляр MentionService с мок-ботом."""
    return MentionService(bot=mock_bot)


@pytest.fixture
def sample_chat():
    """Создает тестовый объект Chat."""
    chat = Mock(spec=Chat)
    chat.id = -1001234567890
    chat.title = "Test Group"
    chat.type = ChatType.SUPERGROUP
    chat.username = None
    chat.members_count = 10
    return chat


@pytest.fixture
def sample_user():
    """Создает тестовый объект User."""
    user = Mock(spec=User)
    user.id = 987654321
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.is_bot = False
    return user


@pytest.fixture
def sample_bot_user():
    """Создает тестовый объект User для бота."""
    user = Mock(spec=User)
    user.id = 123456789
    user.first_name = "Test Bot"
    user.username = "test_bot"
    user.is_bot = True
    return user


@pytest.fixture
def sample_chat_member_owner(sample_user):
    """Создает тестовый ChatMemberOwner (создатель чата)."""
    member = Mock(spec=ChatMemberOwner)
    member.user = sample_user
    member.status = TelegramChatMemberStatus.OWNER
    return member


@pytest.fixture
def sample_chat_member_admin(sample_user):
    """Создает тестовый ChatMemberAdministrator (администратор)."""
    member = Mock(spec=ChatMemberAdministrator)
    member.user = sample_user
    member.status = TelegramChatMemberStatus.ADMINISTRATOR
    member.can_delete_messages = True
    member.can_manage_chat = True
    member.can_restrict_members = True
    member.can_promote_members = False
    member.can_change_info = True
    member.can_invite_users = True
    return member


@pytest.fixture
def sample_chat_member_member(sample_user):
    """Создает тестовый ChatMemberMember (обычный участник)."""
    member = Mock(spec=ChatMemberMember)
    member.user = sample_user
    member.status = TelegramChatMemberStatus.MEMBER
    return member


@pytest.fixture
def mock_update(sample_chat, sample_user):
    """Создает мок-объект Update."""
    update = Mock(spec=Update)
    update.effective_chat = sample_chat
    update.effective_user = sample_user
    update.message = None
    update.chat_member = None
    update.my_chat_member = None
    return update


@pytest.fixture
def mock_context(mock_bot):
    """Создает мок-объект ContextTypes.DEFAULT_TYPE."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = mock_bot
    context.bot.send_message = AsyncMock(return_value=Mock(message_id=123))
    return context


@pytest.fixture
def private_chat():
    """Создает приватный чат."""
    chat = Mock(spec=Chat)
    chat.id = 123456
    chat.type = BotChatType.PRIVATE
    chat.title = None
    chat.username = "test_user"
    chat.first_name = "Test"
    return chat


@pytest.fixture
def group_chat():
    """Создает групповой чат."""
    chat = Mock(spec=Chat)
    chat.id = -123456789
    chat.type = BotChatType.GROUP
    chat.title = "Test Group"
    chat.username = None
    chat.members_count = 10
    return chat


@pytest.fixture
def supergroup_chat():
    """Создает супергруппу."""
    chat = Mock(spec=Chat)
    chat.id = -1001234567890
    chat.type = BotChatType.SUPERGROUP
    chat.title = "Test Supergroup"
    chat.username = None
    chat.members_count = 100
    return chat


# Фикстуры для integration тестов API
@pytest.fixture
def client(monkeypatch):
    """Создает Flask test client."""
    try:
        # Устанавливаем переменные окружения для тестов перед импортом
        import os
        monkeypatch.setenv('BOT_TOKEN', os.environ.get('BOT_TOKEN', 'test_token_123456789'))
        monkeypatch.setenv('WEBAPP_SECRET_KEY', os.environ.get('WEBAPP_SECRET_KEY', 'test_secret_key_for_webapp'))
        monkeypatch.setenv('COMPILE_SCSS', 'false')  # Отключаем компиляцию SCSS в тестах
        monkeypatch.setenv('FLASK_ENV', 'testing')  # Устанавливаем режим тестирования
        
        # Импортируем приложение после установки переменных окружения
        from webapp.app import app
        
        # Настраиваем приложение для тестов
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Отключаем CSRF для тестов
        app.config['SECRET_KEY'] = 'test_secret_key'  # Устанавливаем секретный ключ для тестов
        
        # Отключаем rate limiting в тестах
        try:
            if hasattr(app, 'config'):
                app.config['RATELIMIT_ENABLED'] = False
        except (KeyError, AttributeError):
            pass
        
        # Патчим limiter для тестов, чтобы он не блокировал запросы
        try:
            from webapp.app import limiter
            limiter.enabled = False
        except (ImportError, AttributeError):
            pass
        
        with app.test_client() as test_client:
            yield test_client
    except Exception as e:
        # Если webapp не импортируется, пропускаем тест
        pytest.skip(f"webapp не доступен для тестирования: {type(e).__name__}: {str(e)}")


@pytest.fixture
def valid_init_data():
    """Создает валидные init_data для Telegram WebApp."""
    try:
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
    except (ImportError, AttributeError):
        # Если Config не доступен, возвращаем простую строку
        return "test_data=test&hash=test_hash"


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
    try:
        with patch('webapp.app.get_bot') as mock_get_bot:
            bot = MagicMock()
            bot.id = 123456789
            bot.username = "test_bot"
            bot.initialize = AsyncMock()
            bot.get_me = AsyncMock(return_value=MagicMock(id=bot.id, username=bot.username))
            mock_get_bot.return_value = bot
            yield bot
    except ImportError:
        # Если webapp не импортируется, создаем простой мок
        bot = MagicMock()
        bot.id = 123456789
        bot.username = "test_bot"
        bot.initialize = AsyncMock()
        bot.get_me = AsyncMock(return_value=MagicMock(id=bot.id, username=bot.username))
        yield bot
