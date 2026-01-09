"""Утилиты для retry-логики с экспоненциальной задержкой"""
import asyncio
import logging
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
from telegram.error import (
    TelegramError,
    NetworkError,
    TimedOut,
    RetryAfter,
    Conflict
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


# Константы для retry
MAX_RETRIES = 3
INITIAL_DELAY = 1.0  # секунды
MAX_DELAY = 60.0  # секунды
BACKOFF_MULTIPLIER = 2.0


def calculate_delay(attempt: int, retry_after: Optional[int] = None) -> float:
    """
    Вычисляет задержку перед следующей попыткой.
    
    Args:
        attempt: Номер попытки (начиная с 1)
        retry_after: Время задержки от Telegram API (если есть)
        
    Returns:
        Задержка в секундах
    """
    if retry_after:
        # Используем задержку от Telegram API
        return min(float(retry_after), MAX_DELAY)
    
    # Экспоненциальная задержка: 1s, 2s, 4s, 8s...
    delay = INITIAL_DELAY * (BACKOFF_MULTIPLIER ** (attempt - 1))
    return min(delay, MAX_DELAY)


def should_retry(error: Exception) -> bool:
    """
    Определяет, нужно ли повторять попытку при данной ошибке.
    
    Args:
        error: Исключение
        
    Returns:
        True если нужно повторить, False в противном случае
    """
    if isinstance(error, RetryAfter):
        return True
    if isinstance(error, (NetworkError, TimedOut)):
        return True
    if isinstance(error, Conflict):
        # Конфликты могут быть временными
        return True
    return False


def retry_async(
    max_attempts: int = MAX_RETRIES,
    retry_on: Optional[Callable[[Exception], bool]] = None
) -> Callable:
    """
    Декоратор для retry-логики с экспоненциальной задержкой для async функций.
    
    Args:
        max_attempts: Максимальное количество попыток
        retry_on: Функция для определения, нужно ли повторять при данной ошибке
        
    Returns:
        Декорированная функция
    """
    if retry_on is None:
        retry_on = should_retry
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Проверяем, нужно ли повторять
                    if not retry_on(e):
                        logger.debug(f"Ошибка не требует retry: {type(e).__name__}")
                        raise
                    
                    # Если это последняя попытка, выбрасываем исключение
                    if attempt >= max_attempts:
                        logger.warning(
                            f"Достигнуто максимальное количество попыток ({max_attempts}) "
                            f"для {func.__name__}. Последняя ошибка: {e}"
                        )
                        raise
                    
                    # Вычисляем задержку
                    retry_after = None
                    if isinstance(e, RetryAfter):
                        retry_after = getattr(e, 'retry_after', None)
                    
                    delay = calculate_delay(attempt, retry_after)
                    
                    logger.info(
                        f"Попытка {attempt}/{max_attempts} не удалась для {func.__name__}: {e}. "
                        f"Повтор через {delay:.1f} сек."
                    )
                    
                    await asyncio.sleep(delay)
            
            # Не должно достигнуть этой точки, но на всякий случай
            if last_error:
                raise last_error
            raise RuntimeError("Retry логика завершилась неожиданно")
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = MAX_RETRIES,
    retry_on: Optional[Callable[[Exception], bool]] = None
) -> Callable:
    """
    Декоратор для retry-логики с экспоненциальной задержкой для sync функций.
    
    Args:
        max_attempts: Максимальное количество попыток
        retry_on: Функция для определения, нужно ли повторять при данной ошибке
        
    Returns:
        Декорированная функция
    """
    if retry_on is None:
        retry_on = should_retry
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time
            last_error = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Проверяем, нужно ли повторять
                    if not retry_on(e):
                        logger.debug(f"Ошибка не требует retry: {type(e).__name__}")
                        raise
                    
                    # Если это последняя попытка, выбрасываем исключение
                    if attempt >= max_attempts:
                        logger.warning(
                            f"Достигнуто максимальное количество попыток ({max_attempts}) "
                            f"для {func.__name__}. Последняя ошибка: {e}"
                        )
                        raise
                    
                    # Вычисляем задержку
                    retry_after = None
                    if isinstance(e, RetryAfter):
                        retry_after = getattr(e, 'retry_after', None)
                    
                    delay = calculate_delay(attempt, retry_after)
                    
                    logger.info(
                        f"Попытка {attempt}/{max_attempts} не удалась для {func.__name__}: {e}. "
                        f"Повтор через {delay:.1f} сек."
                    )
                    
                    time.sleep(delay)
            
            # Не должно достигнуть этой точки, но на всякий случай
            if last_error:
                raise last_error
            raise RuntimeError("Retry логика завершилась неожиданно")
        
        return wrapper
    return decorator
