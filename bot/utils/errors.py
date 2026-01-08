"""Обработка ошибок Telegram API"""
import logging
from typing import Optional
from telegram.error import (
    TelegramError,
    BadRequest,
    Conflict,
    RetryAfter,
    NetworkError,
    TimedOut,
    ChatMigrated,
    InvalidToken,
)

logger = logging.getLogger(__name__)


class TelegramAPIError(Exception):
    """Базовое исключение для ошибок Telegram API"""
    pass


class ChatNotFoundError(TelegramAPIError):
    """Чат не найден"""
    pass


class UnauthorizedError(TelegramAPIError):
    """Бот не авторизован"""
    pass


class ForbiddenError(TelegramAPIError):
    """Доступ запрещен"""
    pass


class RateLimitError(TelegramAPIError):
    """Превышен лимит запросов"""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__()
        self.retry_after = retry_after


def handle_telegram_error(error: TelegramError, context: Optional[str] = None) -> TelegramAPIError:
    """
    Обрабатывает ошибку Telegram API и возвращает соответствующее исключение.
    
    Args:
        error: Исключение от Telegram API
        context: Контекст операции (для логирования)
        
    Returns:
        Соответствующее исключение приложения
    """
    context_str = f" [{context}]" if context else ""
    
    # Invalid token
    if isinstance(error, InvalidToken):
        logger.error(f"Invalid bot token{context_str}: {error}")
        return UnauthorizedError("Неверный токен бота")
    
    # BadRequest: разбираем по тексту (в v20 многие кейсы приходят как BadRequest)
    if isinstance(error, BadRequest):
        msg = str(error).lower()
        
        # Чат не найден
        if "chat not found" in msg:
            logger.warning(f"Chat not found{context_str}: {error}")
            return ChatNotFoundError("Чат не найден. Возможно, бот был удален из группы.")
        
        # Доступ запрещен / бот кикнут / недостаточно прав
        if "forbidden" in msg or "bot was kicked" in msg or "not enough rights" in msg:
            logger.error(f"Access forbidden{context_str}: {error}")
            return ForbiddenError("Доступ запрещен. Проверьте права бота и статус в чате.")
        
        logger.warning(f"Bad request{context_str}: {error}")
        return TelegramAPIError(f"Неверный запрос: {error}")
    
    elif isinstance(error, ChatMigrated):
        logger.warning(f"Chat migrated{context_str}: {error}")
        return ChatNotFoundError(f"Чат был мигрирован в супергруппу: {error.new_chat_id}")
    
    elif isinstance(error, RetryAfter):
        retry_after = getattr(error, 'retry_after', None)
        logger.warning(f"Rate limit exceeded{context_str}, retry after {retry_after}s: {error}")
        return RateLimitError(retry_after=retry_after)
    
    elif isinstance(error, (NetworkError, TimedOut)):
        logger.warning(f"Network error{context_str}: {error}")
        return TelegramAPIError(f"Ошибка сети: {error}")
    
    if isinstance(error, Conflict):
        logger.warning(f"Conflict{context_str}: {error}")
        return TelegramAPIError(f"Конфликт: {error}")
    
    logger.error(f"Unknown Telegram error{context_str}: {error}", exc_info=True)
    return TelegramAPIError(f"Ошибка Telegram API: {error}")


def get_user_friendly_message(error: TelegramAPIError) -> str:
    """
    Возвращает понятное пользователю сообщение об ошибке.
    
    Args:
        error: Исключение приложения
        
    Returns:
        Понятное сообщение для пользователя
    """
    if isinstance(error, ChatNotFoundError):
        return "Чат не найден. Возможно, бот был удален из группы."
    
    elif isinstance(error, UnauthorizedError):
        return "Бот не авторизован. Проверьте токен бота."
    
    elif isinstance(error, ForbiddenError):
        return "Доступ запрещен. Убедитесь, что бот является администратором группы."
    
    elif isinstance(error, RateLimitError):
        if error.retry_after:
            return f"Превышен лимит запросов. Попробуйте через {error.retry_after} секунд."
        return "Превышен лимит запросов. Попробуйте позже."
    
    else:
        return str(error) or "Произошла ошибка. Попробуйте позже."
