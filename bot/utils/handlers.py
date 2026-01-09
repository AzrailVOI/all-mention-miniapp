"""Утилиты для обработчиков"""
import logging
from functools import wraps
from typing import Callable, Awaitable, TypeVar, cast
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

from bot.services.chat_storage_service import chat_storage
from bot.config import Config
from bot.constants import ChatType

logger = logging.getLogger(__name__)

# Type variable для обработчиков
HandlerFunc = TypeVar('HandlerFunc', bound=Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]])


def register_chat_on_call(
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    """
    Декоратор для автоматической регистрации чата при вызове обработчика.
    
    Args:
        func: Функция-обработчик команды или сообщения
        
    Returns:
        Обернутая функция с автоматической регистрацией чата
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if chat:
            chat_storage.register_chat(chat)
            logger.debug(f"[Handler] Чат {chat.id} ({chat.type}) зарегистрирован в {func.__name__}")
        return await func(update, context)
    return wrapper


def create_mini_app_keyboard(button_text: str = "📱 Открыть Mini App") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой для открытия Mini App.
    
    Args:
        button_text: Текст кнопки
        
    Returns:
        InlineKeyboardMarkup с кнопкой Mini App
    """
    keyboard = [
        [InlineKeyboardButton(
            button_text,
            web_app={"url": Config.WEBAPP_URL}
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


def is_private_chat(chat: Chat) -> bool:
    """
    Проверяет, является ли чат приватным.
    
    Args:
        chat: Объект Chat из Telegram
        
    Returns:
        True если чат приватный, False в противном случае
    """
    return chat.type == ChatType.PRIVATE


def is_group_chat(chat: Chat) -> bool:
    """
    Проверяет, является ли чат группой или супергруппой.
    
    Args:
        chat: Объект Chat из Telegram
        
    Returns:
        True если чат является группой, False в противном случае
    """
    return ChatType.is_group(chat.type)
