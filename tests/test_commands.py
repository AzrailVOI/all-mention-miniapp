"""
Unit-тесты для обработчиков команд.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

from bot.constants import ChatType

from bot.handlers.commands import (
    start_command,
    chats_command,
    register_chat_command,
    stats_command,
    help_command
)
from bot.utils.handlers import register_chat_on_call


class TestStartCommand:
    """Тесты для команды /start."""
    
    @pytest.mark.asyncio
    async def test_start_command_private_chat(self, private_chat, sample_user, mock_context, mock_bot):
        """Тест команды /start в приватном чате."""
        update = Mock(spec=Update)
        update.effective_chat = private_chat
        update.effective_user = sample_user
        
        with patch('bot.handlers.commands.is_private_chat', return_value=True), \
             patch('bot.handlers.commands.create_mini_app_keyboard') as mock_keyboard:
            mock_keyboard.return_value = Mock()
            
            await start_command(update, mock_context)
            
            # Проверяем, что сообщение отправлено
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == private_chat.id
            assert "Привет" in call_args.kwargs['text']
            assert call_args.kwargs['reply_markup'] is not None
    
    @pytest.mark.asyncio
    async def test_start_command_group_chat(self, group_chat, sample_user, mock_context):
        """Тест команды /start в групповом чате."""
        update = Mock(spec=Update)
        update.effective_chat = group_chat
        update.effective_user = sample_user
        
        with patch('bot.handlers.commands.is_private_chat', return_value=False):
            await start_command(update, mock_context)
            
            # Проверяем, что сообщение отправлено без клавиатуры
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == group_chat.id
            assert call_args.kwargs['reply_markup'] is None


class TestChatsCommand:
    """Тесты для команды /chats."""
    
    @pytest.mark.asyncio
    async def test_chats_command_private_chat(self, private_chat, sample_user, mock_context):
        """Тест команды /chats в приватном чате."""
        update = Mock(spec=Update)
        update.effective_chat = private_chat
        update.effective_user = sample_user
        
        with patch('bot.handlers.commands.is_private_chat', return_value=True), \
             patch('bot.handlers.commands.create_mini_app_keyboard') as mock_keyboard:
            mock_keyboard.return_value = Mock()
            
            await chats_command(update, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == private_chat.id
            assert "Mini App" in call_args.kwargs['text']
            assert call_args.kwargs['reply_markup'] is not None
    
    @pytest.mark.asyncio
    async def test_chats_command_group_chat(self, group_chat, sample_user, mock_context):
        """Тест команды /chats в групповом чате."""
        update = Mock(spec=Update)
        update.effective_chat = group_chat
        update.effective_user = sample_user
        
        with patch('bot.handlers.commands.is_private_chat', return_value=False):
            await chats_command(update, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == group_chat.id
            assert "приватном чате" in call_args.kwargs['text']


class TestRegisterChatCommand:
    """Тесты для команды /register."""
    
    @pytest.mark.asyncio
    async def test_register_chat_command_group(self, group_chat, sample_user, mock_context):
        """Тест команды /register в группе."""
        update = Mock(spec=Update)
        update.effective_chat = group_chat
        update.effective_user = sample_user
        
        with patch('bot.handlers.commands.is_group_chat', return_value=True):
            await register_chat_command(update, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == group_chat.id
            assert "зарегистрирован" in call_args.kwargs['text'].lower()
    
    @pytest.mark.asyncio
    async def test_register_chat_command_private(self, private_chat, sample_user, mock_context):
        """Тест команды /register в приватном чате."""
        update = Mock(spec=Update)
        update.effective_chat = private_chat
        update.effective_user = sample_user
        
        with patch('bot.handlers.commands.is_group_chat', return_value=False):
            await register_chat_command(update, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert "группах" in call_args.kwargs['text'].lower()


class TestStatsCommand:
    """Тесты для команды /stats."""
    
    @pytest.mark.asyncio
    async def test_stats_command_success(self, group_chat, sample_user, mock_context, chat_storage_service):
        """Тест команды /stats с успешным получением статистики."""
        update = Mock(spec=Update)
        update.effective_chat = group_chat
        update.effective_user = sample_user
        
        # Добавляем тестовые данные в хранилище
        test_chat = Mock(spec=Chat)
        test_chat.id = 1
        test_chat.title = "Test Group"
        test_chat.type = ChatType.GROUP
        test_chat.username = None
        test_chat.members_count = 5
        chat_storage_service.register_chat(test_chat)
        
        with patch('bot.services.chat_storage_service.chat_storage', chat_storage_service):
            await stats_command(update, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == group_chat.id
            assert "Статистика" in call_args.kwargs['text']
            assert call_args.kwargs['parse_mode'] == "HTML"
            assert "Всего чатов" in call_args.kwargs['text']
    
    @pytest.mark.asyncio
    async def test_stats_command_empty(self, group_chat, sample_user, mock_context, chat_storage_service):
        """Тест команды /stats с пустым хранилищем."""
        update = Mock(spec=Update)
        update.effective_chat = group_chat
        update.effective_user = sample_user
        
        with patch('bot.services.chat_storage_service.chat_storage', chat_storage_service):
            await stats_command(update, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert "0" in call_args.kwargs['text']  # Должно быть 0 чатов


class TestHelpCommand:
    """Тесты для команды /help."""
    
    @pytest.mark.asyncio
    async def test_help_command(self, group_chat, sample_user, mock_context):
        """Тест команды /help."""
        update = Mock(spec=Update)
        update.effective_chat = group_chat
        update.effective_user = sample_user
        
        await help_command(update, mock_context)
        
        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert call_args.kwargs['chat_id'] == group_chat.id
        assert call_args.kwargs['parse_mode'] == "HTML"
        assert "Доступные команды" in call_args.kwargs['text']
        assert "/start" in call_args.kwargs['text']
        assert "/chats" in call_args.kwargs['text']
        assert "/register" in call_args.kwargs['text']
        assert "/stats" in call_args.kwargs['text']
        assert "/help" in call_args.kwargs['text']
