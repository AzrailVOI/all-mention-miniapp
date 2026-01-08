"""Клиент для работы с Telegram Bot API в контексте Mini App"""
import logging
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError

from bot.config import Config
from bot.utils.errors import handle_telegram_error, get_user_friendly_message
from bot.utils.retry import retry_async, RetryConfig

logger = logging.getLogger(__name__)


class TelegramClient:
    """
    Обертка над Telegram Bot API для использования в Mini App.
    
    Предоставляет:
    - Переиспользование одного экземпляра Bot
    - Автоматическую инициализацию
    - Retry логику для всех запросов
    - Централизованную обработку ошибок
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Инициализирует TelegramClient.
        
        Args:
            token: Токен бота (по умолчанию из Config.TOKEN)
        """
        self._token = token or Config.TOKEN
        self._bot: Optional[Bot] = None
        self._initialized = False
        self._retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0
        )
    
    @property
    def bot(self) -> Bot:
        """
        Получает экземпляр Bot, создавая его при необходимости.
        
        Returns:
            Экземпляр Bot
        """
        if self._bot is None:
            self._bot = Bot(token=self._token)
            logger.info("[TelegramClient] Создан новый экземпляр Bot")
        return self._bot
    
    async def initialize(self) -> None:
        """
        Инициализирует бота (если еще не инициализирован).
        
        Должен вызываться перед использованием бота в async контексте.
        """
        if not self._initialized:
            await self.bot.initialize()
            self._initialized = True
            logger.debug("[TelegramClient] Bot инициализирован")
    
    async def get_chat(self, chat_id: int):
        """
        Получает информацию о чате с retry логикой.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Объект Chat
            
        Raises:
            TelegramError: При ошибке Telegram API
        """
        await self.initialize()
        try:
            return await retry_async(
                self.bot.get_chat,
                chat_id,
                config=self._retry_config
            )
        except TelegramError as e:
            handled_error = handle_telegram_error(e, f"chat_id={chat_id}")
            logger.error(f"[TelegramClient] Ошибка при получении чата {chat_id}: {get_user_friendly_message(handled_error)}")
            raise
    
    async def get_chat_member(self, chat_id: int, user_id: int):
        """
        Получает информацию об участнике чата с retry логикой.
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            
        Returns:
            Объект ChatMember
            
        Raises:
            TelegramError: При ошибке Telegram API
        """
        await self.initialize()
        try:
            return await retry_async(
                self.bot.get_chat_member,
                chat_id,
                user_id,
                config=self._retry_config
            )
        except TelegramError as e:
            handled_error = handle_telegram_error(e, f"chat_id={chat_id}, user_id={user_id}")
            logger.error(f"[TelegramClient] Ошибка при получении участника: {get_user_friendly_message(handled_error)}")
            raise
    
    async def get_chat_administrators(self, chat_id: int):
        """
        Получает список администраторов чата с retry логикой.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Список ChatMember объектов
            
        Raises:
            TelegramError: При ошибке Telegram API
        """
        await self.initialize()
        try:
            return await retry_async(
                self.bot.get_chat_administrators,
                chat_id,
                config=self._retry_config
            )
        except TelegramError as e:
            handled_error = handle_telegram_error(e, f"chat_id={chat_id}")
            logger.error(f"[TelegramClient] Ошибка при получении администраторов: {get_user_friendly_message(handled_error)}")
            raise
    
    async def get_me(self):
        """
        Получает информацию о боте с retry логикой.
        
        Returns:
            Объект User с информацией о боте
            
        Raises:
            TelegramError: При ошибке Telegram API
        """
        await self.initialize()
        try:
            return await retry_async(
                self.bot.get_me,
                config=self._retry_config
            )
        except TelegramError as e:
            handled_error = handle_telegram_error(e, "get_me")
            logger.error(f"[TelegramClient] Ошибка при получении информации о боте: {get_user_friendly_message(handled_error)}")
            raise
    
    async def get_file(self, file_id: str):
        """
        Получает информацию о файле с retry логикой.
        
        Args:
            file_id: ID файла
            
        Returns:
            Объект File
            
        Raises:
            TelegramError: При ошибке Telegram API
        """
        await self.initialize()
        try:
            return await retry_async(
                self.bot.get_file,
                file_id,
                config=self._retry_config
            )
        except TelegramError as e:
            handled_error = handle_telegram_error(e, f"file_id={file_id}")
            logger.error(f"[TelegramClient] Ошибка при получении файла: {get_user_friendly_message(handled_error)}")
            raise


# Глобальный экземпляр клиента для переиспользования
_global_client: Optional[TelegramClient] = None


def get_telegram_client() -> TelegramClient:
    """
    Получает глобальный экземпляр TelegramClient.
    
    Переиспользует один экземпляр для всех запросов.
    
    Returns:
        Экземпляр TelegramClient
    """
    global _global_client
    if _global_client is None:
        _global_client = TelegramClient()
        logger.info("[TelegramClient] Создан глобальный экземпляр TelegramClient")
    return _global_client
