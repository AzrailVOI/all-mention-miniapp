"""Сервис для хранения информации о чатах"""
import logging
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from telegram import Chat, Bot

logger = logging.getLogger(__name__)

# Глобальный экземпляр сервиса хранения чатов
chat_storage = None

# Путь к файлу для сохранения чатов
STORAGE_FILE = "chats_storage.json"


class ChatStorageService:
    """Сервис для хранения и получения информации о чатах"""
    
    def __init__(self, storage_file: str = STORAGE_FILE):
        # In-memory хранилище (можно заменить на БД)
        self._chats: Dict[int, Dict] = {}
        self._storage_file = storage_file
        # Загружаем чаты из файла при инициализации
        self._load_from_file()
    
    def register_chat(self, chat: Chat) -> None:
        """Регистрирует чат в хранилище"""
        try:
            chat_data = {
                'id': chat.id,
                'title': chat.title or chat.first_name or 'Без названия',
                'type': chat.type,
                'username': getattr(chat, 'username', None),
                'registered_at': datetime.now().isoformat(),
                'members_count': getattr(chat, 'members_count', None)
            }
            
            is_new = chat.id not in self._chats
            self._chats[chat.id] = chat_data
            
            if is_new:
                logger.info(f"[ChatStorage] Зарегистрирован новый чат: {chat.id} ({chat.type}) - {chat_data['title']}")
                print(f"[ChatStorage] Зарегистрирован новый чат: {chat.id} ({chat.type}) - {chat_data['title']}")
            else:
                logger.debug(f"[ChatStorage] Обновлен чат: {chat.id} ({chat.type}) - {chat_data['title']}")
            
            # Сохраняем в файл
            self._save_to_file()
            
            logger.info(f"[ChatStorage] Всего чатов в хранилище: {len(self._chats)}")
            print(f"[ChatStorage] Всего чатов в хранилище: {len(self._chats)}")
            
        except Exception as e:
            logger.error(f"[ChatStorage] Ошибка при регистрации чата: {e}")
            print(f"[ChatStorage] Ошибка при регистрации чата: {e}")
    
    def get_chat(self, chat_id: int) -> Optional[Dict]:
        """Получает информацию о чате"""
        return self._chats.get(chat_id)
    
    def get_all_chats(self) -> List[Dict]:
        """Получает список всех зарегистрированных чатов"""
        chats = list(self._chats.values())
        logger.info(f"[ChatStorage] Запрошен список чатов: возвращено {len(chats)} чатов")
        print(f"[ChatStorage] Запрошен список чатов: возвращено {len(chats)} чатов")
        return chats
    
    def get_chats_by_type(self, chat_type: str) -> List[Dict]:
        """Получает чаты по типу"""
        return [chat for chat in self._chats.values() if chat['type'] == chat_type]
    
    def get_stats(self) -> Dict:
        """Получает статистику по чатам"""
        all_chats = self.get_all_chats()
        
        stats = {
            'total': len(all_chats),
            'groups': len([c for c in all_chats if c['type'] == 'group']),
            'supergroups': len([c for c in all_chats if c['type'] == 'supergroup']),
            'private': len([c for c in all_chats if c['type'] == 'private']),
            'channels': len([c for c in all_chats if c['type'] == 'channel'])
        }
        
        return stats
    
    async def update_chat_info(self, bot: Bot, chat_id: int) -> Optional[Dict]:
        """Обновляет информацию о чате из Telegram API"""
        try:
            chat = await bot.get_chat(chat_id)
            
            chat_data = {
                'id': chat.id,
                'title': chat.title or chat.first_name or 'Без названия',
                'type': chat.type,
                'username': getattr(chat, 'username', None),
                'members_count': getattr(chat, 'members_count', None)
            }
            
            # Сохраняем время регистрации, если чат уже был зарегистрирован
            if chat_id in self._chats:
                chat_data['registered_at'] = self._chats[chat_id].get('registered_at')
            else:
                chat_data['registered_at'] = datetime.now().isoformat()
            
            self._chats[chat_id] = chat_data
            # Сохраняем в файл
            self._save_to_file()
            return chat_data
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении информации о чате {chat_id}: {e}")
            return None
    
    def _save_to_file(self) -> None:
        """Сохраняет чаты в файл"""
        try:
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._chats, f, ensure_ascii=False, indent=2)
            logger.debug(f"[ChatStorage] Чаты сохранены в файл: {self._storage_file}")
        except Exception as e:
            logger.error(f"[ChatStorage] Ошибка при сохранении чатов в файл: {e}")
            print(f"[ChatStorage] Ошибка при сохранении чатов в файл: {e}")
    
    def _load_from_file(self) -> None:
        """Загружает чаты из файла"""
        try:
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    loaded_chats = json.load(f)
                    # Конвертируем ключи обратно в int
                    self._chats = {int(k): v for k, v in loaded_chats.items()}
                logger.info(f"[ChatStorage] Загружено {len(self._chats)} чатов из файла: {self._storage_file}")
                print(f"[ChatStorage] Загружено {len(self._chats)} чатов из файла: {self._storage_file}")
            else:
                logger.info(f"[ChatStorage] Файл {self._storage_file} не найден, начинаем с пустого хранилища")
                print(f"[ChatStorage] Файл {self._storage_file} не найден, начинаем с пустого хранилища")
        except Exception as e:
            logger.error(f"[ChatStorage] Ошибка при загрузке чатов из файла: {e}")
            print(f"[ChatStorage] Ошибка при загрузке чатов из файла: {e}")
            self._chats = {}


# Инициализируем глобальный экземпляр
chat_storage = ChatStorageService()

