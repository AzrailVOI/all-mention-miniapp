"""Утилиты для работы с async функциями в синхронном контексте Flask"""
import asyncio
import logging
from typing import TypeVar, Callable, Coroutine, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def run_async_safe(coro: Coroutine[Any, Any, T]) -> T:
    """
    Безопасно выполняет async функцию в синхронном контексте Flask.
    
    Использует правильный подход для работы с event loop:
    - Если loop уже запущен, использует asyncio.run_coroutine_threadsafe
    - Если loop не запущен, создает новый и выполняет через asyncio.run
    
    Args:
        coro: Coroutine для выполнения
        
    Returns:
        Результат выполнения coroutine
        
    Raises:
        Exception: Любое исключение, возникшее при выполнении coroutine
    """
    try:
        # Пытаемся получить текущий event loop
        loop = asyncio.get_running_loop()
        # Если loop уже запущен (в async контексте), это вызовет RuntimeError
        # и мы перейдем к созданию нового loop
    except RuntimeError:
        # Нет запущенного loop - можем создать новый
        try:
            # Пытаемся получить существующий loop (может быть создан, но не запущен)
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # Loop закрыт, создаем новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # Нет loop вообще, создаем новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Выполняем coroutine в loop
        try:
            return loop.run_until_complete(coro)
        finally:
            # НЕ закрываем loop, так как он может использоваться повторно
            # Flask может переиспользовать поток и loop
            pass
    
    # Если loop уже запущен (async контекст), используем другой подход
    # В Flask это редко, но на всякий случай
    import concurrent.futures
    import threading
    
    # Создаем новый loop в отдельном потоке
    future = concurrent.futures.Future()
    
    def run_in_thread():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result = new_loop.run_until_complete(coro)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            new_loop.close()
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    thread.join(timeout=30)  # Максимум 30 секунд на выполнение
    
    if thread.is_alive():
        raise TimeoutError("Async operation timed out")
    
    return future.result()


def async_to_sync(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    Декоратор для преобразования async функции в синхронную.
    
    Используется для Flask endpoints, которые должны вызывать async функции.
    
    Usage:
        @app.route('/api/endpoint')
        @async_to_sync
        async def my_endpoint():
            result = await some_async_function()
            return jsonify(result)
    
    Args:
        func: Async функция для преобразования
        
    Returns:
        Синхронная обертка над async функцией
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return run_async_safe(coro)
    
    return wrapper
