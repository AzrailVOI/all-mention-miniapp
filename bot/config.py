"""Конфигурация бота"""
import os
import logging
from typing import Optional, List
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Валидные уровни логирования
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


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
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
    
    # Настройки веб-приложения
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:5000")
    WEBAPP_HOST: str = os.getenv("WEBAPP_HOST", "0.0.0.0")
    WEBAPP_PORT: int = int(os.getenv("WEBAPP_PORT", "5000"))
    
    # Секретный ключ для валидации Telegram WebApp данных
    # Если не указан, будет сгенерирован из токена бота
    WEBAPP_SECRET_KEY: Optional[str] = os.getenv("WEBAPP_SECRET_KEY", None)
    
    @classmethod
    def validate(cls) -> None:
        """
        Проверяет корректность конфигурации.
        Валидирует все обязательные переменные и их значения.
        
        Raises:
            ValueError: Если какая-либо обязательная переменная не установлена или имеет неверное значение
        """
        errors: List[str] = []
        
        # Проверка обязательных переменных
        if not cls.TOKEN:
            errors.append(
                "BOT_TOKEN не установлен! "
                "Установите переменную окружения BOT_TOKEN или создайте .env файл."
            )
        elif not cls.TOKEN.strip():
            errors.append("BOT_TOKEN не может быть пустой строкой")
        elif len(cls.TOKEN) < 10:
            errors.append("BOT_TOKEN слишком короткий (минимальная длина: 10 символов)")
        
        # Валидация LOG_LEVEL
        if cls.LOG_LEVEL.upper() not in VALID_LOG_LEVELS:
            errors.append(
                f"LOG_LEVEL имеет неверное значение: '{cls.LOG_LEVEL}'. "
                f"Допустимые значения: {', '.join(VALID_LOG_LEVELS)}"
            )
        
        # Валидация WEBAPP_PORT
        try:
            port = int(os.getenv("WEBAPP_PORT", "5000"))
            if port < 1 or port > 65535:
                errors.append(
                    f"WEBAPP_PORT имеет неверное значение: {port}. "
                    "Допустимый диапазон: 1-65535"
                )
        except ValueError:
            errors.append(
                f"WEBAPP_PORT должен быть числом, получено: '{os.getenv('WEBAPP_PORT', '5000')}'"
            )
        
        # Валидация WEBAPP_URL
        if cls.WEBAPP_URL:
            if not (cls.WEBAPP_URL.startswith("http://") or cls.WEBAPP_URL.startswith("https://")):
                errors.append(
                    f"WEBAPP_URL должен начинаться с http:// или https://, получено: '{cls.WEBAPP_URL}'"
                )
        else:
            errors.append("WEBAPP_URL не может быть пустым")
        
        # Валидация WEBAPP_HOST
        if not cls.WEBAPP_HOST:
            errors.append("WEBAPP_HOST не может быть пустым")
        
        # Валидация MENTION_TRIGGERS
        if not cls.MENTION_TRIGGERS:
            errors.append("MENTION_TRIGGERS не может быть пустым списком")
        
        # Если есть ошибки, выбрасываем исключение с полным списком
        if errors:
            error_message = "Ошибки конфигурации:\n" + "\n".join(f"  - {error}" for error in errors)
            error_message += "\n\nПроверьте файл .env или переменные окружения."
            raise ValueError(error_message)
        
        # Логируем успешную валидацию (если логирование уже настроено)
        try:
            logger = logging.getLogger(__name__)
            logger.debug("Конфигурация успешно валидирована")
        except:
            pass  # Игнорируем, если логирование еще не настроено
    
    @classmethod
    def get_required_variables(cls) -> List[str]:
        """
        Возвращает список всех обязательных переменных окружения.
        
        Returns:
            Список имен обязательных переменных
        """
        return [
            "BOT_TOKEN",
            "WEBAPP_URL",
            "WEBAPP_HOST",
            "WEBAPP_PORT",
            "LOG_LEVEL"
        ]
    
    @classmethod
    def get_optional_variables(cls) -> List[str]:
        """
        Возвращает список опциональных переменных окружения.
        
        Returns:
            Список имен опциональных переменных
        """
        return [
            "WEBAPP_SECRET_KEY",
            "FLASK_SECRET_KEY",
            "FLASK_ENV",
            "COMPILE_SCSS"
        ]
    
    @classmethod
    def get_webapp_secret_key(cls) -> bytes:
        """
        Получает секретный ключ для валидации WebApp данных.
        Если WEBAPP_SECRET_KEY не установлен, генерирует из токена бота.
        """
        if cls.WEBAPP_SECRET_KEY:
            return cls.WEBAPP_SECRET_KEY.encode('utf-8')
        
        # Генерируем секретный ключ из токена бота
        # Telegram использует HMAC-SHA256 от строки "WebAppData" с токеном как ключом
        import hmac
        import hashlib
        secret_key = hmac.new(
            cls.TOKEN.encode('utf-8'),
            "WebAppData".encode('utf-8'),
            hashlib.sha256
        ).digest()
        return secret_key

