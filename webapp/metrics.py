"""
Метрики Prometheus для мониторинга производительности приложения
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
import time
from functools import wraps
from typing import Callable, Any

# Метрики для HTTP запросов
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Метрики для Telegram API
telegram_api_requests_total = Counter(
    'telegram_api_requests_total',
    'Total number of Telegram API requests',
    ['method', 'status']
)

telegram_api_request_duration_seconds = Histogram(
    'telegram_api_request_duration_seconds',
    'Telegram API request duration in seconds',
    ['method']
)

# Метрики для кэша
cache_operations_total = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['operation', 'status']  # operation: get, set, delete; status: hit, miss, error
)

cache_size = Gauge(
    'cache_size',
    'Current cache size (number of entries)',
    ['cache_type']  # cache_type: chats, members
)

# Метрики для ошибок
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']  # error_type: telegram_error, validation_error, etc.
)

# Метрики для активных запросов
active_requests = Gauge(
    'active_requests',
    'Number of currently active requests',
    ['endpoint']
)


def track_request_metrics(func: Callable) -> Callable:
    """
    Декоратор для отслеживания метрик HTTP запросов.
    
    Args:
        func: Функция Flask endpoint
        
    Returns:
        Обернутая функция с метриками
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from flask import request
        
        method = request.method
        endpoint = request.endpoint or 'unknown'
        
        # Увеличиваем счетчик активных запросов
        active_requests.labels(endpoint=endpoint).inc()
        
        start_time = time.time()
        status = '200'  # По умолчанию
        
        try:
            response = func(*args, **kwargs)
            
            # Определяем статус из ответа
            if hasattr(response, 'status_code'):
                status = str(response.status_code)
            elif isinstance(response, tuple) and len(response) > 1:
                status = str(response[1])
            
            return response
        except Exception as e:
            status = '500'
            errors_total.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise
        finally:
            # Уменьшаем счетчик активных запросов
            active_requests.labels(endpoint=endpoint).dec()
            
            # Записываем метрики
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
    
    return wrapper


def track_telegram_api_call(method_name: str):
    """
    Декоратор для отслеживания метрик вызовов Telegram API.
    
    Args:
        method_name: Имя метода Telegram API
        
    Returns:
        Декоратор для функции
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                errors_total.labels(
                    error_type='telegram_api_error',
                    endpoint=method_name
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                telegram_api_request_duration_seconds.labels(
                    method=method_name
                ).observe(duration)
                
                telegram_api_requests_total.labels(
                    method=method_name,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


def track_cache_operation(operation: str, cache_type: str):
    """
    Отслеживает операцию с кэшем.
    
    Args:
        operation: Тип операции ('get', 'set', 'delete')
        cache_type: Тип кэша ('chats', 'members')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                
                # Для операций get определяем hit/miss
                if operation == 'get':
                    if result is None:
                        status = 'miss'
                    else:
                        status = 'hit'
                
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                cache_operations_total.labels(
                    operation=operation,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


def get_metrics() -> Response:
    """
    Возвращает метрики Prometheus в формате text/plain.
    
    Returns:
        Flask Response с метриками
    """
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )
