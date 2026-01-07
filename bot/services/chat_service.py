"""Сервис для работы с чатами и участниками"""
import logging
from typing import List
from telegram import Bot, User
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class ChatService:
    """Сервис для работы с чатами"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def is_bot_admin(self, chat_id: int) -> bool:
        """Проверяет, является ли бот администратором чата"""
        try:
            bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
            return bot_member.status in ["administrator", "creator"]
        except TelegramError as e:
            logger.error(f"Ошибка при проверке прав администратора: {e}")
            return False
    
    async def get_all_members(self, chat_id: int) -> List[User]:
        """
        Получает список всех участников чата (кроме ботов)
        
        Примечание: Telegram Bot API не предоставляет прямой метод для получения
        полного списка участников группы. Используем доступные методы:
        1. get_chat_administrators - получает всех администраторов
        2. Для получения остальных участников требуется использовать методы,
           которые доступны только в Telegram Client API (MTProto), а не в Bot API.
        
        В Bot API можно получить информацию о конкретном участнике через get_chat_member,
        но для этого нужно знать его user_id заранее.
        """
        members = []
        seen_user_ids = set()
        
        try:
            # Получаем всех администраторов (включая создателя)
            admins = await self.bot.get_chat_administrators(chat_id)
            
            for admin in admins:
                user = admin.user
                if not user.is_bot and user.id not in seen_user_ids:
                    members.append(user)
                    seen_user_ids.add(user.id)
            
            # Примечание: Для получения всех участников группы в Bot API нет прямого метода.
            # Можно попробовать использовать get_chat_member для известных user_id,
            # но это требует предварительного знания ID всех участников.
            # Альтернатива - использовать Telegram Client API (pyrogram, telethon),
            # но это выходит за рамки Bot API.
            
            logger.info(f"Получено {len(members)} участников из администраторов чата {chat_id}")
            
        except TelegramError as e:
            logger.error(f"Ошибка при получении участников чата: {e}")
            raise
        
        return members
    
    async def get_chat_member_count(self, chat_id: int) -> int:
        """Получает количество участников в чате"""
        try:
            chat = await self.bot.get_chat(chat_id)
            return chat.get_members_count() if hasattr(chat, 'get_members_count') else 0
        except TelegramError as e:
            logger.error(f"Ошибка при получении количества участников: {e}")
            return 0

