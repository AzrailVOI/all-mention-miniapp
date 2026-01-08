"""Главный файл запуска бота"""
import logging
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from bot.config import Config
from bot.handlers.commands import (
    start_command,
    chats_command,
    register_chat_command,
    stats_command,
    help_command
)
from bot.handlers.messages import handle_text_message
from bot.handlers.chat_events import handle_chat_member_update, handle_my_chat_member_update

# Настройка логирования
if Config.LOG_JSON:
    import json
    import sys
    from datetime import datetime
    
    class JSONFormatter(logging.Formatter):
        """JSON форматтер для структурированного логирования"""
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Добавляем исключение, если есть
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            
            # Добавляем дополнительные поля из extra
            if hasattr(record, 'extra'):
                log_entry.update(record.extra)
            
            return json.dumps(log_entry, ensure_ascii=False)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        handlers=[handler]
    )
else:
    logging.basicConfig(
        format=Config.LOG_FORMAT,
        level=getattr(logging, Config.LOG_LEVEL.upper())
    )

logger = logging.getLogger(__name__)


def run_webapp():
    """Запуск веб-приложения в отдельном потоке"""
    try:
        from webapp.app import run_webapp
        logger.info(f"Запуск веб-сервера на {Config.WEBAPP_HOST}:{Config.WEBAPP_PORT}")
        run_webapp()
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-сервера: {e}")


def main() -> None:
    """Запуск бота"""
    # Проверяем конфигурацию
    try:
        Config.validate()
    except ValueError as e:
        logger.error(e)
        return
    
    # Запускаем веб-сервер в отдельном потоке
    webapp_thread = threading.Thread(target=run_webapp, daemon=True)
    webapp_thread.start()
    logger.info("Веб-сервер запущен в фоновом режиме")
    
    # Создаем приложение
    application = Application.builder().token(Config.TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chats", chats_command))
    application.add_handler(CommandHandler("register", register_chat_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчик всех сообщений для регистрации чатов и обработки упоминаний
    # handle_text_message уже регистрирует чат для всех сообщений и обрабатывает упоминания для текстовых
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, handle_text_message)
    )
    
    # Обработчики событий чата
    from telegram.ext import ChatMemberHandler
    application.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(ChatMemberHandler(handle_my_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе...")
    logger.info(f"Mini App доступен по адресу: {Config.WEBAPP_URL}")
    application.run_polling(
        allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"]
    )


if __name__ == "__main__":
    main()

