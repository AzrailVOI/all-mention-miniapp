"""Утилиты для батчинга запросов к Telegram API"""
import asyncio
import logging
from typing import List, TypeVar, Callable, Coroutine, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def batch_process(
    items: List[Any],
    processor: Callable[[Any], Coroutine[Any, Any, T]],
    max_concurrent: int = 5,
    error_handler: Optional[Callable[[Any, Exception], None]] = None
) -> List[Optional[T]]:
    """
    Обрабатывает список элементов параллельно с ограничением количества одновременных запросов.
    
    Использует Semaphore для ограничения параллелизма и asyncio.gather для параллельного выполнения.
    
    Args:
        items: Список элементов для обработки
        processor: Async функция для обработки одного элемента
        max_concurrent: Максимальное количество одновременных запросов (по умолчанию 5)
        error_handler: Опциональная функция для обработки ошибок (item, exception)
        
    Returns:
        Список результатов обработки (None для элементов, которые не удалось обработать)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: List[Optional[T]] = [None] * len(items)
    
    async def process_with_semaphore(index: int, item: Any) -> None:
        """Обрабатывает один элемент с учетом семафора"""
        async with semaphore:
            try:
                result = await processor(item)
                results[index] = result
            except Exception as e:
                if error_handler:
                    error_handler(item, e)
                else:
                    logger.warning(f"Ошибка при обработке элемента {item}: {e}")
                results[index] = None
    
    # Создаем задачи для всех элементов
    tasks = [
        process_with_semaphore(i, item)
        for i, item in enumerate(items)
    ]
    
    # Выполняем все задачи параллельно
    await asyncio.gather(*tasks, return_exceptions=True)
    
    return results


async def batch_process_with_filter(
    items: List[Any],
    processor: Callable[[Any], Coroutine[Any, Any, Optional[T]]],
    max_concurrent: int = 5,
    error_handler: Optional[Callable[[Any, Exception], None]] = None
) -> List[T]:
    """
    Обрабатывает список элементов параллельно и возвращает только успешно обработанные.
    
    Аналогично batch_process, но фильтрует None результаты.
    
    Args:
        items: Список элементов для обработки
        processor: Async функция для обработки одного элемента (может вернуть None для пропуска)
        max_concurrent: Максимальное количество одновременных запросов
        error_handler: Опциональная функция для обработки ошибок
        
    Returns:
        Список успешно обработанных элементов (без None)
    """
    results = await batch_process(items, processor, max_concurrent, error_handler)
    return [r for r in results if r is not None]
