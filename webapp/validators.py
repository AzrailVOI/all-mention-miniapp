"""Валидация входных данных для API endpoints"""
from typing import Optional
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class ChatListRequest(BaseModel):
    """Модель валидации запроса списка чатов"""
    init_data: str = Field(..., description="Данные от Telegram WebApp")
    user_id: int = Field(..., gt=0, description="ID пользователя Telegram")
    page: int = Field(1, ge=1, description="Номер страницы (начинается с 1)")
    per_page: int = Field(20, ge=1, le=100, description="Количество чатов на странице (1-100)")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Валидация user_id"""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        return v
    
    @validator('init_data')
    def validate_init_data(cls, v):
        """Валидация init_data"""
        if not isinstance(v, str) or len(v) == 0:
            raise ValueError("init_data не может быть пустым")
        if len(v) > 10000:  # Разумный лимит
            raise ValueError("init_data слишком длинный")
        return v


class ChatMembersRequest(BaseModel):
    """Модель валидации запроса участников чата"""
    user_id: int = Field(..., gt=0, description="ID пользователя Telegram")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Валидация user_id"""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        return v


def validate_chat_id(chat_id: str) -> int:
    """
    Валидирует и преобразует chat_id в int.
    
    Args:
        chat_id: Строка с ID чата
        
    Returns:
        int: Валидный ID чата
        
    Raises:
        ValueError: Если chat_id невалиден
    """
    try:
        chat_id_int = int(chat_id)
        # Telegram chat_id может быть отрицательным для групп
        if chat_id_int == 0:
            raise ValueError("chat_id не может быть 0")
        return chat_id_int
    except (ValueError, TypeError) as e:
        raise ValueError(f"Неверный формат chat_id: {chat_id}") from e
