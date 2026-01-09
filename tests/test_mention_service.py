"""
Unit-тесты для MentionService.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from telegram import User
from telegram.error import TelegramError

from bot.services.mention_service import MentionService
from bot.models.message import MentionMessage


class TestMentionService:
    """Тесты для MentionService."""
    
    def test_extract_cleaned_text(self, mention_service):
        """Тест удаления триггеров упоминания из текста."""
        text = "@all Привет всем!"
        cleaned = mention_service.extract_cleaned_text(text)
        assert "@all" not in cleaned
        assert "Привет всем!" in cleaned
    
    def test_extract_cleaned_text_multiple_triggers(self, mention_service):
        """Тест удаления нескольких триггеров."""
        text = "@all @everyone @everybody_mention_bot Сообщение"
        cleaned = mention_service.extract_cleaned_text(text)
        assert "@all" not in cleaned
        assert "@everyone" not in cleaned
        assert "@everybody_mention_bot" not in cleaned
        assert "Сообщение" in cleaned
    
    def test_has_mention_trigger_true(self, mention_service):
        """Тест проверки наличия триггера упоминания - True."""
        text = "Привет @all всем!"
        assert mention_service.has_mention_trigger(text) is True
    
    def test_has_mention_trigger_false(self, mention_service):
        """Тест проверки наличия триггера упоминания - False."""
        text = "Привет всем!"
        assert mention_service.has_mention_trigger(text) is False
    
    def test_has_mention_trigger_case_insensitive(self, mention_service):
        """Тест проверки триггера без учета регистра."""
        text = "Привет @ALL всем!"
        assert mention_service.has_mention_trigger(text) is True
    
    def test_format_user_tags_with_username(self, mention_service, sample_user):
        """Тест форматирования тегов пользователей с username."""
        users = [sample_user]
        tags = mention_service.format_user_tags(users)
        
        assert len(tags) == 1
        assert tags[0] == f"@{sample_user.username}"
    
    def test_format_user_tags_without_username(self, mention_service):
        """Тест форматирования тегов пользователей без username."""
        user = Mock(spec=User)
        user.id = 123
        user.username = None
        user.first_name = "John"
        user.last_name = None
        
        users = [user]
        tags = mention_service.format_user_tags(users)
        
        assert len(tags) == 1
        assert tags[0] == "John"
    
    def test_format_user_tags_multiple_users(self, mention_service, sample_user):
        """Тест форматирования тегов для нескольких пользователей."""
        user1 = Mock(spec=User)
        user1.id = 1
        user1.username = "user1"
        user1.first_name = None
        
        user2 = Mock(spec=User)
        user2.id = 2
        user2.username = None
        user2.first_name = "User2"
        
        users = [user1, user2]
        tags = mention_service.format_user_tags(users)
        
        assert len(tags) == 2
        assert tags[0] == "@user1"
        assert tags[1] == "User2"
    
    def test_build_mention_message_success(self, mention_service, sample_user):
        """Тест построения сообщения с упоминаниями - успех."""
        mention_msg = MentionMessage(
            author=sample_user,
            original_text="@all Привет",
            cleaned_text="Привет",
            chat_id=123,
            message_id=456
        )
        users = [sample_user]
        
        result = mention_service.build_mention_message(mention_msg, users)
        
        assert result is not None
        assert mention_msg.formatted_message in result
        assert f"@{sample_user.username}" in result
    
    def test_build_mention_message_too_long(self, mention_service, sample_user):
        """Тест построения сообщения - превышение максимальной длины."""
        # Создаем очень длинное сообщение
        long_message = "A" * 4000  # Почти максимальная длина
        mention_msg = MentionMessage(
            author=sample_user,
            original_text="@all " + long_message,
            cleaned_text=long_message,
            chat_id=123,
            message_id=456
        )
        # Создаем много пользователей для длинных тегов
        users = [Mock(spec=User, id=i, username=f"user{i}", first_name=None) for i in range(100)]
        
        result = mention_service.build_mention_message(mention_msg, users)
        
        # Должно вернуть None, так как сообщение слишком длинное
        assert result is None
    
    @pytest.mark.asyncio
    async def test_send_mention_message_success(self, mention_service):
        """Тест отправки сообщения с упоминаниями - успех."""
        mention_service.bot.send_message = AsyncMock(return_value=Mock(message_id=789))
        
        result = await mention_service.send_mention_message(
            chat_id=123,
            message="Привет @user1"
        )
        
        assert result is True
        mention_service.bot.send_message.assert_called_once_with(
            chat_id=123,
            text="Привет @user1",
            parse_mode="HTML"
        )
    
    @pytest.mark.asyncio
    async def test_send_mention_message_error(self, mention_service):
        """Тест отправки сообщения при ошибке Telegram API."""
        mention_service.bot.send_message = AsyncMock(side_effect=TelegramError("API Error"))
        
        result = await mention_service.send_mention_message(
            chat_id=123,
            message="Привет @user1"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_original_message_success(self, mention_service):
        """Тест удаления оригинального сообщения - успех."""
        mention_service.bot.delete_message = AsyncMock(return_value=True)
        
        result = await mention_service.delete_original_message(
            chat_id=123,
            message_id=456
        )
        
        assert result is True
        mention_service.bot.delete_message.assert_called_once_with(
            chat_id=123,
            message_id=456
        )
    
    @pytest.mark.asyncio
    async def test_delete_original_message_error(self, mention_service):
        """Тест удаления оригинального сообщения при ошибке."""
        mention_service.bot.delete_message = AsyncMock(side_effect=TelegramError("API Error"))
        
        result = await mention_service.delete_original_message(
            chat_id=123,
            message_id=456
        )
        
        assert result is False
