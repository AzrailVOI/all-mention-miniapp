"""Обработчики событий чата (добавление бота, обновление чата)"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.chat_storage_service import chat_storage

logger = logging.getLogger(__name__)


async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик обновления участников чата"""
    if not update.chat_member:
        return
    
    chat = update.chat_member.chat
    
    # ВСЕГДА регистрируем чат при любом изменении участников
    # Это помогает отслеживать все чаты
    chat_storage.register_chat(chat)
    
    new_status = update.chat_member.new_chat_member.status
    old_status = update.chat_member.old_chat_member.status
    
    # Логируем добавление бота
    if new_status in ["member", "administrator", "creator"] and old_status == "left":
        logger.info(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")
        print(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")


async def handle_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик обновления статуса бота в чате"""
    if not update.my_chat_member:
        return
    
    chat = update.my_chat_member.chat
    new_status = update.my_chat_member.new_chat_member.status
    old_status = update.my_chat_member.old_chat_member.status
    
    # ВСЕГДА регистрируем чат при любом изменении статуса
    # Это критично для получения списка всех чатов, где добавлен бот
    chat_storage.register_chat(chat)
    
    # Регистрируем чат при добавлении бота
    if new_status in ["member", "administrator", "creator"] and old_status == "left":
        logger.info(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")
        print(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")
    elif new_status == "left":
        logger.info(f"[ChatEvents] Бот удален из чата: {chat.id} ({chat.type})")
        print(f"[ChatEvents] Бот удален из чата: {chat.id} ({chat.type})")
    else:
        logger.debug(f"[ChatEvents] Статус бота изменен в чате {chat.id}: {old_status} -> {new_status}")

