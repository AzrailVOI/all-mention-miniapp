"""Кэширование данных с TTL"""
import time
import logging
from typing import Dict, Optional, Any, Callable
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Запись в кэше с временем истечения"""
    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.time() + ttl
        self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Проверяет, истекла ли запись"""
        return time.time() > self.expires_at


class SimpleCache:
    """Простое in-memory кэширование с TTL"""
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получает значение из кэша.
        
        Args:
            key: Ключ кэша
            
        Returns:
            Значение или None, если не найдено или истекло
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                logger.debug(f"Кэш запись {key} истекла и удалена")
                return None
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: float = 300.0) -> None:
        """
        Сохраняет значение в кэш.
        
        Args:
            key: Ключ кэша
            value: Значение для кэширования
            ttl: Время жизни в секундах (по умолчанию 5 минут)
        """
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Значение сохранено в кэш: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> None:
        """Удаляет запись из кэша"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Запись удалена из кэша: {key}")
    
    def clear(self) -> None:
        """Очищает весь кэш"""
        with self._lock:
            self._cache.clear()
            logger.info("Кэш полностью очищен")
    
    def invalidate_pattern(self, pattern: str) -> None:
        """
        Инвалидирует все ключи, начинающиеся с pattern.
        
        Args:
            pattern: Префикс ключей для удаления
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            if keys_to_delete:
                logger.debug(f"Инвалидировано {len(keys_to_delete)} записей с паттерном: {pattern}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for entry in self._cache.values() if entry.is_expired())
            return {
                'total_entries': total,
                'expired_entries': expired,
                'active_entries': total - expired
            }


# Глобальный экземпляр кэша
_cache_instance: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """Получает глобальный экземпляр кэша"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache()
    return _cache_instance


def cached(ttl: float = 300.0, key_func: Optional[Callable] = None):
    """
    Декоратор для кэширования результатов функций.
    
    Args:
        ttl: Время жизни кэша в секундах
        key_func: Функция для генерации ключа кэша (по умолчанию используется имя функции + args)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Простой ключ на основе аргументов
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Проверяем кэш
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Кэш попадание для {cache_key}")
                return cached_value
            
            # Выполняем функцию
            logger.debug(f"Кэш промах для {cache_key}, выполняем функцию")
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Генерируем ключ кэша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Проверяем кэш
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Кэш попадание для {cache_key}")
                return cached_value
            
            # Выполняем функцию
            logger.debug(f"Кэш промах для {cache_key}, выполняем функцию")
            result = func(*args, **kwargs)
            
            # Сохраняем в кэш
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Определяем, async или sync функция
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
