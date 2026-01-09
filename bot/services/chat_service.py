"""Сервис для работы с чатами и участниками"""
import logging
from typing import List, Dict, Any, Optional
from telegram import Bot, User
from telegram.error import TelegramError

from bot.utils.retry import retry_async
from bot.constants import ChatMemberStatus

logger = logging.getLogger(__name__)


class ChatService:
    """
    Сервис для работы с чатами и участниками через Telegram Bot API.
    
    Предоставляет методы для проверки прав бота, получения списка участников,
    проверки статуса пользователей и другой функциональности, связанной с чатами.
    """
    
    def __init__(self, bot: Bot):
        """
        Инициализирует сервис с экземпляром бота.
        
        Args:
            bot: Экземпляр Telegram Bot для выполнения API запросов
        """
        self.bot = bot
    
    async def is_bot_admin(self, chat_id: int) -> bool:
        """
        Проверяет, является ли бот администратором чата.
        
        Args:
            chat_id: ID чата для проверки
            
        Returns:
            True если бот является администратором или создателем, False в противном случае
            
        Note:
            В случае ошибки API возвращает False и логирует ошибку.
        """
        try:
            bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
            is_admin = ChatMemberStatus.is_admin(bot_member.status)
            logger.info(f"[ChatService] Бот {self.bot.id} в чате {chat_id}: статус = {bot_member.status}, является админом = {is_admin}")
            return is_admin
        except TelegramError as e:
            logger.error(f"[ChatService] Ошибка при проверке прав администратора для чата {chat_id}: {e}")
            return False
    
    async def get_all_members(self, chat_id: int) -> List[User]:
        """
        Получает список всех участников чата (кроме ботов)
        
        Примечание: Telegram Bot API не предоставляет прямой метод для получения
        полного списка участников группы. Используем доступные методы:
        1. get_chat_administrators - получает всех администраторов
        2. Для получения остальных участников требуется использовать методы,
           которые доступны только в Telegram Client API (MTProto), а не в Bot API.
        
        В Bot API можно получить информацию о конкретном участнике через get_chat_member,
        но для этого нужно знать его user_id заранее.
        """
        members = []
        seen_user_ids = set()
        
        try:
            # Получаем всех администраторов (включая создателя)
            admins = await self.bot.get_chat_administrators(chat_id)
            
            for admin in admins:
                user = admin.user
                if not user.is_bot and user.id not in seen_user_ids:
                    members.append(user)
                    seen_user_ids.add(user.id)
            
            # Примечание: Для получения всех участников группы в Bot API нет прямого метода.
            # Можно попробовать использовать get_chat_member для известных user_id,
            # но это требует предварительного знания ID всех участников.
            # Альтернатива - использовать Telegram Client API (pyrogram, telethon),
            # но это выходит за рамки Bot API.
            
            logger.info(f"Получено {len(members)} участников из администраторов чата {chat_id}")
            
        except TelegramError as e:
            logger.error(f"Ошибка при получении участников чата: {e}")
            raise
        
        return members
    
    async def get_chat_member_count(self, chat_id: int) -> int:
        """
        Получает количество участников в чате.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Количество участников в чате, или 0 в случае ошибки
        """
        try:
            chat = await self.bot.get_chat(chat_id)
            return chat.get_members_count() if hasattr(chat, 'get_members_count') else 0
        except TelegramError as e:
            logger.error(f"Ошибка при получении количества участников: {e}")
            return 0
    
    async def is_user_creator(self, chat_id: int, user_id: int) -> bool:
        """
        Проверяет, является ли пользователь создателем чата.
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя для проверки
            
        Returns:
            True если пользователь является создателем чата, False в противном случае
            
        Note:
            Метод получает список администраторов и проверяет статус пользователя.
            В случае ошибки API возвращает False.
        """
        try:
            logger.info(f"[ChatService] Проверка прав создателя: чат {chat_id}, пользователь {user_id}")
            
            # Получаем список администраторов
            admins = await self.bot.get_chat_administrators(chat_id)
            logger.info(f"[ChatService] Получено {len(admins)} администраторов для чата {chat_id}")
            
            # Ищем пользователя среди администраторов
            for admin in admins:
                admin_user_id = admin.user.id
                admin_status = admin.status
                logger.debug(f"[ChatService] Админ: {admin_user_id}, статус: {admin_status}")
                
                if admin_user_id == user_id:
                    is_creator = admin_status == ChatMemberStatus.CREATOR
                    logger.info(f"[ChatService] Пользователь {user_id} найден, статус: {admin_status}, является создателем: {is_creator}")
                    return is_creator
            
            logger.warning(f"[ChatService] Пользователь {user_id} не найден среди администраторов чата {chat_id}")
            return False
        except TelegramError as e:
            logger.error(f"[ChatService] Ошибка при проверке прав создателя для чата {chat_id}, пользователя {user_id}: {e}")
            return False
    
    async def get_chat_members_list(self, chat_id: int, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Получает список всех участников чата с информацией о статусе и правах.
        
        Args:
            chat_id: ID чата
            use_cache: Использовать ли кэш участников (по умолчанию True)
            
        Returns:
            Список словарей с информацией о каждом участнике, включая:
            - id, first_name, last_name, username
            - is_bot
            - status (creator, administrator, member)
            - profile_photo_url (если доступно)
            - права администратора (can_delete_messages, can_manage_chat, и т.д.)
            - cached: True если данные из кэша
            
        Raises:
            TelegramError: При ошибке получения данных из Telegram API
            
        Note:
            В Bot API доступны только администраторы. Обычные участники
            не могут быть получены без знания их user_id заранее.
            
            Для получения полного списка участников требуется использовать
            Telegram Client API (MTProto) через библиотеки типа pyrogram или telethon.
            См. bot/services/member_research.md для подробностей.
        """
        # Проверяем кэш, если включено
        if use_cache:
            from bot.services.member_cache_service import member_cache
            cached_members = member_cache.get_cached_members(chat_id)
            if cached_members:
                logger.info(f"[ChatService] Использованы кэшированные данные участников для чата {chat_id}")
                return cached_members
        
        members_list = []
        seen_user_ids = set()
        
        try:
            # Получаем всех администраторов (включая создателя)
            # ВАЖНО: Telegram Bot API не предоставляет способ получить полный список участников.
            # Доступны только администраторы через get_chat_administrators().
            # Для получения всех участников требуется Telegram Client API (MTProto).
            admins = await self.bot.get_chat_administrators(chat_id)
            
            for admin in admins:
                user = admin.user
                if user.id not in seen_user_ids:
                    # Получаем фото профиля пользователя
                    profile_photo_url = None
                    try:
                        logger.info(f"[ChatService] Получение фото профиля для пользователя {user.id} ({user.first_name})")
                        
                        photos = await self.bot.get_user_profile_photos(user.id, limit=1)
                        logger.info(f"[ChatService] Результат get_user_profile_photos для {user.id}: total_count = {photos.total_count if photos else 0}, photos = {photos.photos if photos else None}")
                        
                        if photos and photos.total_count > 0 and photos.photos:
                            # Берем самое большое фото (последний элемент в массиве размеров)
                            photo = photos.photos[0][-1]  # Последний элемент - самое большое фото
                            logger.info(f"[ChatService] Получение файла фото для пользователя {user.id}: file_id = {photo.file_id}")
                            
                            file = await self.bot.get_file(photo.file_id)
                            # Формируем URL для доступа к файлу
                            profile_photo_url = file.file_path
                            logger.info(f"[ChatService] Получено фото профиля для пользователя {user.id}: {profile_photo_url}")
                        else:
                            logger.info(f"[ChatService] Пользователь {user.id} не имеет фото профиля (total_count = {photos.total_count if photos else 0})")
                    except Exception as e:
                        logger.error(f"[ChatService] Ошибка при получении фото профиля для пользователя {user.id}: {e}", exc_info=True)
                    
                    member_info = {
                        'id': user.id,
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                        'username': user.username or '',
                        'is_bot': user.is_bot,
                        'status': admin.status,  # creator, administrator, member
                        'profile_photo_url': profile_photo_url,  # URL фото профиля
                        'can_be_edited': getattr(admin, 'can_be_edited', False),
                        'can_manage_chat': getattr(admin, 'can_manage_chat', False),
                        'can_delete_messages': getattr(admin, 'can_delete_messages', False),
                        'can_manage_video_chats': getattr(admin, 'can_manage_video_chats', False),
                        'can_restrict_members': getattr(admin, 'can_restrict_members', False),
                        'can_promote_members': getattr(admin, 'can_promote_members', False),
                        'can_change_info': getattr(admin, 'can_change_info', False),
                        'can_invite_users': getattr(admin, 'can_invite_users', False),
                        'can_post_messages': getattr(admin, 'can_post_messages', False),
                        'can_edit_messages': getattr(admin, 'can_edit_messages', False),
                        'can_pin_messages': getattr(admin, 'can_pin_messages', False),
                    }
                    members_list.append(member_info)
                    seen_user_ids.add(user.id)
            
            logger.info(f"Получено {len(members_list)} участников из администраторов чата {chat_id}")
            
            # Кэшируем полученных участников
            if use_cache:
                from bot.services.member_cache_service import member_cache
                member_cache.cache_members(chat_id, members_list)
            
        except TelegramError as e:
            logger.error(f"Ошибка при получении участников чата: {e}")
            raise
        
        return members_list

