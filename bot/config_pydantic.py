"""
Конфигурация бота с использованием Pydantic для валидации
"""
import os
from typing import Optional, List
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Валидные уровни логирования
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Config(BaseSettings):
    """
    Класс конфигурации бота с валидацией через Pydantic.
    
    Все переменные окружения автоматически загружаются и валидируются.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Игнорируем дополнительные переменные
    )
    
    # Токен бота (обязательный)
    BOT_TOKEN: str = Field(
        ...,
        min_length=10,
        description="Токен Telegram бота"
    )
    
    # Триггеры для упоминания всех
    MENTION_TRIGGERS: List[str] = Field(
        default=["@all", "@everybody_mention_bot", "@everyone"],
        min_length=1,
        description="Список триггеров для упоминания всех участников"
    )
    
    # Максимальная длина сообщения Telegram
    MAX_MESSAGE_LENGTH: int = Field(
        default=4096,
        ge=1,
        le=4096,
        description="Максимальная длина сообщения Telegram"
    )
    
    # Настройки логирования
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Уровень логирования"
    )
    
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s",
        description="Формат логов"
    )
    
    # Настройки веб-приложения
    WEBAPP_URL: str = Field(
        ...,
        description="Базовый URL для Mini App"
    )
    
    WEBAPP_HOST: str = Field(
        default="0.0.0.0",
        description="Хост для запуска Flask приложения"
    )
    
    WEBAPP_PORT: int = Field(
        default=5000,
        ge=1,
        le=65535,
        description="Порт для запуска Flask приложения"
    )
    
    # Секретный ключ для валидации Telegram WebApp данных
    WEBAPP_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Секретный ключ для валидации WebApp данных (опционально)"
    )
    
    # Секретный ключ для Flask сессий
    FLASK_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Секретный ключ для Flask сессий (опционально)"
    )
    
    # Настройки окружения
    FLASK_ENV: str = Field(
        default="production",
        description="Окружение Flask (development/production)"
    )
    
    COMPILE_SCSS: bool = Field(
        default=True,
        description="Включить/отключить компиляцию SCSS при старте"
    )
    
    USE_JSON_LOGGING: bool = Field(
        default=False,
        description="Использовать JSON формат для логов (для продакшена)"
    )
    
    @field_validator('BOT_TOKEN')
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Валидирует токен бота"""
        if not v or not v.strip():
            raise ValueError("BOT_TOKEN не может быть пустым")
        if len(v) < 10:
            raise ValueError("BOT_TOKEN слишком короткий (минимальная длина: 10 символов)")
        return v.strip()
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидирует уровень логирования"""
        v_upper = v.upper()
        if v_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"LOG_LEVEL имеет неверное значение: '{v}'. "
                f"Допустимые значения: {', '.join(VALID_LOG_LEVELS)}"
            )
        return v_upper
    
    @field_validator('WEBAPP_URL')
    @classmethod
    def validate_webapp_url(cls, v: str) -> str:
        """Валидирует URL веб-приложения"""
        if not v:
            raise ValueError("WEBAPP_URL не может быть пустым")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(
                f"WEBAPP_URL должен начинаться с http:// или https://, получено: '{v}'"
            )
        return v
    
    @field_validator('WEBAPP_HOST')
    @classmethod
    def validate_webapp_host(cls, v: str) -> str:
        """Валидирует хост веб-приложения"""
        if not v or not v.strip():
            raise ValueError("WEBAPP_HOST не может быть пустым")
        return v.strip()
    
    @field_validator('MENTION_TRIGGERS')
    @classmethod
    def validate_mention_triggers(cls, v: List[str]) -> List[str]:
        """Валидирует список триггеров упоминания"""
        if not v:
            raise ValueError("MENTION_TRIGGERS не может быть пустым списком")
        return v
    
    @computed_field
    @property
    def TOKEN(self) -> str:
        """Алиас для BOT_TOKEN для обратной совместимости"""
        return self.BOT_TOKEN
    
    def get_webapp_secret_key(self) -> bytes:
        """
        Получает секретный ключ для валидации WebApp данных.
        Если WEBAPP_SECRET_KEY не установлен, генерирует из токена бота.
        
        Returns:
            Секретный ключ в виде bytes
        """
        if self.WEBAPP_SECRET_KEY:
            return self.WEBAPP_SECRET_KEY.encode('utf-8')
        
        # Генерируем секретный ключ из токена бота
        # Telegram использует HMAC-SHA256 от строки "WebAppData" с токеном как ключом
        import hmac
        import hashlib
        secret_key = hmac.new(
            self.BOT_TOKEN.encode('utf-8'),
            "WebAppData".encode('utf-8'),
            hashlib.sha256
        ).digest()
        return secret_key
    
    @classmethod
    def get_required_variables(cls) -> dict:
        """
        Возвращает словарь обязательных переменных окружения.
        
        Returns:
            Словарь {имя_переменной: (тип, описание)}
        """
        return {
            "BOT_TOKEN": (str, "Токен Telegram бота"),
            "WEBAPP_URL": (str, "Базовый URL для Mini App"),
            "WEBAPP_HOST": (str, "Хост для запуска Flask приложения"),
            "WEBAPP_PORT": (int, "Порт для запуска Flask приложения"),
        }
    
    @classmethod
    def get_optional_variables(cls) -> dict:
        """
        Возвращает словарь опциональных переменных окружения.
        
        Returns:
            Словарь {имя_переменной: (тип, описание)}
        """
        return {
            "LOG_LEVEL": (str, "Уровень логирования (INFO, DEBUG, WARNING, ERROR)"),
            "WEBAPP_SECRET_KEY": (str, "Секретный ключ для валидации WebApp данных"),
            "FLASK_SECRET_KEY": (str, "Секретный ключ для Flask сессий"),
            "COMPILE_SCSS": (str, "Включить/отключить компиляцию SCSS при старте (true/false)"),
        }


# Глобальный экземпляр конфигурации
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Получает глобальный экземпляр конфигурации.
    
    Returns:
        Экземпляр Config
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
