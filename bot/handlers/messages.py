"""Обработчики текстовых сообщений"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from bot.models.message import MentionMessage
from bot.services.chat_service import ChatService
from bot.services.mention_service import MentionService
from bot.services.chat_storage_service import chat_storage
from bot.config import Config

logger = logging.getLogger(__name__)


class MessageHandler:
    """Обработчик текстовых сообщений"""
    
    def __init__(self):
        self.config = Config
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает входящие текстовые сообщения"""
        if not update.message or not update.message.text:
            return
        
        message_text = update.message.text
        chat = update.message.chat
        chat_id = update.message.chat_id
        
        # Регистрируем чат в хранилище
        chat_storage.register_chat(chat)
        
        # Проверяем наличие триггера упоминания
        mention_service = MentionService(context.bot)
        if not mention_service.has_mention_trigger(message_text):
            return
        
        # Проверяем, что это группа или супергруппа
        if chat.type not in ["group", "supergroup"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Эта команда работает только в группах."
            )
            return
        
        # Проверяем права администратора
        chat_service = ChatService(context.bot)
        if not await chat_service.is_bot_admin(chat_id):
            await context.bot.send_message(
                chat_id=chat_id,
                text="Я должен быть администратором, чтобы тегать участников!"
            )
            return
        
        # Создаем модель сообщения
        mention_message = MentionMessage(
            author=update.message.from_user,
            original_text=message_text,
            cleaned_text=mention_service.extract_cleaned_text(message_text),
            chat_id=chat_id,
            message_id=update.message.message_id
        )
        
        # Обрабатываем упоминание
        try:
            await self._process_mention(
                update, 
                context, 
                mention_message, 
                chat_service, 
                mention_service
            )
        except TelegramError as e:
            logger.error(f"Ошибка Telegram API: {e}")
            await self._send_error_message(
                context, 
                chat_id, 
                mention_message, 
                f"Произошла ошибка: {e.message}. Убедитесь, что у меня есть права администратора."
            )
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
            await self._send_error_message(
                context, 
                chat_id, 
                mention_message, 
                "Произошла неизвестная ошибка. Пожалуйста, попробуйте позже."
            )
    
    async def _process_mention(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        mention_message: MentionMessage,
        chat_service: ChatService,
        mention_service: MentionService
    ) -> None:
        """Обрабатывает упоминание участников"""
        chat_id = mention_message.chat_id
        
        # Получаем список участников
        members = await chat_service.get_all_members(chat_id)
        
        if not members:
            await mention_service.send_mention_message(
                chat_id=chat_id,
                message=(
                    f"{mention_message.formatted_message}\n"
                    "Не удалось найти участников (кроме ботов). "
                    "Telegram API ограничивает доступ к полному списку участников."
                )
            )
            return
        
        # Формируем сообщение с упоминаниями
        response = mention_service.build_mention_message(mention_message, members)
        
        if not response:
            # Сообщение слишком длинное
            await mention_service.send_mention_message(
                chat_id=chat_id,
                message=(
                    f"{mention_message.formatted_message}\n"
                    "Слишком много участников для тегирования в одном сообщении!"
                )
            )
            return
        
        # Отправляем сообщение с упоминаниями
        success = await mention_service.send_mention_message(chat_id, response)
        
        if success:
            # Пытаемся удалить оригинальное сообщение
            deleted = await mention_service.delete_original_message(
                chat_id, 
                mention_message.message_id
            )
            
            if not deleted:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Не удалось удалить оригинальное сообщение. Проверьте мои права администратора."
                )
    
    async def _send_error_message(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        mention_message: MentionMessage,
        error_text: str
    ) -> None:
        """Отправляет сообщение об ошибке"""
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{mention_message.formatted_message}\n{error_text}",
            parse_mode="HTML"
        )


# Создаем экземпляр обработчика
message_handler = MessageHandler()


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Публичная функция-обертка для обработчика сообщений"""
    await message_handler.handle_message(update, context)

