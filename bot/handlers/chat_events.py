"""Обработчики событий чата (добавление бота, обновление чата)"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.chat_storage_service import chat_storage
from bot.utils.cache import get_cache
from bot.constants import ChatMemberUpdateStatus

logger = logging.getLogger(__name__)


async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик обновления участников чата.
    
    Обрабатывает события изменения статуса участников чата:
    - Регистрирует чат в хранилище
    - Инвалидирует кэш участников при изменениях
    - Логирует добавление бота в чат
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения обработчика
    """
    if not update.chat_member:
        return
    
    chat = update.chat_member.chat
    
    # ВСЕГДА регистрируем чат при любом изменении участников
    # Это помогает отслеживать все чаты
    try:
        chat_storage.register_chat(chat)
    except Exception as e:
        logger.error(f"Ошибка при регистрации чата {chat.id}: {e}", exc_info=True)
    
    # Инвалидируем кэш участников для этого чата
    cache = get_cache()
    cache.invalidate_pattern(f"members:{chat.id}:")
    
    new_status = update.chat_member.new_chat_member.status
    old_status = update.chat_member.old_chat_member.status
    
    # Логируем добавление бота
    if new_status in [ChatMemberUpdateStatus.MEMBER.value, ChatMemberUpdateStatus.ADMINISTRATOR.value, ChatMemberUpdateStatus.CREATOR.value] and old_status == ChatMemberUpdateStatus.LEFT.value:
        logger.info(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")


async def handle_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик обновления статуса бота в чате.
    
    Обрабатывает события изменения статуса бота в чате:
    - Регистрирует чат в хранилище при добавлении бота
    - Инвалидирует кэш при изменении статуса
    - Логирует добавление/удаление бота из чата
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения обработчика
    """
    if not update.my_chat_member:
        return
    
    chat = update.my_chat_member.chat
    new_status = update.my_chat_member.new_chat_member.status
    old_status = update.my_chat_member.old_chat_member.status
    
    # ВСЕГДА регистрируем чат при любом изменении статуса
    # Это критично для получения списка всех чатов, где добавлен бот
    try:
        chat_storage.register_chat(chat)
    except Exception as e:
        logger.error(f"Ошибка при регистрации чата {chat.id}: {e}", exc_info=True)
    
    # Инвалидируем кэш при изменении статуса бота
    cache = get_cache()
    cache.invalidate_pattern(f"chats:")
    cache.invalidate_pattern(f"members:{chat.id}:")
    
    # Регистрируем чат при добавлении бота
    if new_status in [ChatMemberUpdateStatus.MEMBER.value, ChatMemberUpdateStatus.ADMINISTRATOR.value, ChatMemberUpdateStatus.CREATOR.value] and old_status == ChatMemberUpdateStatus.LEFT.value:
        logger.info(f"[ChatEvents] Бот добавлен в чат: {chat.id} ({chat.type}) - {chat.title or 'Без названия'}")
    elif new_status == ChatMemberUpdateStatus.LEFT.value:
        logger.info(f"[ChatEvents] Бот удален из чата: {chat.id} ({chat.type})")
    else:
        logger.debug(f"[ChatEvents] Статус бота изменен в чате {chat.id}: {old_status} -> {new_status}")

