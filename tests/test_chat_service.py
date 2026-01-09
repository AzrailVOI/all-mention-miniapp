"""
Unit-тесты для ChatService.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from telegram.error import TelegramError

from bot.services.chat_service import ChatService
from bot.constants import ChatMemberStatus


class TestChatService:
    """Тесты для ChatService."""
    
    @pytest.mark.asyncio
    async def test_is_bot_admin_true(self, chat_service, sample_chat_member_owner):
        """Тест проверки прав администратора - бот является создателем."""
        chat_service.bot.get_chat_member = AsyncMock(return_value=sample_chat_member_owner)
        
        result = await chat_service.is_bot_admin(chat_id=123)
        
        assert result is True
        chat_service.bot.get_chat_member.assert_called_once_with(123, chat_service.bot.id)
    
    @pytest.mark.asyncio
    async def test_is_bot_admin_false(self, chat_service, sample_chat_member_member):
        """Тест проверки прав администратора - бот не является администратором."""
        # Мокаем обычного участника для бота
        bot_member = Mock()
        bot_member.status = ChatMemberStatus.MEMBER
        chat_service.bot.get_chat_member = AsyncMock(return_value=bot_member)
        
        result = await chat_service.is_bot_admin(chat_id=123)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_bot_admin_error(self, chat_service):
        """Тест проверки прав администратора при ошибке Telegram API."""
        chat_service.bot.get_chat_member = AsyncMock(side_effect=TelegramError("API Error"))
        
        result = await chat_service.is_bot_admin(chat_id=123)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_user_creator_true(self, chat_service, sample_user, sample_chat_member_owner):
        """Тест проверки, является ли пользователь создателем - True."""
        sample_chat_member_owner.user = sample_user
        sample_chat_member_owner.status = "creator"
        chat_service.bot.get_chat_administrators = AsyncMock(return_value=[sample_chat_member_owner])
        
        result = await chat_service.is_user_creator(chat_id=123, user_id=sample_user.id)
        
        assert result is True
        chat_service.bot.get_chat_administrators.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    async def test_is_user_creator_false(self, chat_service, sample_user, sample_chat_member_admin):
        """Тест проверки, является ли пользователь создателем - False (администратор, но не создатель)."""
        sample_chat_member_admin.user = sample_user
        sample_chat_member_admin.status = "administrator"
        chat_service.bot.get_chat_administrators = AsyncMock(return_value=[sample_chat_member_admin])
        
        result = await chat_service.is_user_creator(chat_id=123, user_id=sample_user.id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_user_creator_not_found(self, chat_service, sample_user, sample_chat_member_admin):
        """Тест проверки, является ли пользователь создателем - пользователь не найден."""
        other_user = Mock()
        other_user.id = 999
        sample_chat_member_admin.user = other_user
        chat_service.bot.get_chat_administrators = AsyncMock(return_value=[sample_chat_member_admin])
        
        result = await chat_service.is_user_creator(chat_id=123, user_id=sample_user.id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_chat_member_count_success(self, chat_service):
        """Тест получения количества участников чата."""
        # Мокаем get_chat и его метод get_members_count
        mock_chat = Mock()
        mock_chat.get_members_count = Mock(return_value=100)
        chat_service.bot.get_chat = AsyncMock(return_value=mock_chat)
        
        result = await chat_service.get_chat_member_count(chat_id=123)
        
        assert result == 100
        chat_service.bot.get_chat.assert_called_once_with(123)
        mock_chat.get_members_count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_chat_member_count_error(self, chat_service):
        """Тест получения количества участников при ошибке."""
        from telegram.error import TelegramError
        chat_service.bot.get_chat = AsyncMock(side_effect=TelegramError("API Error"))
        
        result = await chat_service.get_chat_member_count(chat_id=123)
        
        assert result == 0
        chat_service.bot.get_chat.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    async def test_get_chat_members_list_with_cache(self, chat_service, sample_user, sample_chat_member_admin):
        """Тест получения списка участников с использованием кэша."""
        from bot.services.member_cache_service import member_cache
        
        # Кэшируем данные
        cached_members = [
            {
                'id': sample_user.id,
                'first_name': sample_user.first_name,
                'last_name': sample_user.last_name,
                'username': sample_user.username,
                'is_bot': False,
                'status': 'administrator'
            }
        ]
        member_cache.cache_members(chat_id=123, members=cached_members)
        
        # Получаем участников (должны вернуться из кэша)
        result = await chat_service.get_chat_members_list(chat_id=123, use_cache=True)
        
        assert len(result) == 1
        assert result[0]['id'] == sample_user.id
        # Очищаем кэш после теста
        member_cache.clear_cache(123)
    
    @pytest.mark.asyncio
    async def test_get_chat_members_list_no_cache(self, chat_service, sample_user, sample_chat_member_admin):
        """Тест получения списка участников без кэша."""
        # Мокаем администраторов
        sample_chat_member_admin.user = sample_user
        chat_service.bot.get_chat_administrators = AsyncMock(return_value=[sample_chat_member_admin])
        
        result = await chat_service.get_chat_members_list(chat_id=123, use_cache=False)
        
        assert len(result) > 0
        assert any(m['id'] == sample_user.id for m in result)
        chat_service.bot.get_chat_administrators.assert_called_once_with(123)
