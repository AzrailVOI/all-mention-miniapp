"""Обработчики команд бота"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.services.chat_storage_service import chat_storage
from bot.config import Config

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    chat = update.effective_chat
    
    # Регистрируем чат
    chat_storage.register_chat(chat)
    
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
    """Обработчик команды /chats для открытия Mini App"""
    chat = update.effective_chat
    
    # Регистрируем чат
    chat_storage.register_chat(chat)
    
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
    """Обработчик команды /register для регистрации текущего чата"""
    chat = update.effective_chat
    
    # Регистрируем чат
    chat_storage.register_chat(chat)
    
    if chat.type in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Чат '{chat.title or 'Без названия'}' зарегистрирован! Теперь он будет отображаться в Mini App."
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Эта команда работает только в группах и супергруппах."
        )

