"""Сервис для работы с упоминаниями участников"""
import logging
from typing import List, Optional
from telegram import Bot, User
from telegram.error import TelegramError

from bot.models.message import MentionMessage
from bot.config import Config

logger = logging.getLogger(__name__)


class MentionService:
    """Сервис для обработки упоминаний участников"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Config
    
    def extract_cleaned_text(self, text: str) -> str:
        """Удаляет триггеры упоминания из текста"""
        cleaned = text
        for trigger in self.config.MENTION_TRIGGERS:
            cleaned = cleaned.replace(trigger, "").replace(trigger.lower(), "")
        return cleaned.strip()
    
    def has_mention_trigger(self, text: str) -> bool:
        """Проверяет, содержит ли текст триггер упоминания"""
        text_lower = text.lower()
        return any(trigger.lower() in text_lower for trigger in self.config.MENTION_TRIGGERS)
    
    def format_user_tags(self, users: List[User]) -> List[str]:
        """Форматирует список пользователей в теги"""
        tags = []
        for user in users:
            if user.username:
                tags.append(f"@{user.username}")
            elif user.first_name:
                tags.append(user.first_name)
            else:
                tags.append(f"User {user.id}")
        return tags
    
    def build_mention_message(
        self, 
        mention_msg: MentionMessage, 
        users: List[User]
    ) -> Optional[str]:
        """
        Строит сообщение с упоминаниями участников
        
        Returns:
            Строка с сообщением или None, если сообщение слишком длинное
        """
        tags = self.format_user_tags(users)
        tags_text = " ".join(tags)
        
        response = f"{mention_msg.formatted_message}\n{tags_text}"
        
        # Проверяем длину сообщения
        if len(response) > self.config.MAX_MESSAGE_LENGTH:
            return None
        
        return response
    
    async def send_mention_message(
        self, 
        chat_id: int, 
        message: str
    ) -> bool:
        """Отправляет сообщение с упоминаниями"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
            return True
        except TelegramError as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False
    
    async def delete_original_message(
        self, 
        chat_id: int, 
        message_id: int
    ) -> bool:
        """Удаляет оригинальное сообщение"""
        try:
            await self.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
            return True
        except TelegramError as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")
            return False

