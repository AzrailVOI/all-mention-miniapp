"""Сервис для работы с чатами и участниками"""
import logging
from typing import List
from telegram import Bot, User
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class ChatService:
    """Сервис для работы с чатами"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def is_bot_admin(self, chat_id: int) -> bool:
        """Проверяет, является ли бот администратором чата"""
        try:
            bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
            is_admin = bot_member.status in ["administrator", "creator"]
            logger.info(f"[ChatService] Бот {self.bot.id} в чате {chat_id}: статус = {bot_member.status}, является админом = {is_admin}")
            print(f"[ChatService] Бот {self.bot.id} в чате {chat_id}: статус = {bot_member.status}, является админом = {is_admin}")
            return is_admin
        except TelegramError as e:
            logger.error(f"[ChatService] Ошибка при проверке прав администратора для чата {chat_id}: {e}")
            print(f"[ChatService] Ошибка при проверке прав администратора для чата {chat_id}: {e}")
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
        """Получает количество участников в чате"""
        try:
            chat = await self.bot.get_chat(chat_id)
            return chat.get_members_count() if hasattr(chat, 'get_members_count') else 0
        except TelegramError as e:
            logger.error(f"Ошибка при получении количества участников: {e}")
            return 0
    
    async def is_user_creator(self, chat_id: int, user_id: int) -> bool:
        """Проверяет, является ли пользователь создателем чата"""
        try:
            logger.info(f"[ChatService] Проверка прав создателя: чат {chat_id}, пользователь {user_id}")
            print(f"[ChatService] Проверка прав создателя: чат {chat_id}, пользователь {user_id}")
            
            # Получаем список администраторов
            admins = await self.bot.get_chat_administrators(chat_id)
            logger.info(f"[ChatService] Получено {len(admins)} администраторов для чата {chat_id}")
            print(f"[ChatService] Получено {len(admins)} администраторов для чата {chat_id}")
            
            # Ищем пользователя среди администраторов
            for admin in admins:
                admin_user_id = admin.user.id
                admin_status = admin.status
                logger.debug(f"[ChatService] Админ: {admin_user_id}, статус: {admin_status}")
                
                if admin_user_id == user_id:
                    is_creator = admin_status == "creator"
                    logger.info(f"[ChatService] Пользователь {user_id} найден, статус: {admin_status}, является создателем: {is_creator}")
                    print(f"[ChatService] Пользователь {user_id} найден, статус: {admin_status}, является создателем: {is_creator}")
                    return is_creator
            
            logger.warning(f"[ChatService] Пользователь {user_id} не найден среди администраторов чата {chat_id}")
            print(f"[ChatService] Пользователь {user_id} не найден среди администраторов чата {chat_id}")
            return False
        except TelegramError as e:
            logger.error(f"[ChatService] Ошибка при проверке прав создателя для чата {chat_id}, пользователя {user_id}: {e}")
            print(f"[ChatService] Ошибка при проверке прав создателя для чата {chat_id}, пользователя {user_id}: {e}")
            return False
    
    async def get_chat_members_list(self, chat_id: int) -> List[dict]:
        """
        Получает список всех участников чата с информацией о статусе
        Возвращает список словарей с информацией о пользователях
        """
        members_list = []
        seen_user_ids = set()
        
        try:
            # Получаем всех администраторов (включая создателя)
            admins = await self.bot.get_chat_administrators(chat_id)
            
            for admin in admins:
                user = admin.user
                if user.id not in seen_user_ids:
                    # Получаем фото профиля пользователя
                    profile_photo_url = None
                    try:
                        photos = await self.bot.get_user_profile_photos(user.id, limit=1)
                        if photos and photos.total_count > 0 and photos.photos:
                            # Берем самое большое фото (последний элемент в массиве размеров)
                            photo = photos.photos[0][-1]  # Последний элемент - самое большое фото
                            file = await self.bot.get_file(photo.file_id)
                            # Формируем URL для доступа к файлу
                            profile_photo_url = file.file_path
                            logger.debug(f"[ChatService] Получено фото профиля для пользователя {user.id}: {profile_photo_url}")
                    except Exception as e:
                        logger.debug(f"[ChatService] Не удалось получить фото профиля для пользователя {user.id}: {e}")
                        pass
                    
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
            
        except TelegramError as e:
            logger.error(f"Ошибка при получении участников чата: {e}")
            raise
        
        return members_list

