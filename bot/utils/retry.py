"""Retry логика с экспоненциальной задержкой"""
import asyncio
import logging
from typing import TypeVar, Callable, Optional, List, Type
from functools import wraps
from telegram.error import (
    TelegramError,
    NetworkError,
    TimedOut,
    RetryAfter,
    Conflict,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Конфигурация для retry логики"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_errors: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_errors = retryable_errors or [
            NetworkError,
            TimedOut,
            RetryAfter,
            Conflict,
        ]


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Вычисляет задержку для попытки с экспоненциальной задержкой.
    
    Args:
        attempt: Номер попытки (начинается с 0)
        config: Конфигурация retry
        
    Returns:
        Задержка в секундах
    """
    delay = config.initial_delay * (config.exponential_base ** attempt)
    return min(delay, config.max_delay)


async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Выполняет async функцию с retry логикой.
    
    Args:
        func: Async функция для выполнения
        *args: Позиционные аргументы
        config: Конфигурация retry (по умолчанию используется стандартная)
        **kwargs: Именованные аргументы
        
    Returns:
        Результат выполнения функции
        
    Raises:
        Последнее исключение, если все попытки исчерпаны
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except RetryAfter as e:
            # Для RetryAfter используем указанное время ожидания
            retry_after = getattr(e, 'retry_after', None)
            if retry_after:
                delay = float(retry_after)
                logger.warning(
                    f"Rate limit exceeded, retrying after {delay}s "
                    f"(attempt {attempt + 1}/{config.max_attempts})"
                )
                await asyncio.sleep(delay)
                continue
            else:
                # Если retry_after не указан, используем экспоненциальную задержку
                last_exception = e
                if attempt < config.max_attempts - 1:
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"RetryAfter error, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{config.max_attempts})"
                    )
                    await asyncio.sleep(delay)
                continue
        except tuple(config.retryable_errors) as e:
            last_exception = e
            if attempt < config.max_attempts - 1:
                delay = calculate_delay(attempt, config)
                logger.warning(
                    f"Retryable error {type(e).__name__}, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{config.max_attempts}): {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed for {func.__name__}"
                )
                raise
        except Exception as e:
            # Не retryable ошибки - пробрасываем сразу
            logger.error(f"Non-retryable error in {func.__name__}: {e}")
            raise
    
    # Если дошли сюда, все попытки исчерпаны
    if last_exception:
        raise last_exception
    raise RuntimeError(f"All {config.max_attempts} attempts failed for {func.__name__}")


def retry_decorator(config: Optional[RetryConfig] = None):
    """
    Декоратор для добавления retry логики к async функциям.
    
    Usage:
        @retry_decorator()
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper
    return decorator
