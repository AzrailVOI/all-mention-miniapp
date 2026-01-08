"""Валидация данных Telegram WebApp"""
import hmac
import hashlib
import logging
from typing import Dict, Optional
from urllib.parse import parse_qsl, unquote
from datetime import datetime, timezone

from bot.config import Config

logger = logging.getLogger(__name__)


def validate_telegram_webapp_data(init_data: str) -> bool:
    """
    Валидирует данные от Telegram WebApp через проверку подписи HMAC-SHA256.
    
    Telegram WebApp отправляет данные в формате query string:
    user=...&auth_date=...&hash=...
    
    Алгоритм валидации:
    1. Извлечь hash из init_data
    2. Создать data_check_string из всех полей кроме hash, отсортированных по ключу
    3. Вычислить secret_key = HMAC-SHA256(bot_token, "WebAppData")
    4. Вычислить проверочный hash = HMAC-SHA256(secret_key, data_check_string)
    5. Сравнить с полученным hash
    
    Args:
        init_data: Строка с данными от Telegram WebApp в формате query string
        
    Returns:
        True если данные валидны, False в противном случае
    """
    if not init_data:
        logger.warning("WebApp validation failed: empty init_data")
        return False
    
    try:
        # Парсим query string
        parsed_data = dict(parse_qsl(init_data))
        
        # Извлекаем hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            logger.warning("WebApp validation failed: hash not found in init_data")
            return False
        
        # Проверяем время создания (auth_date)
        auth_date_str = parsed_data.get('auth_date')
        if auth_date_str:
            try:
                auth_date = datetime.fromtimestamp(int(auth_date_str), tz=timezone.utc)
                now = datetime.now(timezone.utc)
                age_seconds = (now - auth_date).total_seconds()
                
                if age_seconds > Config.WEBAPP_DATA_MAX_AGE:
                    logger.warning(
                        f"WebApp validation failed: data too old "
                        f"({age_seconds:.0f} seconds, max {Config.WEBAPP_DATA_MAX_AGE})"
                    )
                    return False
            except (ValueError, TypeError) as e:
                logger.warning(f"WebApp validation failed: invalid auth_date: {e}")
                return False
        
        # Создаем data_check_string: все поля кроме hash, отсортированные по ключу
        # Формат: key=value\nkey2=value2 (отсортировано по ключу)
        data_check_parts = []
        for key in sorted(parsed_data.keys()):
            value = parsed_data[key]
            # URL decode значение
            decoded_value = unquote(value)
            data_check_parts.append(f"{key}={decoded_value}")
        
        data_check_string = '\n'.join(data_check_parts)
        
        # Вычисляем secret_key = HMAC-SHA256(bot_token, "WebAppData")
        secret_key = hmac.new(
            "WebAppData".encode('utf-8'),
            Config.WEBAPP_SECRET_KEY.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Вычисляем проверочный hash = HMAC-SHA256(secret_key, data_check_string)
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем hash (constant-time comparison для безопасности)
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("WebApp validation failed: hash mismatch")
            return False
        
        logger.debug("WebApp validation successful")
        return True
        
    except Exception as e:
        logger.error(f"WebApp validation error: {e}", exc_info=True)
        return False


def parse_webapp_data(init_data: str) -> Optional[Dict]:
    """
    Парсит данные Telegram WebApp и возвращает словарь.
    
    Args:
        init_data: Строка с данными от Telegram WebApp
        
    Returns:
        Словарь с распарсенными данными или None при ошибке
    """
    if not init_data:
        return None
    
    try:
        parsed_data = dict(parse_qsl(init_data))
        # Убираем hash из результата
        parsed_data.pop('hash', None)
        
        # Парсим JSON поля если есть
        if 'user' in parsed_data:
            import json
            try:
                parsed_data['user'] = json.loads(parsed_data['user'])
            except json.JSONDecodeError:
                pass
        
        if 'start_param' in parsed_data:
            # start_param может быть пустой строкой
            if not parsed_data['start_param']:
                parsed_data.pop('start_param')
        
        return parsed_data
    except Exception as e:
        logger.error(f"Error parsing WebApp data: {e}", exc_info=True)
        return None
