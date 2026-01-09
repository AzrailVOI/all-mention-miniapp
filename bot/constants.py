"""Константы для бота"""
from enum import Enum


class ChatType(str, Enum):
    """Типы чатов в Telegram"""
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
    
    @classmethod
    def get_group_types(cls) -> list[str]:
        """Возвращает типы, которые являются группами"""
        return [cls.GROUP, cls.SUPERGROUP]
    
    @classmethod
    def is_group(cls, chat_type: str) -> bool:
        """Проверяет, является ли тип чата группой"""
        return chat_type in cls.get_group_types()


class ChatMemberStatus(str, Enum):
    """Статусы участников чата в Telegram"""
    CREATOR = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    KICKED = "kicked"
    
    @classmethod
    def get_admin_statuses(cls) -> list[str]:
        """Возвращает статусы, которые являются администраторами"""
        return [cls.ADMINISTRATOR, cls.CREATOR]
    
    @classmethod
    def is_admin(cls, status: str) -> bool:
        """Проверяет, является ли статус администратором"""
        return status in cls.get_admin_statuses()
    
    @classmethod
    def get_active_statuses(cls) -> list[str]:
        """Возвращает статусы активных участников (не left/kicked)"""
        return [cls.MEMBER, cls.ADMINISTRATOR, cls.CREATOR, cls.RESTRICTED]
    
    @classmethod
    def is_active(cls, status: str) -> bool:
        """Проверяет, является ли участник активным"""
        return status in cls.get_active_statuses()


# Триггеры для упоминания всех (используются из Config, но можно добавить сюда для консистентности)
MENTION_TRIGGERS = ["@all", "@everybody_mention_bot", "@everyone"]
