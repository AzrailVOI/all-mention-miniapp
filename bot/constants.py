"""Константы для бота"""
from enum import Enum


class ChatType(str, Enum):
    """Типы чатов Telegram"""
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class ChatMemberStatus(str, Enum):
    """Статусы участников чата"""
    CREATOR = "creator"
    ADMINISTRATOR = "administrator"
    MEMBER = "member"
    RESTRICTED = "restricted"
    LEFT = "left"
    KICKED = "kicked"


class ChatMemberUpdateStatus(str, Enum):
    """Статусы для обновления участников"""
    MEMBER = "member"
    ADMINISTRATOR = "administrator"
    CREATOR = "creator"
    LEFT = "left"


# Триггеры для упоминания всех участников
MENTION_TRIGGERS = ["@all", "@everybody_mention_bot", "@everyone"]

# Максимальная длина сообщения Telegram
MAX_MESSAGE_LENGTH = 4096

# Групповые типы чатов (где работает функционал упоминаний)
GROUP_CHAT_TYPES = [ChatType.GROUP.value, ChatType.SUPERGROUP.value]

# Статусы администраторов
ADMIN_STATUSES = [ChatMemberStatus.CREATOR.value, ChatMemberStatus.ADMINISTRATOR.value]
