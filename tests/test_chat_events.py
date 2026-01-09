"""
Unit-тесты для обработчиков событий чата.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from telegram import Update, Chat, ChatMemberUpdated
from telegram.ext import ContextTypes

from bot.handlers.chat_events import (
    handle_chat_member_update,
    handle_my_chat_member_update
)
from bot.constants import ChatMemberStatus, ChatType


class TestChatMemberUpdate:
    """Тесты для handle_chat_member_update."""
    
    @pytest.mark.asyncio
    async def test_handle_chat_member_update_no_chat_member(self, mock_context):
        """Тест обработки обновления участника без update.chat_member."""
        update = Mock(spec=Update)
        update.chat_member = None
        
        await handle_chat_member_update(update, mock_context)
        
        # Не должно быть ошибок
        mock_context.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_chat_member_update_bot_added(self, group_chat, mock_context):
        """Тест обработки добавления бота в чат."""
        # Создаем мок ChatMemberUpdated
        new_member = Mock()
        new_member.status = ChatMemberStatus.ADMINISTRATOR.value
        
        old_member = Mock()
        old_member.status = ChatMemberStatus.LEFT.value
        
        chat_member = Mock(spec=ChatMemberUpdated)
        chat_member.chat = group_chat
        chat_member.new_chat_member = new_member
        chat_member.old_chat_member = old_member
        
        update = Mock(spec=Update)
        update.chat_member = chat_member
        update.effective_chat = group_chat
        
        # Патчим chat_storage в месте, где он импортируется
        with patch('bot.services.chat_storage_service.chat_storage') as mock_storage, \
             patch('bot.utils.handlers.chat_storage', mock_storage):
            await handle_chat_member_update(update, mock_context)
            
            # Чат должен быть зарегистрирован (вызывается через декоратор register_chat_on_call)
            assert mock_storage.register_chat.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_handle_chat_member_update_status_change(self, group_chat, mock_context):
        """Тест обработки изменения статуса участника."""
        new_member = Mock()
        new_member.status = ChatMemberStatus.MEMBER.value
        
        old_member = Mock()
        old_member.status = ChatMemberStatus.RESTRICTED.value
        
        chat_member = Mock(spec=ChatMemberUpdated)
        chat_member.chat = group_chat
        chat_member.new_chat_member = new_member
        chat_member.old_chat_member = old_member
        
        update = Mock(spec=Update)
        update.chat_member = chat_member
        update.effective_chat = group_chat
        
        # Патчим chat_storage в месте, где он импортируется
        with patch('bot.services.chat_storage_service.chat_storage') as mock_storage, \
             patch('bot.utils.handlers.chat_storage', mock_storage):
            await handle_chat_member_update(update, mock_context)
            
            # Чат должен быть зарегистрирован (вызывается через декоратор register_chat_on_call)
            assert mock_storage.register_chat.call_count >= 1


class TestMyChatMemberUpdate:
    """Тесты для handle_my_chat_member_update."""
    
    @pytest.mark.asyncio
    async def test_handle_my_chat_member_update_no_my_chat_member(self, mock_context):
        """Тест обработки обновления статуса бота без update.my_chat_member."""
        update = Mock(spec=Update)
        update.my_chat_member = None
        
        await handle_my_chat_member_update(update, mock_context)
        
        # Не должно быть ошибок
        mock_context.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_my_chat_member_update_bot_added(self, group_chat, mock_context):
        """Тест обработки добавления бота в чат."""
        new_member = Mock()
        new_member.status = ChatMemberStatus.ADMINISTRATOR.value
        
        old_member = Mock()
        old_member.status = ChatMemberStatus.LEFT.value
        
        chat_member = Mock(spec=ChatMemberUpdated)
        chat_member.chat = group_chat
        chat_member.new_chat_member = new_member
        chat_member.old_chat_member = old_member
        
        update = Mock(spec=Update)
        update.my_chat_member = chat_member
        update.effective_chat = group_chat
        
        # Патчим chat_storage в месте, где он импортируется
        with patch('bot.services.chat_storage_service.chat_storage') as mock_storage, \
             patch('bot.utils.handlers.chat_storage', mock_storage):
            await handle_my_chat_member_update(update, mock_context)
            
            # Чат должен быть зарегистрирован (вызывается через декоратор register_chat_on_call)
            assert mock_storage.register_chat.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_handle_my_chat_member_update_bot_removed(self, group_chat, mock_context):
        """Тест обработки удаления бота из чата."""
        new_member = Mock()
        new_member.status = ChatMemberStatus.LEFT.value
        
        old_member = Mock()
        old_member.status = ChatMemberStatus.ADMINISTRATOR.value
        
        chat_member = Mock(spec=ChatMemberUpdated)
        chat_member.chat = group_chat
        chat_member.new_chat_member = new_member
        chat_member.old_chat_member = old_member
        
        update = Mock(spec=Update)
        update.my_chat_member = chat_member
        update.effective_chat = group_chat
        
        # Патчим chat_storage в месте, где он импортируется
        with patch('bot.services.chat_storage_service.chat_storage') as mock_storage, \
             patch('bot.utils.handlers.chat_storage', mock_storage):
            await handle_my_chat_member_update(update, mock_context)
            
            # Чат должен быть зарегистрирован (вызывается через декоратор register_chat_on_call)
            assert mock_storage.register_chat.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_handle_my_chat_member_update_status_change(self, group_chat, mock_context):
        """Тест обработки изменения статуса бота."""
        new_member = Mock()
        new_member.status = ChatMemberStatus.ADMINISTRATOR.value
        
        old_member = Mock()
        old_member.status = ChatMemberStatus.MEMBER.value
        
        chat_member = Mock(spec=ChatMemberUpdated)
        chat_member.chat = group_chat
        chat_member.new_chat_member = new_member
        chat_member.old_chat_member = old_member
        
        update = Mock(spec=Update)
        update.my_chat_member = chat_member
        update.effective_chat = group_chat
        
        # Патчим chat_storage в месте, где он импортируется
        with patch('bot.services.chat_storage_service.chat_storage') as mock_storage, \
             patch('bot.utils.handlers.chat_storage', mock_storage):
            await handle_my_chat_member_update(update, mock_context)
            
            # Чат должен быть зарегистрирован (вызывается через декоратор register_chat_on_call)
            assert mock_storage.register_chat.call_count >= 1
