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
    new_status = update.chat_member.new_chat_member.status
    old_status = update.chat_member.old_chat_member.status
    
    # Регистрируем чат при добавлении бота
    if new_status in ["member", "administrator", "creator"] and old_status == "left":
        chat_storage.register_chat(chat)
        logger.info(f"Бот добавлен в чат: {chat.id} ({chat.type})")
    
    # Обновляем информацию о чате
    if chat:
        chat_storage.register_chat(chat)


async def handle_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик обновления статуса бота в чате"""
    if not update.my_chat_member:
        return
    
    chat = update.my_chat_member.chat
    new_status = update.my_chat_member.new_chat_member.status
    old_status = update.my_chat_member.old_chat_member.status
    
    # Регистрируем чат при добавлении бота
    if new_status in ["member", "administrator", "creator"] and old_status == "left":
        chat_storage.register_chat(chat)
        logger.info(f"Бот добавлен в чат: {chat.id} ({chat.type})")
    elif new_status == "left":
        logger.info(f"Бот удален из чата: {chat.id} ({chat.type})")
    
    # Обновляем информацию о чате
    if chat:
        chat_storage.register_chat(chat)

