"""
Unit-тесты для обработчиков сообщений.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from bot.constants import ChatType

from bot.handlers.messages import MessageHandler
from bot.models.message import MentionMessage
from bot.services.chat_service import ChatService
from bot.services.mention_service import MentionService


class TestMessageHandler:
    """Тесты для MessageHandler."""
    
    @pytest.mark.asyncio
    async def test_handle_message_no_message(self, mock_context):
        """Тест обработки сообщения без update.message."""
        update = Mock(spec=Update)
        update.message = None
        
        handler = MessageHandler()
        await handler.handle_message(update, mock_context)
        
        # Не должно быть вызовов
        mock_context.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_no_text(self, group_chat, sample_user, mock_context):
        """Тест обработки сообщения без текста."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = None
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        with patch('bot.handlers.messages.chat_storage') as mock_storage:
            await handler.handle_message(update, mock_context)
            
            # Чат должен быть зарегистрирован
            mock_storage.register_chat.assert_called_once_with(group_chat)
            # Сообщение не должно быть отправлено
            mock_context.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_no_mention_trigger(self, group_chat, sample_user, mock_context):
        """Тест обработки сообщения без триггера упоминания."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = "Обычное сообщение без триггера"
        message.from_user = sample_user
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        with patch('bot.handlers.messages.chat_storage') as mock_storage, \
             patch.object(MentionService, 'has_mention_trigger', return_value=False):
            await handler.handle_message(update, mock_context)
            
            # Чат должен быть зарегистрирован
            mock_storage.register_chat.assert_called_once_with(group_chat)
            # Сообщение не должно быть отправлено
            mock_context.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_message_with_mention_trigger_not_group(self, private_chat, sample_user, mock_context):
        """Тест обработки сообщения с триггером в не-группе."""
        message = Mock(spec=Message)
        message.chat = private_chat
        message.chat_id = private_chat.id
        message.text = "@all Привет всем!"
        message.from_user = sample_user
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        with patch('bot.handlers.messages.chat_storage') as mock_storage, \
             patch.object(MentionService, 'has_mention_trigger', return_value=True), \
             patch('bot.handlers.messages.ChatType.is_group', return_value=False):
            await handler.handle_message(update, mock_context)
            
            # Должно быть сообщение о том, что команда работает только в группах
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert "группах" in call_args.kwargs['text'].lower()
    
    @pytest.mark.asyncio
    async def test_handle_message_bot_not_admin(self, group_chat, sample_user, mock_context):
        """Тест обработки сообщения, когда бот не является администратором."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = "@all Привет всем!"
        message.from_user = sample_user
        message.message_id = 123
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        mock_chat_service = Mock(spec=ChatService)
        mock_chat_service.is_bot_admin = AsyncMock(return_value=False)
        
        with patch('bot.handlers.messages.chat_storage') as mock_storage, \
             patch.object(MentionService, 'has_mention_trigger', return_value=True), \
             patch('bot.handlers.messages.ChatType.is_group', return_value=True), \
             patch('bot.handlers.messages.ChatService', return_value=mock_chat_service):
            await handler.handle_message(update, mock_context)
            
            # Должно быть сообщение о том, что бот должен быть администратором
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert "администратором" in call_args.kwargs['text'].lower()
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self, group_chat, sample_user, mock_context):
        """Тест успешной обработки сообщения с упоминанием."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = "@all Привет всем!"
        message.from_user = sample_user
        message.message_id = 123
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        # Мокаем сервисы
        mock_chat_service = Mock(spec=ChatService)
        mock_chat_service.is_bot_admin = AsyncMock(return_value=True)
        mock_chat_service.get_all_members = AsyncMock(return_value=[sample_user])
        
        mock_mention_service = Mock(spec=MentionService)
        mock_mention_service.has_mention_trigger = Mock(return_value=True)
        mock_mention_service.extract_cleaned_text = Mock(return_value="Привет всем!")
        mock_mention_service.build_mention_message = Mock(return_value="Test User: Привет всем!\n@testuser")
        mock_mention_service.send_mention_message = AsyncMock(return_value=True)
        mock_mention_service.delete_original_message = AsyncMock(return_value=True)
        
        with patch('bot.handlers.messages.chat_storage') as mock_storage, \
             patch('bot.handlers.messages.ChatType.is_group', return_value=True), \
             patch('bot.handlers.messages.ChatService', return_value=mock_chat_service), \
             patch('bot.handlers.messages.MentionService', return_value=mock_mention_service):
            await handler.handle_message(update, mock_context)
            
            # Проверяем, что чат зарегистрирован
            mock_storage.register_chat.assert_called_once_with(group_chat)
            # Проверяем, что сообщение с упоминаниями отправлено
            mock_mention_service.send_mention_message.assert_called_once()
            # Проверяем, что оригинальное сообщение удалено
            mock_mention_service.delete_original_message.assert_called_once_with(
                group_chat.id,
                123
            )
    
    @pytest.mark.asyncio
    async def test_handle_message_no_members(self, group_chat, sample_user, mock_context):
        """Тест обработки сообщения, когда не найдены участники."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = "@all Привет всем!"
        message.from_user = sample_user
        message.message_id = 123
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        mock_chat_service = Mock(spec=ChatService)
        mock_chat_service.is_bot_admin = AsyncMock(return_value=True)
        mock_chat_service.get_all_members = AsyncMock(return_value=[])
        
        mock_mention_service = Mock(spec=MentionService)
        mock_mention_service.has_mention_trigger = Mock(return_value=True)
        mock_mention_service.extract_cleaned_text = Mock(return_value="Привет всем!")
        mock_mention_service.send_mention_message = AsyncMock(return_value=True)
        
        with patch('bot.handlers.messages.chat_storage'), \
             patch('bot.handlers.messages.ChatType.is_group', return_value=True), \
             patch('bot.handlers.messages.ChatService', return_value=mock_chat_service), \
             patch('bot.handlers.messages.MentionService', return_value=mock_mention_service):
            await handler.handle_message(update, mock_context)
            
            # Должно быть сообщение о том, что участники не найдены
            mock_mention_service.send_mention_message.assert_called_once()
            call_args = mock_mention_service.send_mention_message.call_args
            assert "Не удалось найти участников" in call_args.kwargs['message']
    
    @pytest.mark.asyncio
    async def test_handle_message_too_long(self, group_chat, sample_user, mock_context):
        """Тест обработки сообщения, которое слишком длинное."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = "@all Привет всем!"
        message.from_user = sample_user
        message.message_id = 123
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        mock_chat_service = Mock(spec=ChatService)
        mock_chat_service.is_bot_admin = AsyncMock(return_value=True)
        mock_chat_service.get_all_members = AsyncMock(return_value=[sample_user])
        
        mock_mention_service = Mock(spec=MentionService)
        mock_mention_service.has_mention_trigger = Mock(return_value=True)
        mock_mention_service.extract_cleaned_text = Mock(return_value="Привет всем!")
        mock_mention_service.build_mention_message = Mock(return_value=None)  # Слишком длинное
        mock_mention_service.send_mention_message = AsyncMock(return_value=True)
        
        with patch('bot.handlers.messages.chat_storage'), \
             patch('bot.handlers.messages.ChatType.is_group', return_value=True), \
             patch('bot.handlers.messages.ChatService', return_value=mock_chat_service), \
             patch('bot.handlers.messages.MentionService', return_value=mock_mention_service):
            await handler.handle_message(update, mock_context)
            
            # Должно быть сообщение о том, что сообщение слишком длинное
            mock_mention_service.send_mention_message.assert_called_once()
            call_args = mock_mention_service.send_mention_message.call_args
            assert "Слишком много участников" in call_args.kwargs['message']
    
    @pytest.mark.asyncio
    async def test_handle_message_telegram_error(self, group_chat, sample_user, mock_context):
        """Тест обработки ошибки Telegram API."""
        message = Mock(spec=Message)
        message.chat = group_chat
        message.chat_id = group_chat.id
        message.text = "@all Привет всем!"
        message.from_user = sample_user
        message.message_id = 123
        
        update = Mock(spec=Update)
        update.message = message
        
        handler = MessageHandler()
        
        mock_chat_service = Mock(spec=ChatService)
        mock_chat_service.is_bot_admin = AsyncMock(return_value=True)
        mock_chat_service.get_all_members = AsyncMock(side_effect=TelegramError("API Error"))
        
        mock_mention_service = Mock(spec=MentionService)
        mock_mention_service.has_mention_trigger = Mock(return_value=True)
        mock_mention_service.extract_cleaned_text = Mock(return_value="Привет всем!")
        
        with patch('bot.handlers.messages.chat_storage'), \
             patch('bot.handlers.messages.ChatType.is_group', return_value=True), \
             patch('bot.handlers.messages.ChatService', return_value=mock_chat_service), \
             patch('bot.handlers.messages.MentionService', return_value=mock_mention_service):
            await handler.handle_message(update, mock_context)
            
            # Должно быть сообщение об ошибке
            mock_context.bot.send_message.assert_called()
            # Проверяем, что было отправлено сообщение об ошибке
            call_args_list = mock_context.bot.send_message.call_args_list
            assert any("ошибка" in str(call.kwargs.get('text', '')).lower() or 
                      "error" in str(call.kwargs.get('text', '')).lower() 
                      for call in call_args_list)
