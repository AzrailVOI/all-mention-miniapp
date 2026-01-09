"""Вспомогательные функции для работы с чатами в API"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from telegram import Bot, Chat
from telegram.error import TelegramError

from bot.services.chat_service import ChatService
from bot.services.chat_storage_service import chat_storage
from bot.constants import ChatType
from bot.config import Config
from bot.exceptions import handle_telegram_error

logger = logging.getLogger(__name__)

# Типы для данных чата
ChatDataDict = Dict[str, Any]
StatsDict = Dict[str, int]


async def fetch_chat_photo(bot: Bot, chat: Chat) -> Optional[str]:
    """
    Получает URL фото чата.
    
    Args:
        bot: Экземпляр Telegram Bot
        chat: Объект Chat из Telegram
        
    Returns:
        URL фото чата или None, если фото отсутствует
    """
    try:
        if hasattr(chat, 'photo') and chat.photo:
            photo = chat.photo.big_file_id
            file = await bot.get_file(photo)
            file_path = file.file_path
            
            # Формируем полный URL
            full_photo_url = f"https://api.telegram.org/file/bot{Config.TOKEN}/{file_path}"
            logger.info(f"[ChatHelpers] Получено фото чата {chat.id}: {full_photo_url}")
            return full_photo_url
    except Exception as e:
        logger.error(f"[ChatHelpers] Ошибка при получении фото чата {chat.id}: {e}", exc_info=True)
    return None


def build_chat_data(chat: Chat, photo_url: Optional[str] = None) -> ChatDataDict:
    """
    Формирует словарь с данными чата для API ответа.
    
    Args:
        chat: Объект Chat из Telegram
        photo_url: URL фото чата (опционально)
        
    Returns:
        Словарь с данными чата
    """
    return {
        'id': chat.id,
        'title': chat.title or 'Без названия',
        'type': chat.type,
        'username': getattr(chat, 'username', None),
        'members_count': getattr(chat, 'members_count', None),
        'photo_url': photo_url
    }


async def process_chat(
    bot: Bot,
    chat_service: ChatService,
    chat_id: int,
    user_id: int
) -> Tuple[Optional[ChatDataDict], Dict[str, int]]:
    """
    Обрабатывает один чат: проверяет права и получает данные.
    
    Args:
        bot: Экземпляр Telegram Bot
        chat_service: Сервис для работы с чатами
        chat_id: ID чата для обработки
        user_id: ID пользователя для проверки прав
        
    Returns:
        Tuple (данные чата или None, словарь со счетчиками пропущенных чатов)
    """
    skipped = {
        'not_group': 0,
        'not_admin': 0,
        'not_creator': 0
    }
    
    try:
        # Получаем информацию о чате
        chat = await bot.get_chat(chat_id)
        
        # Пропускаем, если это не группа или супергруппа
        if not ChatType.is_group(chat.type):
            skipped['not_group'] = 1
            logger.debug(f"[ChatHelpers] Чат {chat_id} пропущен: не группа")
            return None, skipped
        
        chat_title = chat.title or 'Без названия'
        logger.info(f"[ChatHelpers] Проверка чата {chat_id} ({chat_title}, {chat.type})")
        
        # Проверяем, является ли бот администратором
        is_bot_admin = await chat_service.is_bot_admin(chat_id)
        if not is_bot_admin:
            skipped['not_admin'] = 1
            logger.warning(f"[ChatHelpers] Чат {chat_id} пропущен: бот не является администратором")
            return None, skipped
        
        # Проверяем, является ли пользователь создателем
        is_user_creator = await chat_service.is_user_creator(chat_id, user_id)
        if not is_user_creator:
            skipped['not_creator'] = 1
            logger.warning(f"[ChatHelpers] Чат {chat_id} пропущен: пользователь {user_id} не является создателем")
            return None, skipped
        
        # Получаем фото чата
        photo_url = await fetch_chat_photo(bot, chat)
        
        # Формируем данные чата
        chat_data = build_chat_data(chat, photo_url)
        
        # Сохраняем в хранилище
        chat_storage.register_chat(chat)
        
        logger.info(f"[ChatHelpers] Чат {chat_id} успешно обработан")
        return chat_data, skipped
        
    except TelegramError as e:
        telegram_error = handle_telegram_error(e, context=f"chat_id={chat_id}")
        logger.debug(f"[ChatHelpers] Не удалось получить информацию о чате {chat_id}: {telegram_error.user_message}")
        return None, skipped
    except Exception as e:
        logger.error(f"[ChatHelpers] Ошибка при обработке чата {chat_id}: {e}")
        return None, skipped


def calculate_stats(chats: List[ChatDataDict]) -> StatsDict:
    """
    Подсчитывает статистику по чатам.
    
    Args:
        chats: Список чатов
        
    Returns:
        Словарь со статистикой
    """
    return {
        'total': len(chats),
        'groups': len([c for c in chats if c.get('type') == 'group']),
        'supergroups': len([c for c in chats if c.get('type') == 'supergroup']),
        'private': 0,
        'channels': 0
    }


def get_info_message(has_chats: bool, has_stored_chats: bool) -> Optional[str]:
    """
    Формирует информационное сообщение для пользователя.
    
    Args:
        has_chats: Есть ли отфильтрованные чаты
        has_stored_chats: Есть ли чаты в хранилище
        
    Returns:
        Информационное сообщение или None
    """
    if not has_chats and not has_stored_chats:
        return (
            "Чаты не найдены. Telegram Bot API не предоставляет способ получить список всех чатов.\n\n"
            "Чаты будут автоматически регистрироваться при:\n"
            "• Получении любого сообщения в группе\n"
            "• Добавлении бота в группу (событие my_chat_member)\n"
            "• Использовании команды /register в группе\n\n"
            "Отправьте любое сообщение в группе или используйте /register для регистрации."
        )
    return None
