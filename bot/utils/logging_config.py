"""
Настройка структурированного логирования
"""
import logging
import json
import os
from typing import Any, Dict
from logging import LogRecord

from bot.config import Config
from bot.utils.correlation import CorrelationIDFilter


class JSONFormatter(logging.Formatter):
    """
    Форматтер для структурированного JSON логирования.
    
    Используется в продакшене для удобного парсинга логов системами мониторинга.
    """
    
    def format(self, record: LogRecord) -> str:
        """
        Форматирует запись лога в JSON формат.
        
        Args:
            record: Запись лога
            
        Returns:
            JSON строка с данными лога
        """
        log_data: Dict[str, Any] = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Добавляем correlation ID, если есть
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        # Добавляем информацию об исключении, если есть
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Добавляем дополнительные поля из extra
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """
    Форматтер для структурированного логирования с читаемым форматом.
    
    Используется в разработке для удобного чтения логов.
    """
    
    def format(self, record: LogRecord) -> str:
        """
        Форматирует запись лога в структурированный формат.
        
        Args:
            record: Запись лога
            
        Returns:
            Отформатированная строка лога
        """
        correlation_id = getattr(record, 'correlation_id', 'no-correlation-id')
        correlation_short = correlation_id[:8] if correlation_id != 'no-correlation-id' else 'no-corr'
        
        base_message = (
            f"{self.formatTime(record, self.datefmt)} - "
            f"{record.name} - "
            f"{record.levelname} - "
            f"[{correlation_short}] - "
            f"{record.getMessage()}"
        )
        
        # Добавляем информацию об исключении, если есть
        if record.exc_info:
            base_message += f"\n{self.formatException(record.exc_info)}"
        
        return base_message


def setup_logging(use_json: bool = False) -> None:
    """
    Настраивает логирование для приложения.
    
    Args:
        use_json: Если True, использует JSON форматтер (для продакшена).
                 Если False, использует структурированный текстовый форматтер (для разработки).
    """
    # Определяем форматтер
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter(
            fmt=Config.LOG_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # Удаляем существующие обработчики
    root_logger.handlers.clear()
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    console_handler.setFormatter(formatter)
    
    # Добавляем фильтр для correlation ID
    if not any(isinstance(f, CorrelationIDFilter) for f in root_logger.filters):
        root_logger.addFilter(CorrelationIDFilter())
    
    root_logger.addHandler(console_handler)
    
    # Настраиваем логирование для внешних библиотек
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Получает настроенный logger с автоматическим добавлением correlation ID.
    
    Args:
        name: Имя logger'а
        
    Returns:
        Настроенный logger
    """
    logger = logging.getLogger(name)
    
    # Добавляем фильтр для correlation ID, если его еще нет
    if not any(isinstance(f, CorrelationIDFilter) for f in logger.filters):
        logger.addFilter(CorrelationIDFilter())
    
    return logger
