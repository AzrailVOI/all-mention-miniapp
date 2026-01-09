"""
Утилиты для валидации входных данных с использованием Pydantic
"""
from functools import wraps
from typing import Callable, Any
from flask import request, jsonify
from pydantic import ValidationError

from webapp.schemas import (
    ChatListRequest,
    ChatMembersRequest,
    DeleteChatRequest,
    ChatIdPath
)


def validate_request(schema_class: type):
    """
    Декоратор для валидации входных данных запроса через Pydantic схему.
    
    Args:
        schema_class: Класс Pydantic схемы для валидации
        
    Returns:
        Декорированная функция с валидацией
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Получаем JSON данные из запроса
                json_data = request.get_json() or {}
                
                # Валидируем данные через Pydantic схему
                validated_data = schema_class(**json_data)
                
                # Добавляем валидированные данные в kwargs для использования в функции
                kwargs['validated_data'] = validated_data
                
                return func(*args, **kwargs)
            except ValidationError as e:
                # Возвращаем детальные ошибки валидации
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")
                
                return jsonify({
                    'success': False,
                    'error': 'Ошибка валидации входных данных',
                    'details': errors
                }), 400
            except Exception as e:
                # Обрабатываем другие ошибки (например, если JSON невалиден)
                return jsonify({
                    'success': False,
                    'error': f'Ошибка при обработке запроса: {str(e)}'
                }), 400
        
        return wrapper
    return decorator


def validate_path_param(param_name: str, schema_class: type):
    """
    Декоратор для валидации параметров пути URL через Pydantic схему.
    
    Args:
        param_name: Имя параметра в пути (например, 'chat_id')
        schema_class: Класс Pydantic схемы для валидации
        
    Returns:
        Декорированная функция с валидацией
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Получаем значение параметра из kwargs
                param_value = kwargs.get(param_name)
                
                if param_value is None:
                    return jsonify({
                        'success': False,
                        'error': f'Параметр {param_name} не предоставлен'
                    }), 400
                
                # Валидируем параметр через Pydantic схему
                validated_param = schema_class(**{param_name: param_value})
                
                # Заменяем значение в kwargs на валидированное
                kwargs[param_name] = getattr(validated_param, param_name)
                
                return func(*args, **kwargs)
            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    message = error['msg']
                    errors.append(f"{field}: {message}")
                
                return jsonify({
                    'success': False,
                    'error': f'Ошибка валидации параметра {param_name}',
                    'details': errors
                }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Ошибка при валидации параметра {param_name}: {str(e)}'
                }), 400
        
        return wrapper
    return decorator
