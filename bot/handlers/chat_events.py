"""Обработчики событий чата (добавление бота, обновление чата)"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.chat_storage_service import chat_storage
from bot.constants import ChatMemberStatus
from bot.utils.handlers import register_chat_on_call

logger = logging.getLogger(__name__)


@register_chat_on_call
async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик обновления участников чата.
    
    Обрабатывает события изменения статуса участников чата.
    Автоматически регистрирует чат в хранилище.
    
    Args:
        update: Объект Update с информацией о событии
        context: Контекст выполнения обработчика
    """
    if not update.chat_member:
        return
    
    chat = update.chat_member.chat
    
    new_status = update.chat_member.new_chat_member.status
    old_status = update.chat_member.old_chat_member.status
    
    # Логируем добавление бота
    if ChatMemberStatus.is_active(new_status) and old_status == ChatMemberStatus.LEFT:
        logger.info(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")


@register_chat_on_call
async def handle_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик обновления статуса бота в чате.
    
    Обрабатывает события изменения статуса бота (добавление, удаление, изменение прав).
    Автоматически регистрирует чат в хранилище при любом изменении статуса.
    
    Args:
        update: Объект Update с информацией о событии
        context: Контекст выполнения обработчика
    """
    if not update.my_chat_member:
        return
    
    chat = update.my_chat_member.chat
    new_status = update.my_chat_member.new_chat_member.status
    old_status = update.my_chat_member.old_chat_member.status
    
    # Регистрируем чат при добавлении бота
    if ChatMemberStatus.is_active(new_status) and old_status == ChatMemberStatus.LEFT:
        logger.info(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")
    elif new_status == ChatMemberStatus.LEFT:
        logger.info(f"[ChatEvents] Бот удален из чата: {chat.id} ({chat.type})")
    else:
        logger.debug(f"[ChatEvents] Статус бота изменен в чате {chat.id}: {old_status} -> {new_status}")

