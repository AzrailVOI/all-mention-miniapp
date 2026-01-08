"""Обработчики команд бота"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.services.chat_storage_service import chat_storage
from bot.config import Config
from bot.constants import ChatType, GROUP_CHAT_TYPES

logger = logging.getLogger(__name__)


def register_chat_safe(chat) -> None:
    """
    Безопасная регистрация чата с обработкой ошибок.
    
    Args:
        chat: Объект Chat для регистрации
    """
    try:
        chat_storage.register_chat(chat)
    except Exception as e:
        logger.error(f"Ошибка при регистрации чата {chat.id}: {e}", exc_info=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    
    Приветствует пользователя и предоставляет информацию о боте,
    включая кнопку для открытия Mini App (если это приватный чат).
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения команды
    """
    chat = update.effective_chat
    
    # Регистрируем чат
    register_chat_safe(chat)
    
    welcome_text = (
        "Привет! Я бот, который тегает всех участников группы по упоминанию @all "
        "(кроме ботов) и пересылает сообщение с указанием автора.\n\n"
        "📋 Доступные триггеры:\n"
        "• @all\n"
        "• @everybody_mention_bot\n"
        "• @everyone\n\n"
        "⚠️ Убедитесь, что я администратор в группе с правами на удаление сообщений."
    )
    
    # Добавляем кнопку для Mini App, если это приватный чат
    reply_markup = None
    if chat.type == "private":
        keyboard = [
            [InlineKeyboardButton(
                "📱 Открыть Mini App",
                web_app={"url": Config.WEBAPP_URL}
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=welcome_text,
        reply_markup=reply_markup
    )


async def chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /chats для открытия Mini App.
    
    Открывает Mini App со списком всех чатов, где добавлен бот.
    Работает только в приватном чате с ботом.
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения команды
    """
    chat = update.effective_chat
    
    # Регистрируем чат
    register_chat_safe(chat)
    
    if chat.type == "private":
        keyboard = [
            [InlineKeyboardButton(
                "📱 Открыть список чатов",
                web_app={"url": Config.WEBAPP_URL}
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=chat.id,
            text="Нажмите кнопку ниже, чтобы открыть Mini App со списком чатов:",
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Команда /chats доступна только в приватном чате с ботом."
        )


async def register_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /register для регистрации текущего чата.
    
    Регистрирует текущий чат в хранилище, чтобы он отображался в Mini App.
    Работает только в группах и супергруппах.
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения команды
    """
    chat = update.effective_chat
    
    # Регистрируем чат
    register_chat_safe(chat)
    
    if chat.type in GROUP_CHAT_TYPES:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Чат '{chat.title or 'Без названия'}' зарегистрирован! Теперь он будет отображаться в Mini App."
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Эта команда работает только в группах и супергруппах."
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /stats для получения статистики по чатам.
    
    Отображает статистику по всем зарегистрированным чатам:
    общее количество, количество групп, супергрупп и т.д.
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения команды
    """
    chat = update.effective_chat
    
    # Регистрируем чат
    register_chat_safe(chat)
    
    # Получаем статистику
    stats = chat_storage.get_stats()
    
    stats_text = (
        "📊 <b>Статистика по чатам:</b>\n\n"
        f"📁 Всего чатов: <b>{stats['total']}</b>\n"
        f"👥 Группы: <b>{stats['groups']}</b>\n"
        f"👥👥 Супергруппы: <b>{stats['supergroups']}</b>\n"
        f"💬 Приватные чаты: <b>{stats['private']}</b>\n"
        f"📢 Каналы: <b>{stats['channels']}</b>"
    )
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=stats_text,
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /help с описанием всех команд.
    
    Отображает справку по всем доступным командам бота и его функциональности.
    В приватном чате также добавляет кнопку для открытия Mini App.
    
    Args:
        update: Объект Update от Telegram Bot API
        context: Контекст выполнения команды
    """
    chat = update.effective_chat
    
    # Регистрируем чат
    register_chat_safe(chat)
    
    help_text = (
        "🤖 <b>All Mention Bot - Справка</b>\n\n"
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/chats - Открыть Mini App со списком чатов (только в приватном чате)\n"
        "/register - Зарегистрировать текущий чат в Mini App (только в группах)\n"
        "/stats - Показать статистику по зарегистрированным чатам\n\n"
        "📝 <b>Использование:</b>\n\n"
        "В группах используйте триггеры для упоминания всех участников:\n"
        "• @all\n"
        "• @everybody_mention_bot\n"
        "• @everyone\n\n"
        "Бот автоматически:\n"
        "✅ Упомянет всех участников (кроме ботов)\n"
        "✅ Покажет автора сообщения\n"
        "✅ Удалит оригинальное сообщение\n\n"
        "⚠️ <b>Требования:</b>\n"
        "• Бот должен быть администратором группы\n"
        "• Бот должен иметь права на удаление сообщений\n\n"
        "📱 <b>Mini App:</b>\n"
        "Используйте команду /chats в приватном чате для просмотра всех чатов, "
        "где добавлен бот."
    )
    
    # Добавляем кнопку для Mini App, если это приватный чат
    reply_markup = None
    if chat.type == ChatType.PRIVATE.value:
        keyboard = [
            [InlineKeyboardButton(
                "📱 Открыть Mini App",
                web_app={"url": Config.WEBAPP_URL}
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=help_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

