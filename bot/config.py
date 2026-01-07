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
    
    # Триггеры для упоминания всех
    MENTION_TRIGGERS: list[str] = ["@all", "@everybody_mention_bot", "@everyone"]
    
    # Максимальная длина сообщения Telegram
    MAX_MESSAGE_LENGTH: int = 4096
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Настройки веб-приложения
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:5000")
    WEBAPP_HOST: str = os.getenv("WEBAPP_HOST", "0.0.0.0")
    WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "5000"))
    
    @classmethod
    def validate(cls) -> None:
        """Проверяет корректность конфигурации"""
        if not cls.TOKEN:
            raise ValueError(
                "BOT_TOKEN не установлен! "
                "Установите переменную окружения BOT_TOKEN или создайте .env файл."
            )

