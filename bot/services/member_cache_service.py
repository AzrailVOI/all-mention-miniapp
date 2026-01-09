"""
Сервис для кэширования и обновления информации об участниках чата
"""
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from telegram import Bot, User

from bot.services.chat_storage_service import chat_storage

logger = logging.getLogger(__name__)

# Время жизни кэша участников (24 часа)
MEMBER_CACHE_TTL = timedelta(hours=24)


class MemberCacheService:
    """
    Сервис для кэширования и управления информацией об участниках чата.
    
    Использует хранилище чатов для сохранения информации об участниках,
    обновляя её при получении данных из Telegram API и событиях чата.
    """
    
    def __init__(self):
        """Инициализирует MemberCacheService"""
        self._member_cache: Dict[int, Dict[int, Dict]] = {}  # {chat_id: {user_id: member_data}}
    
    def cache_members(self, chat_id: int, members: List[Dict]) -> None:
        """
        Кэширует список участников чата.
        
        Args:
            chat_id: ID чата
            members: Список словарей с информацией об участниках
        """
        if chat_id not in self._member_cache:
            self._member_cache[chat_id] = {}
        
        for member in members:
            user_id = member.get('id')
            if user_id:
                self._member_cache[chat_id][user_id] = {
                    **member,
                    'cached_at': datetime.now().isoformat()
                }
        
        logger.info(f"[MemberCache] Кэшировано {len(members)} участников для чата {chat_id}")
    
    def get_cached_members(self, chat_id: int) -> Optional[List[Dict]]:
        """
        Получает кэшированный список участников чата.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Список участников или None, если кэш отсутствует или устарел
        """
        if chat_id not in self._member_cache:
            return None
        
        cached_members = []
        now = datetime.now()
        
        for user_id, member_data in self._member_cache[chat_id].items():
            cached_at_str = member_data.get('cached_at')
            if cached_at_str:
                try:
                    cached_at = datetime.fromisoformat(cached_at_str)
                    if now - cached_at < MEMBER_CACHE_TTL:
                        cached_members.append(member_data)
                    else:
                        # Удаляем устаревшие записи
                        del self._member_cache[chat_id][user_id]
                except (ValueError, TypeError):
                    # Если не удалось распарсить дату, оставляем запись
                    cached_members.append(member_data)
        
        if cached_members:
            logger.info(f"[MemberCache] Возвращено {len(cached_members)} кэшированных участников для чата {chat_id}")
            return cached_members
        
        return None
    
    def update_member(self, chat_id: int, user_id: int, member_data: Dict) -> None:
        """
        Обновляет информацию об участнике в кэше.
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            member_data: Данные об участнике
        """
        if chat_id not in self._member_cache:
            self._member_cache[chat_id] = {}
        
        self._member_cache[chat_id][user_id] = {
            **member_data,
            'cached_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        logger.debug(f"[MemberCache] Обновлен участник {user_id} в чате {chat_id}")
    
    def remove_member(self, chat_id: int, user_id: int) -> None:
        """
        Удаляет участника из кэша.
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
        """
        if chat_id in self._member_cache and user_id in self._member_cache[chat_id]:
            del self._member_cache[chat_id][user_id]
            logger.debug(f"[MemberCache] Удален участник {user_id} из кэша чата {chat_id}")
    
    def clear_cache(self, chat_id: Optional[int] = None) -> None:
        """
        Очищает кэш участников.
        
        Args:
            chat_id: ID чата (если None, очищает весь кэш)
        """
        if chat_id:
            if chat_id in self._member_cache:
                del self._member_cache[chat_id]
                logger.info(f"[MemberCache] Очищен кэш участников для чата {chat_id}")
        else:
            self._member_cache.clear()
            logger.info("[MemberCache] Очищен весь кэш участников")
    
    def get_cached_user_ids(self, chat_id: int) -> Set[int]:
        """
        Получает множество ID пользователей из кэша.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Множество ID пользователей
        """
        if chat_id not in self._member_cache:
            return set()
        
        return set(self._member_cache[chat_id].keys())


# Глобальный экземпляр сервиса
member_cache = MemberCacheService()
