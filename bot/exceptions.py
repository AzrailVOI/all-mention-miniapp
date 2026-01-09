"""Кастомные исключения и обработчики для Telegram API ошибок"""
import logging
from typing import Optional
from telegram.error import (
    TelegramError,
    BadRequest,
    InvalidToken,  # Заменяет Unauthorized в python-telegram-bot 20+
    Forbidden,
    Conflict,
    RetryAfter,
    NetworkError,
    TimedOut,
    ChatMigrated,
    EndPointNotFound  # Заменяет NotFound в python-telegram-bot 20+
)

logger = logging.getLogger(__name__)


class TelegramAPIError(Exception):
    """Базовое исключение для ошибок Telegram API"""
    def __init__(self, message: str, original_error: Optional[TelegramError] = None):
        super().__init__(message)
        self.original_error = original_error
        self.user_message = message


class ChatAccessError(TelegramAPIError):
    """Ошибка доступа к чату"""
    pass


class UserAccessError(TelegramAPIError):
    """Ошибка доступа к пользователю"""
    pass


class RateLimitError(TelegramAPIError):
    """Ошибка превышения лимита запросов"""
    def __init__(self, message: str, retry_after: Optional[int] = None, original_error: Optional[TelegramError] = None):
        super().__init__(message, original_error)
        self.retry_after = retry_after


class NetworkAPIError(TelegramAPIError):
    """Ошибка сети при обращении к Telegram API"""
    pass


def handle_telegram_error(error: TelegramError, context: Optional[str] = None) -> TelegramAPIError:
    """
    Обрабатывает TelegramError и преобразует в соответствующее кастомное исключение.
    
    Args:
        error: Исключение от Telegram API
        context: Дополнительный контекст (например, chat_id, user_id)
        
    Returns:
        Соответствующее кастомное исключение
    """
    context_str = f" [{context}]" if context else ""
    
    # В python-telegram-bot 20+ ChatNotFound и UserNotFound не существуют,
    # нужно проверять через Forbidden с соответствующими сообщениями
    if isinstance(error, Forbidden):
        logger.warning(f"Доступ запрещен{context_str}: {error}")
        # Определяем тип запрета по сообщению
        error_msg = str(error).lower()
        if "chat not found" in error_msg or "group chat was upgraded" in error_msg:
            return ChatAccessError("Чат не найден или недоступен", original_error=error)
        elif "bot was blocked" in error_msg or "user is deactivated" in error_msg:
            return UserAccessError("Пользователь недоступен", original_error=error)
        else:
            return ChatAccessError("Доступ к чату запрещен", original_error=error)
    
    elif isinstance(error, InvalidToken):
        logger.error(f"Неавторизован (невалидный токен){context_str}: {error}")
        return TelegramAPIError("Бот не авторизован. Проверьте токен.", original_error=error)
    
    elif isinstance(error, BadRequest):
        logger.warning(f"Неверный запрос{context_str}: {error}")
        # Проверяем специфичные случаи BadRequest
        error_msg = str(error).lower()
        if "chat not found" in error_msg:
            return ChatAccessError("Чат не найден или недоступен", original_error=error)
        elif "user not found" in error_msg:
            return UserAccessError("Пользователь не найден", original_error=error)
        else:
            return TelegramAPIError(f"Неверный запрос к Telegram API: {error}", original_error=error)
    
    elif isinstance(error, EndPointNotFound):
        logger.warning(f"Ресурс не найден{context_str}: {error}")
        return TelegramAPIError("Запрашиваемый ресурс не найден", original_error=error)
    
    elif isinstance(error, RetryAfter):
        retry_after = getattr(error, 'retry_after', None)
        logger.warning(f"Превышен лимит запросов{context_str}. Retry after: {retry_after} сек")
        return RateLimitError(
            f"Превышен лимит запросов. Попробуйте через {retry_after} секунд",
            retry_after=retry_after,
            original_error=error
        )
    
    elif isinstance(error, (NetworkError, TimedOut)):
        logger.warning(f"Ошибка сети{context_str}: {error}")
        return NetworkAPIError("Ошибка сети при обращении к Telegram API. Попробуйте позже.", original_error=error)
    
    elif isinstance(error, Conflict):
        logger.warning(f"Конфликт{context_str}: {error}")
        return TelegramAPIError("Конфликт при выполнении операции", original_error=error)
    
    else:
        # Неизвестная ошибка Telegram API
        logger.error(f"Неизвестная ошибка Telegram API{context_str}: {error}", exc_info=True)
        return TelegramAPIError(f"Ошибка Telegram API: {error}", original_error=error)


def get_user_friendly_message(error: TelegramAPIError) -> str:
    """
    Получает понятное пользователю сообщение об ошибке.
    
    Args:
        error: Кастомное исключение
        
    Returns:
        Понятное сообщение для пользователя
    """
    return error.user_message if hasattr(error, 'user_message') else str(error)
