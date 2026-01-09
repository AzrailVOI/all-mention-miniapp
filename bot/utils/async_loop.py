"""Утилиты для безопасного выполнения async функций из sync кода"""
import asyncio
import logging
from typing import Any, Coroutine

logger = logging.getLogger(__name__)


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Безопасно выполняет async функцию из sync кода.
    
    Использует asyncio.run() для создания нового event loop, что является
    рекомендуемым способом в Python 3.7+.
    
    Args:
        coro: Coroutine для выполнения
        
    Returns:
        Результат выполнения coroutine
        
    Raises:
        Exception: Любое исключение, возникшее при выполнении coroutine
    """
    try:
        # asyncio.run() создает новый event loop, выполняет coroutine и закрывает loop
        # Это безопасный способ для выполнения async кода из sync контекста
        return asyncio.run(coro)
    except RuntimeError as e:
        # Если уже есть запущенный event loop (например, в Jupyter или некоторых фреймворках),
        # используем альтернативный подход
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            logger.warning("Обнаружен запущенный event loop, используем альтернативный метод")
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Если loop уже запущен, создаем новый в отдельном потоке
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, coro)
                        return future.result()
                else:
                    return loop.run_until_complete(coro)
            except RuntimeError:
                # Если нет event loop, создаем новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()
        else:
            raise
    except Exception as e:
        logger.error(f"Ошибка при выполнении async функции: {e}", exc_info=True)
        raise
