"""
Утилиты для работы с correlation ID (идентификаторами корреляции запросов)
"""
import uuid
import logging
from contextvars import ContextVar
from typing import Optional

# Context variable для хранения correlation ID в текущем контексте выполнения
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """
    Генерирует новый correlation ID.
    
    Returns:
        UUID строка в формате hex (32 символа).
    """
    return uuid.uuid4().hex


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Устанавливает correlation ID в текущий контекст.
    
    Args:
        correlation_id: ID корреляции. Если не указан, генерируется новый.
        
    Returns:
        Установленный correlation ID.
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Получает correlation ID из текущего контекста.
    
    Returns:
        Correlation ID или None, если не установлен.
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """
    Очищает correlation ID из текущего контекста.
    """
    correlation_id_var.set(None)


class CorrelationIDFilter(logging.Filter):
    """
    Фильтр для логирования, который добавляет correlation ID к каждой записи лога.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Добавляет correlation_id к записи лога.
        
        Args:
            record: Запись лога.
            
        Returns:
            True (всегда пропускает запись).
        """
        correlation_id = get_correlation_id()
        record.correlation_id = correlation_id or 'no-correlation-id'
        return True


def get_logger_with_context(name: str) -> logging.Logger:
    """
    Создает logger с автоматическим добавлением correlation ID.
    
    Args:
        name: Имя logger'а.
        
    Returns:
        Настроенный logger.
    """
    logger_instance = logging.getLogger(name)
    
    # Добавляем фильтр, если его еще нет
    if not any(isinstance(f, CorrelationIDFilter) for f in logger_instance.filters):
        logger_instance.addFilter(CorrelationIDFilter())
    
    return logger_instance


def log_with_context(logger_instance: logging.Logger, level: int, message: str, *args, **kwargs) -> None:
    """
    Логирует сообщение с автоматическим добавлением correlation ID.
    
    Args:
        logger_instance: Экземпляр logger'а.
        level: Уровень логирования (logging.INFO, logging.ERROR, и т.д.).
        message: Сообщение для логирования.
        *args: Дополнительные позиционные аргументы.
        **kwargs: Дополнительные именованные аргументы.
    """
    correlation_id = get_correlation_id()
    if correlation_id:
        message = f"[{correlation_id[:8]}] {message}"
    
    logger_instance.log(level, message, *args, **kwargs)
