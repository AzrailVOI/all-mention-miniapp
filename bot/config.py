"""Конфигурация бота"""
import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации бота"""
    
    # Токен бота из переменных окружения
    TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Секретный ключ для валидации Telegram WebApp
    # ДОЛЖЕН быть отдельным от токена бота
    WEBAPP_SECRET_KEY: str = os.getenv("WEBAPP_SECRET_KEY", "")
    
    # Импортируем константы из модуля constants
    from bot.constants import MENTION_TRIGGERS, MAX_MESSAGE_LENGTH
    
    # Триггеры для упоминания всех (из constants)
    MENTION_TRIGGERS: list[str] = MENTION_TRIGGERS
    
    # Максимальная длина сообщения Telegram (из constants)
    MAX_MESSAGE_LENGTH: int = MAX_MESSAGE_LENGTH
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_JSON: bool = os.getenv("LOG_JSON", "false").lower() == "true"  # JSON формат для продакшена
    
    # Настройки веб-приложения
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:5000")
    WEBAPP_HOST: str = os.getenv("WEBAPP_HOST", "0.0.0.0")
    WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "5000"))
    
    # Максимальное время жизни данных WebApp (в секундах)
    WEBAPP_DATA_MAX_AGE: int = int(os.getenv("WEBAPP_DATA_MAX_AGE", "86400"))  # 24 часа
    
    @classmethod
    def validate(cls) -> None:
        """
        Проверяет корректность конфигурации.
        Валидирует все обязательные переменные окружения.
        """
        errors = []
        
        # Проверка обязательных переменных
        if not cls.TOKEN:
            errors.append("BOT_TOKEN не установлен! Установите переменную окружения BOT_TOKEN или создайте .env файл.")
        
        # Проверка числовых значений
        try:
            if cls.WEBAPP_PORT <= 0 or cls.WEBAPP_PORT > 65535:
                errors.append(f"WEBAPP_PORT должен быть в диапазоне 1-65535, получено: {cls.WEBAPP_PORT}")
        except (ValueError, TypeError):
            errors.append(f"WEBAPP_PORT должен быть числом, получено: {os.getenv('WEBAPP_PORT', '5000')}")
        
        try:
            if cls.WEBAPP_DATA_MAX_AGE <= 0:
                errors.append(f"WEBAPP_DATA_MAX_AGE должен быть положительным числом, получено: {cls.WEBAPP_DATA_MAX_AGE}")
        except (ValueError, TypeError):
            errors.append(f"WEBAPP_DATA_MAX_AGE должен быть числом, получено: {os.getenv('WEBAPP_DATA_MAX_AGE', '86400')}")
        
        # Проверка URL
        if cls.WEBAPP_URL and not (cls.WEBAPP_URL.startswith('http://') or cls.WEBAPP_URL.startswith('https://')):
            errors.append(f"WEBAPP_URL должен начинаться с http:// или https://, получено: {cls.WEBAPP_URL}")
        
        # WEBAPP_SECRET_KEY обязателен и должен отличаться от BOT_TOKEN
        if not cls.WEBAPP_SECRET_KEY:
            errors.append(
                "WEBAPP_SECRET_KEY не установлен! "
                "Создайте в .env отдельный случайный ключ WEBAPP_SECRET_KEY, "
                "отличный от BOT_TOKEN."
            )
        elif cls.WEBAPP_SECRET_KEY == cls.TOKEN:
            errors.append(
                "WEBAPP_SECRET_KEY не должен совпадать с BOT_TOKEN. "
                "Создайте отдельный секретный ключ для WebApp."
            )
        
        # Проверка уровня логирования
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL должен быть одним из: {', '.join(valid_log_levels)}, получено: {cls.LOG_LEVEL}")
        
        if errors:
            error_message = "Ошибки конфигурации:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_message)

