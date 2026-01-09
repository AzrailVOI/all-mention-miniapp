"""
Pydantic схемы для валидации входных данных API
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl
import re


class ChatListRequest(BaseModel):
    """
    Схема для запроса списка чатов.
    
    Attributes:
        init_data: Данные инициализации Telegram WebApp (строка с параметрами)
        user_id: ID пользователя Telegram
        force_refresh: Принудительное обновление кэша
    """
    init_data: str = Field(
        ...,
        min_length=1,
        description="Данные инициализации Telegram WebApp"
    )
    user_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID пользователя Telegram"
    )
    force_refresh: bool = Field(
        default=False,
        description="Принудительное обновление кэша"
    )
    
    @field_validator('init_data')
    @classmethod
    def validate_init_data(cls, v: str) -> str:
        """
        Валидирует формат init_data.
        
        Args:
            v: Строка init_data
            
        Returns:
            Валидированная строка
            
        Raises:
            ValueError: Если формат неверный
        """
        if not v or not v.strip():
            raise ValueError("init_data не может быть пустым")
        
        # Проверяем базовый формат (должен содержать параметры)
        if '=' not in v:
            raise ValueError("init_data имеет неверный формат")
        
        return v.strip()
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        """
        Валидирует user_id.
        
        Args:
            v: ID пользователя
            
        Returns:
            Валидированный ID
            
        Raises:
            ValueError: Если ID неверный
        """
        if v is not None and v < 1:
            raise ValueError("user_id должен быть положительным числом")
        return v


class ChatMembersRequest(BaseModel):
    """
    Схема для запроса списка участников чата.
    
    Attributes:
        init_data: Данные инициализации Telegram WebApp
        user_id: ID пользователя Telegram
        force_refresh: Принудительное обновление кэша
    """
    init_data: str = Field(
        ...,
        min_length=1,
        description="Данные инициализации Telegram WebApp"
    )
    user_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID пользователя Telegram"
    )
    force_refresh: bool = Field(
        default=False,
        description="Принудительное обновление кэша"
    )
    
    @field_validator('init_data')
    @classmethod
    def validate_init_data(cls, v: str) -> str:
        """Валидирует формат init_data"""
        if not v or not v.strip():
            raise ValueError("init_data не может быть пустым")
        if '=' not in v:
            raise ValueError("init_data имеет неверный формат")
        return v.strip()
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        """Валидирует user_id"""
        if v is not None and v < 1:
            raise ValueError("user_id должен быть положительным числом")
        return v


class DeleteChatRequest(BaseModel):
    """
    Схема для запроса удаления чата.
    
    Attributes:
        init_data: Данные инициализации Telegram WebApp
        user_id: ID пользователя Telegram
    """
    init_data: str = Field(
        ...,
        min_length=1,
        description="Данные инициализации Telegram WebApp"
    )
    user_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID пользователя Telegram"
    )
    
    @field_validator('init_data')
    @classmethod
    def validate_init_data(cls, v: str) -> str:
        """Валидирует формат init_data"""
        if not v or not v.strip():
            raise ValueError("init_data не может быть пустым")
        if '=' not in v:
            raise ValueError("init_data имеет неверный формат")
        return v.strip()
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        """Валидирует user_id"""
        if v is not None and v < 1:
            raise ValueError("user_id должен быть положительным числом")
        return v


class ChatIdPath(BaseModel):
    """
    Схема для валидации chat_id из пути URL.
    
    Attributes:
        chat_id: ID чата
    """
    chat_id: int = Field(
        ...,
        ge=-9223372036854775808,  # Минимальное значение int64
        le=9223372036854775807,   # Максимальное значение int64
        description="ID чата Telegram"
    )
    
    @field_validator('chat_id')
    @classmethod
    def validate_chat_id(cls, v: int) -> int:
        """
        Валидирует chat_id.
        
        Telegram chat_id может быть отрицательным для групп.
        
        Args:
            v: ID чата
            
        Returns:
            Валидированный ID
            
        Raises:
            ValueError: Если ID неверный
        """
        # Telegram chat_id для групп отрицательный
        # Проверяем, что это валидный int64
        if not isinstance(v, int):
            raise ValueError("chat_id должен быть целым числом")
        return v
