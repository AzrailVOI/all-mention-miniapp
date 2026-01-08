"""Главный файл запуска бота"""
import logging
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from bot.config import Config
from bot.handlers.commands import start_command, chats_command, register_chat_command
from bot.handlers.messages import handle_text_message
from bot.handlers.chat_events import handle_chat_member_update, handle_my_chat_member_update

# Настройка логирования
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
    
    # Компилируем SCSS перед запуском
    try:
        from webapp.utils.scss_compiler import compile_scss
        logger.info("Компиляция SCSS...")
        if compile_scss(output_style='expanded'):
            logger.info("SCSS успешно скомпилирован")
        else:
            logger.warning("SCSS не был скомпилирован (возможно, файлы не найдены)")
    except ImportError as e:
        logger.warning(f"libsass не установлен, пропускаем компиляцию SCSS: {e}")
    except Exception as e:
        logger.warning(f"Ошибка при компиляции SCSS: {e}")
    
    # Запускаем веб-сервер в отдельном потоке
    webapp_thread = threading.Thread(target=run_webapp, daemon=True)
    webapp_thread.start()
    logger.info("Веб-сервер запущен в фоновом режиме")
    
    # Создаем приложение
    application = Application.builder().token(Config.TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("chats", chats_command))
    application.add_handler(CommandHandler("register", register_chat_command))
    
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

