"""Модели для работы с сообщениями"""
from dataclasses import dataclass
from typing import Optional
from telegram import User


@dataclass
class MentionMessage:
    """Модель сообщения для упоминания участников"""
    author: User
    original_text: str
    cleaned_text: str
    chat_id: int
    message_id: int
    
    @property
    def author_display_name(self) -> str:
        """Возвращает отображаемое имя автора"""
        if self.author.first_name:
            return f"<b>{self.author.first_name}</b>"
        return self.author.username or "Неизвестный пользователь"
    
    @property
    def formatted_message(self) -> str:
        """Возвращает отформатированное сообщение с именем автора"""
        return f"{self.author_display_name}: {self.cleaned_text}"

