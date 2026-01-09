"""Обработчики команд бота"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.handlers import (
    register_chat_on_call,
    create_mini_app_keyboard,
    is_private_chat,
    is_group_chat
)

logger = logging.getLogger(__name__)


@register_chat_on_call
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    chat = update.effective_chat
    
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
    if is_private_chat(chat):
        reply_markup = create_mini_app_keyboard("📱 Открыть Mini App")
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=welcome_text,
        reply_markup=reply_markup
    )


@register_chat_on_call
async def chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /chats для открытия Mini App"""
    chat = update.effective_chat
    
    if is_private_chat(chat):
        reply_markup = create_mini_app_keyboard("📱 Открыть список чатов")
        
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


@register_chat_on_call
async def register_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /register для регистрации текущего чата"""
    chat = update.effective_chat
    
    if is_group_chat(chat):
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Чат '{chat.title or 'Без названия'}' зарегистрирован! Теперь он будет отображаться в Mini App."
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Эта команда работает только в группах и супергруппах."
        )


@register_chat_on_call
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /stats для получения статистики по чатам"""
    chat = update.effective_chat
    
    # Получаем статистику
    from bot.services.chat_storage_service import chat_storage
    stats = chat_storage.get_stats()
    
    stats_text = (
        "📊 <b>Статистика по чатам:</b>\n\n"
        f"📈 Всего чатов: <b>{stats['total']}</b>\n"
        f"👥 Группы: <b>{stats['groups']}</b>\n"
        f"💬 Супергруппы: <b>{stats['supergroups']}</b>\n"
        f"🔒 Приватные чаты: <b>{stats['private']}</b>\n"
        f"📢 Каналы: <b>{stats['channels']}</b>"
    )
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=stats_text,
        parse_mode="HTML"
    )


@register_chat_on_call
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help с описанием всех команд"""
    chat = update.effective_chat
    
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "• <b>/start</b> - Начать работу с ботом\n"
        "• <b>/chats</b> - Открыть Mini App со списком чатов (только в приватном чате)\n"
        "• <b>/register</b> - Зарегистрировать текущий чат в Mini App (только в группах)\n"
        "• <b>/stats</b> - Показать статистику по чатам\n"
        "• <b>/help</b> - Показать эту справку\n\n"
        "📋 <b>Триггеры для упоминания всех:</b>\n"
        "• @all\n"
        "• @everybody_mention_bot\n"
        "• @everyone\n\n"
        "⚠️ <b>Важно:</b> Бот должен быть администратором в группе с правами на удаление сообщений."
    )
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=help_text,
        parse_mode="HTML"
    )
