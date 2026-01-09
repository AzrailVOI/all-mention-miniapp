"""Flask приложение для Mini App"""
import logging
import hmac
import hashlib
import json
import os
import urllib.parse
import time
import threading
from flask import Flask, render_template, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from telegram import Bot
from telegram.error import TelegramError

from bot.config import Config
from bot.services.chat_storage_service import chat_storage
from bot.utils.correlation import (
    generate_correlation_id, 
    set_correlation_id, 
    get_correlation_id,
    CorrelationIDFilter
)
from bot.exceptions import handle_telegram_error, get_user_friendly_message, TelegramAPIError
from webapp.validators import validate_request, validate_path_param
from webapp.schemas import ChatListRequest, ChatMembersRequest, DeleteChatRequest, ChatIdPath
from webapp.metrics import track_request_metrics, get_metrics, telegram_api_requests_total, telegram_api_request_duration_seconds, errors_total, cache_operations_total, cache_size

logger = logging.getLogger(__name__)

# Добавляем фильтр для correlation ID ко всем логгерам
root_logger = logging.getLogger()
if not any(isinstance(f, CorrelationIDFilter) for f in root_logger.filters):
    root_logger.addFilter(CorrelationIDFilter())

app = Flask(__name__)
# Используем отдельный секретный ключ для Flask сессий (не связан с WebApp валидацией)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', Config.TOKEN)

# Настройка Rate Limiting
# Используем in-memory хранилище (для продакшена можно использовать Redis)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"  # или "moving-window" для более плавного ограничения
)

# Настройка кэширования
# Используем простой in-memory кэш (для продакшена можно использовать Redis)
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',  # Простой in-memory кэш
    'CACHE_DEFAULT_TIMEOUT': 300,  # 5 минут по умолчанию
    'CACHE_THRESHOLD': 1000  # Максимум 1000 записей в кэше
})

# Глобальный экземпляр Bot для переиспользования
_global_bot: Bot | None = None
_bot_lock = threading.Lock()


def get_bot() -> Bot:
    """
    Получает глобальный экземпляр Bot, создавая его при первом вызове.
    Thread-safe инициализация.
    """
    global _global_bot
    if _global_bot is None:
        with _bot_lock:
            # Двойная проверка для thread-safety
            if _global_bot is None:
                _global_bot = Bot(token=Config.TOKEN)
                logger.info("Создан глобальный экземпляр Bot для WebApp")
    return _global_bot

# Версия для cache busting
import time
APP_VERSION = str(int(time.time()))  # Используем timestamp как версию

# Компилируем SCSS при запуске (если в режиме разработки)
# В продакшене можно отключить через переменную окружения COMPILE_SCSS=false
if os.getenv('FLASK_ENV') == 'development' or os.getenv('COMPILE_SCSS', 'true').lower() == 'true':
    try:
        from webapp.utils.scss_compiler import compile_scss
        if compile_scss(output_style='expanded'):
            logger.info("SCSS скомпилирован при запуске приложения")
        else:
            logger.warning("SCSS не был скомпилирован (возможно, файлы не найдены или libsass не установлен)")
    except ImportError as e:
        logger.warning(f"libsass не установлен, пропускаем компиляцию SCSS: {e}")
    except Exception as e:
        logger.warning(f"Не удалось скомпилировать SCSS при запуске: {e}")


def validate_telegram_webapp_data(init_data: str) -> bool:
    """
    Валидирует данные от Telegram WebApp через проверку подписи HMAC-SHA256.
    
    Алгоритм валидации:
    1. Извлекает hash из init_data
    2. Создает строку из всех пар key=value (кроме hash), отсортированных по ключу
    3. Вычисляет HMAC-SHA256 используя секретный ключ
    4. Сравнивает полученный hash с hash из init_data
    5. Проверяет auth_date (время создания, не старше 24 часов)
    
    Args:
        init_data: Строка с данными от Telegram WebApp в формате query string
        
    Returns:
        True если данные валидны, False в противном случае
    """
    try:
        if not init_data:
            logger.warning("Пустые данные WebApp")
            return False
        
        # Парсим query string
        parsed_data = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        
        # Извлекаем hash
        if 'hash' not in parsed_data or not parsed_data['hash']:
            logger.warning("Hash отсутствует в данных WebApp")
            return False
        
        received_hash = parsed_data['hash'][0]
        
        # Создаем строку для проверки: все пары key=value кроме hash, отсортированные по ключу
        data_check_string_parts = []
        for key in sorted(parsed_data.keys()):
            if key == 'hash':
                continue
            value = parsed_data[key][0]
            data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Получаем секретный ключ
        secret_key = Config.get_webapp_secret_key()
        
        # Вычисляем HMAC-SHA256
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем hash
        if calculated_hash != received_hash:
            logger.warning(f"Неверная подпись WebApp данных. Ожидалось: {calculated_hash[:16]}..., получено: {received_hash[:16]}...")
            return False
        
        # Проверяем время создания (auth_date)
        if 'auth_date' in parsed_data:
            try:
                auth_date = int(parsed_data['auth_date'][0])
                current_time = int(time.time())
                # Проверяем, что данные не старше 24 часов
                if current_time - auth_date > 86400:  # 24 часа в секундах
                    logger.warning(f"Данные WebApp устарели. auth_date: {auth_date}, текущее время: {current_time}")
                    return False
            except (ValueError, IndexError) as e:
                logger.warning(f"Неверный формат auth_date: {e}")
                return False
        
        logger.debug("Данные WebApp успешно валидированы")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка валидации данных WebApp: {e}", exc_info=True)
        return False


@app.route('/')
def index():
    """Главная страница Mini App"""
    return render_template('index.html', version=APP_VERSION)


@app.route('/members')
def members_page():
    """Страница участников чата"""
    logger.info(f"[API] GET /members - запрос страницы участников")
    return render_template('members.html', version=APP_VERSION)


@app.after_request
def add_security_headers(response):
    """Добавляет заголовки безопасности, CORS, correlation ID и предотвращения кэширования"""
    # Добавляем correlation ID в заголовки ответа
    correlation_id = get_correlation_id()
    if correlation_id:
        response.headers['X-Correlation-ID'] = correlation_id
    
    # CORS настройки для Telegram WebApp
    # Разрешаем только запросы от Telegram
    origin = request.headers.get('Origin', '')
    if origin.startswith('https://web.telegram.org') or origin.startswith('http://localhost'):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
    
    # Безопасные HTTP заголовки
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy для Mini App
    # Разрешаем только необходимые источники
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' https://api.telegram.org data:; "
        "font-src 'self' https://unpkg.com; "
        "connect-src 'self' https://api.telegram.org; "
        "frame-ancestors 'self' https://web.telegram.org;"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # Заголовки для предотвращения кэширования
    if request.endpoint == 'static' or request.endpoint == 'index':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response


@app.before_request
def handle_preflight():
    """Обработка preflight запросов для CORS и установка correlation ID"""
    # Устанавливаем correlation ID для каждого запроса
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    g.correlation_id = correlation_id
    logger.debug(f"[Request] {request.method} {request.path} - Correlation ID: {correlation_id[:8]}")
    
    # Метрики отслеживаются через декоратор @track_request_metrics на endpoint'ах
    # Здесь не нужно вызывать track_request_metrics(), так как это декоратор
    
    # Обработка preflight запросов для CORS
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin', '')
        if origin.startswith('https://web.telegram.org') or origin.startswith('http://localhost'):
            response = jsonify({})
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '3600'
            if correlation_id:
                response.headers['X-Correlation-ID'] = correlation_id
            return response
        return jsonify({'error': 'CORS not allowed'}), 403


@app.route('/api/chats', methods=['POST'])
@limiter.limit("10 per minute")  # 10 запросов в минуту
@validate_request(ChatListRequest)
def get_chats(validated_data):
    """API endpoint для получения списка чатов напрямую из Telegram API"""
    try:
        # Используем валидированные данные
        init_data = validated_data.init_data
        user_id = validated_data.user_id
        force_refresh = validated_data.force_refresh
        
        correlation_id = get_correlation_id()
        logger.info(f"[API] GET /api/chats - запрос от пользователя {user_id} (correlation_id: {correlation_id[:8] if correlation_id else 'none'})")
        
        if not user_id:
            logger.warning(f"[API] GET /api/chats - User ID не предоставлен")
            return jsonify({
                'success': False,
                'error': 'User ID не предоставлен'
            }), 400
        
        # Проверяем, что init_data не пустой
        if not init_data or not init_data.strip():
            logger.warning(f"[API] Пустые данные WebApp от пользователя {user_id}")
            return jsonify({
                'success': False,
                'error': 'Данные WebApp не предоставлены. Убедитесь, что приложение запущено через Telegram WebApp.'
            }), 401
        
        # Валидация подписи HMAC-SHA256
        if not validate_telegram_webapp_data(init_data):
            logger.warning(f"[API] Невалидные данные WebApp от пользователя {user_id}")
            return jsonify({
                'success': False,
                'error': 'Невалидные данные WebApp. Проверка подписи не пройдена. Убедитесь, что используется правильный токен бота.'
            }), 401
        
        # Определяем ключ кэша для использования в обработчиках исключений
        cache_key = f"chats_{user_id}"
        
        # Используем глобальный экземпляр бота
        bot = get_bot()
        from webapp.utils.chat_helpers import (
            process_chat,
            calculate_stats,
            get_info_message
        )
        
        async def get_chats_from_telegram():
            """Получает и фильтрует чаты из Telegram API"""
            try:
                # Инициализируем бота перед использованием
                await bot.initialize()
                from bot.services.chat_service import ChatService
                chat_service = ChatService(bot)
                
                # Получаем чаты только из хранилища
                stored_chats = chat_storage.get_all_chats()
                logger.info(f"[API] Чатов в хранилище: {len(stored_chats)}")
                
                all_chat_ids = {stored_chat['id'] for stored_chat in stored_chats}
                logger.info(f"[API] Всего чатов для проверки: {len(all_chat_ids)}")
                
                # Если нет чатов, выводим предупреждение
                if len(all_chat_ids) == 0:
                    logger.warning(f"[API] ВНИМАНИЕ: Не найдено чатов в хранилище!")
                    logger.warning(f"[API] Чаты будут появляться автоматически при:")
                    logger.warning(f"[API] 1. Получении сообщений в группах")
                    logger.warning(f"[API] 2. Добавлении бота в группы (событие my_chat_member)")
                    logger.warning(f"[API] 3. Использовании команды /register в группе")
                
                # Обрабатываем каждый чат
                filtered_chats = []
                total_skipped = {'not_group': 0, 'not_admin': 0, 'not_creator': 0}
                
                for chat_id in all_chat_ids:
                    chat_data, skipped = await process_chat(bot, chat_service, chat_id, user_id)
                    if chat_data:
                        filtered_chats.append(chat_data)
                    # Суммируем пропущенные
                    for key in total_skipped:
                        total_skipped[key] += skipped[key]
                
                logger.info(f"[API] Результат фильтрации: {len(filtered_chats)} чатов")
                logger.info(f"[API] Пропущено (не группа): {total_skipped['not_group']}, "
                          f"(бот не админ): {total_skipped['not_admin']}, "
                          f"(пользователь не создатель): {total_skipped['not_creator']}")
                
                # Сортируем чаты по названию
                filtered_chats.sort(key=lambda x: x['title'].lower())
                
                return filtered_chats, len(all_chat_ids)
                        
            except Exception as e:
                logger.error(f"[API] Ошибка при получении чатов: {e}")
                return [], 0
        
        # Запускаем async функцию через утилиту
        from bot.utils.async_loop import run_async
        start_time = time.time()
        try:
            filtered_chats, total_stored_chats = run_async(get_chats_from_telegram())
            # Отслеживаем успешный запрос к Telegram API
            telegram_api_requests_total.labels(method='POST /api/chats', status='success').inc()
            telegram_api_request_duration_seconds.labels(method='POST /api/chats').observe(time.time() - start_time)
        except Exception as e:
            # Отслеживаем ошибку запроса к Telegram API
            telegram_api_requests_total.labels(method='POST /api/chats', status='error').inc()
            telegram_api_request_duration_seconds.labels(method='POST /api/chats').observe(time.time() - start_time)
            raise
        
        # Подсчитываем статистику
        stats = calculate_stats(filtered_chats)
        
        # Добавляем информационное сообщение, если чатов нет
        info_message = get_info_message(len(filtered_chats) > 0, total_stored_chats > 0)
        
        logger.info(f"[API] GET /api/chats - успешно возвращено {len(filtered_chats)} чатов")
        
        response_data = {
            'success': True,
            'chats': filtered_chats,
            'stats': stats
        }
        
        if info_message:
            response_data['info'] = info_message
        
        # Сохраняем в кэш на 5 минут (300 секунд)
        cache.set(cache_key, response_data, timeout=300)
        cache_operations_total.labels(operation='set', status='success').inc()
        cache_size.labels(cache_type='chats').set(cache.get_cache_info().currsize)
        logger.info(f"[API] Данные сохранены в кэш для пользователя {user_id}")
        
        return jsonify(response_data)
        
    except TelegramError as e:
        # Отслеживаем ошибку Telegram API
        errors_total.labels(error_type='telegram_error', endpoint='POST /api/chats').inc()
        # Graceful Degradation: пытаемся вернуть кэшированные данные
        logger.warning(f"[API] Ошибка Telegram API при получении списка чатов, пытаемся вернуть кэш")
        try:
            user_id = request.get_json().get('user_id', 'unknown')
            cache_key = f"chats_{user_id}"
        except:
            cache_key = "chats_unknown"
        cached_data = cache.get(cache_key)
        if cached_data:
            cache_operations_total.labels(operation='get', status='hit').inc()
            logger.info(f"[API] Возвращаем кэшированные данные (Graceful Degradation)")
            cached_data['cached'] = True  # Помечаем, что данные из кэша
            cached_data['warning'] = 'Telegram API временно недоступен. Показаны кэшированные данные.'
            return jsonify(cached_data)
        
        # Если кэша нет, возвращаем ошибку
        from bot.exceptions import handle_telegram_error, get_user_friendly_message
        telegram_error = handle_telegram_error(e)
        user_message = get_user_friendly_message(telegram_error)
        logger.error(f"[API] Ошибка Telegram API при получении списка чатов: {user_message}")
        return jsonify({
            'success': False,
            'error': user_message
        }), 503  # Service Unavailable для ошибок Telegram API
    except Exception as e:
        # Отслеживаем общую ошибку
        errors_total.labels(error_type='general_error', endpoint='POST /api/chats').inc()
        # Graceful Degradation: пытаемся вернуть кэшированные данные
        logger.warning(f"[API] Ошибка при получении списка чатов, пытаемся вернуть кэш: {e}")
        try:
            user_id = request.get_json().get('user_id', 'unknown')
            cache_key = f"chats_{user_id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                cache_operations_total.labels(operation='get', status='hit').inc()
                logger.info(f"[API] Возвращаем кэшированные данные (Graceful Degradation)")
                cached_data['cached'] = True
                cached_data['warning'] = 'Произошла ошибка при загрузке данных. Показаны кэшированные данные.'
                return jsonify(cached_data)
            else:
                cache_operations_total.labels(operation='get', status='miss').inc()
        except:
            pass  # Игнорируем ошибки при попытке получить кэш
        
        logger.error(f"[API] Ошибка при получении списка чатов: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Не удалось загрузить список чатов'
        }), 500


@app.route('/api/chats/<chat_id>/members', methods=['POST'])
@limiter.limit("20 per minute")  # 20 запросов в минуту
@validate_path_param('chat_id', ChatIdPath)
@validate_request(ChatMembersRequest)
@track_request_metrics
def get_chat_members(chat_id, validated_data):
    """API endpoint для получения списка участников чата"""
    try:
        # Используем валидированные данные
        init_data = validated_data.init_data
        user_id = validated_data.user_id
        force_refresh = validated_data.force_refresh
        
        correlation_id = get_correlation_id()
        logger.info(f"[API] GET /api/chats/{chat_id}/members - запрос от пользователя {user_id}, force_refresh={force_refresh} (correlation_id: {correlation_id[:8] if correlation_id else 'none'})")
        
        if not user_id:
            logger.warning(f"[API] GET /api/chats/{chat_id}/members - User ID не предоставлен")
            return jsonify({
                'success': False,
                'error': 'User ID не предоставлен'
            }), 400
        
        # Валидация данных Mini App
        if not validate_telegram_webapp_data(init_data):
            logger.warning(f"[API] Невалидные данные WebApp от пользователя {user_id} для чата {chat_id}")
            return jsonify({
                'success': False,
                'error': 'Невалидные данные WebApp. Проверка подписи не пройдена.'
            }), 401
        
        # Проверяем кэш (если не требуется принудительное обновление)
        cache_key = f"members_{chat_id}_{user_id}"
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                cache_operations_total.labels(operation='get', status='hit').inc()
                logger.info(f"[API] Возвращаем кэшированные данные участников для чата {chat_id}, пользователя {user_id}")
                return jsonify(cached_data)
            else:
                cache_operations_total.labels(operation='get', status='miss').inc()
        
        bot = get_bot()  # Используем глобальный экземпляр бота
        from bot.services.chat_service import ChatService
        chat_service = ChatService(bot)
        
        # Отслеживаем время выполнения Telegram API запросов
        start_time = time.time()
        
        # Проверяем права пользователя и бота
        async def check_and_get_members():
            # Инициализируем бота перед использованием
            await bot.initialize()
            # Проверяем, является ли пользователь создателем
            is_user_creator = await chat_service.is_user_creator(chat_id, user_id)
            logger.info(f"[API] Чат {chat_id}: пользователь {user_id} создатель = {is_user_creator}")
        
            if not is_user_creator:
                return None, "Пользователь не является создателем группы"
            
            # Проверяем, является ли бот администратором
            is_bot_admin = await chat_service.is_bot_admin(chat_id)
            logger.info(f"[API] Чат {chat_id}: бот админ = {is_bot_admin}")
            
            if not is_bot_admin:
                return None, "Бот не является администратором группы"
            
            # Получаем список участников
            members = await chat_service.get_chat_members_list(chat_id)
            logger.info(f"[API] Получено {len(members)} участников для чата {chat_id}")
            
            # Формируем полные URL для фото профиля
            logger.info(f"[API] Формирование URL для {len(members)} участников")
            
            for member in members:
                if member.get('profile_photo_url'):
                    # Формируем полный URL для доступа к файлу через Telegram Bot API
                    file_path = member['profile_photo_url']
                    full_url = f"https://api.telegram.org/file/bot{Config.TOKEN}/{file_path}"
                    member['profile_photo_url'] = full_url
                    logger.info(f"[API] Участник {member.get('id')} ({member.get('first_name')}): фото URL = {full_url}")
                else:
                    logger.info(f"[API] Участник {member.get('id')} ({member.get('first_name')}): нет фото профиля")
            
            return members, None
        
        # Запускаем async функцию через утилиту
        from bot.utils.async_loop import run_async
        try:
            members, error = run_async(check_and_get_members())
            
            if error:
                # Отслеживаем ошибки, возвращенные функцией (например, недостаточно прав)
                telegram_api_requests_total.labels(method='POST /api/chats/{id}/members', status='error').inc()
                telegram_api_request_duration_seconds.labels(method='POST /api/chats/{id}/members').observe(time.time() - start_time)
                errors_total.labels(error_type='authorization_error', endpoint='POST /api/chats/{id}/members').inc()
                logger.warning(f"[API] GET /api/chats/{chat_id}/members - ошибка: {error}")
                return jsonify({
                    'success': False,
                    'error': error
                }), 403
            
            # Отслеживаем успешные запросы к Telegram API
            telegram_api_requests_total.labels(method='POST /api/chats/{id}/members', status='success').inc()
            telegram_api_request_duration_seconds.labels(method='POST /api/chats/{id}/members').observe(time.time() - start_time)
        except TelegramError as e:
            # Отслеживаем ошибки Telegram API
            telegram_api_requests_total.labels(method='POST /api/chats/{id}/members', status='error').inc()
            telegram_api_request_duration_seconds.labels(method='POST /api/chats/{id}/members').observe(time.time() - start_time)
            errors_total.labels(error_type='telegram_error', endpoint='POST /api/chats/{id}/members').inc()
            raise
        except Exception as e:
            # Отслеживаем общие ошибки
            errors_total.labels(error_type='general_error', endpoint='POST /api/chats/{id}/members').inc()
            raise
        
        logger.info(f"[API] GET /api/chats/{chat_id}/members - успешно возвращено {len(members)} участников")
        
        response_data = {
            'success': True,
            'members': members
        }
        
        # Сохраняем в кэш на 15 минут (900 секунд)
        cache.set(cache_key, response_data, timeout=900)
        cache_operations_total.labels(operation='set', status='success').inc()
        cache_size.labels(cache_type='members').set(cache.get_cache_info().currsize)
        logger.info(f"[API] Данные участников сохранены в кэш для чата {chat_id}, пользователя {user_id}")
        
        return jsonify(response_data)
        
    except TelegramError as e:
        # Graceful Degradation: пытаемся вернуть кэшированные данные
        logger.warning(f"[API] Ошибка Telegram API при получении участников чата {chat_id}, пытаемся вернуть кэш")
        cached_data = cache.get(cache_key)
        if cached_data:
            cache_operations_total.labels(operation='get', status='hit').inc()
            logger.info(f"[API] Возвращаем кэшированные данные участников для чата {chat_id} (Graceful Degradation)")
            cached_data['cached'] = True  # Помечаем, что данные из кэша
            cached_data['warning'] = 'Telegram API временно недоступен. Показаны кэшированные данные.'
            return jsonify(cached_data)
        
        # Если кэша нет, возвращаем ошибку
        from bot.exceptions import handle_telegram_error, get_user_friendly_message
        telegram_error = handle_telegram_error(e, context=f"chat_id={chat_id}, user_id={user_id}")
        user_message = get_user_friendly_message(telegram_error)
        logger.error(f"[API] Ошибка Telegram API при получении участников чата {chat_id}: {user_message}")
        return jsonify({
            'success': False,
            'error': user_message
        }), 503  # Service Unavailable для ошибок Telegram API
    except Exception as e:
        # Graceful Degradation: пытаемся вернуть кэшированные данные
        logger.warning(f"[API] Ошибка при получении участников чата {chat_id}, пытаемся вернуть кэш: {e}")
        cached_data = cache.get(cache_key)
        if cached_data:
            cache_operations_total.labels(operation='get', status='hit').inc()
            logger.info(f"[API] Возвращаем кэшированные данные участников для чата {chat_id} (Graceful Degradation)")
            cached_data['cached'] = True
            cached_data['warning'] = 'Произошла ошибка при загрузке данных. Показаны кэшированные данные.'
            return jsonify(cached_data)
        
        logger.error(f"[API] Ошибка при получении участников чата {chat_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Не удалось загрузить список участников'
        }), 500


@app.route('/metrics')
def metrics():
    """Endpoint для Prometheus метрик."""
    from webapp.metrics import get_metrics
    return get_metrics()


@app.route('/health')
def health():
    """
    Расширенный health check endpoint.
    Проверяет состояние приложения, Telegram API, хранилища и ресурсов.
    """
    from bot.utils.async_loop import run_async
    
    # Опциональный импорт psutil для проверки ресурсов
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
    
    health_status = {
        'status': 'ok',
        'timestamp': int(time.time()),
        'version': APP_VERSION,
        'checks': {}
    }
    
    overall_healthy = True
    
    # Проверка Telegram API
    try:
        async def check_telegram_api():
            bot = get_bot()
            me = await bot.get_me()
            return {
                'available': True,
                'bot_id': me.id,
                'bot_username': me.username
            }
        
        telegram_check = run_async(check_telegram_api())
        health_status['checks']['telegram_api'] = telegram_check
    except Exception as e:
        logger.warning(f"Health check: Telegram API недоступен: {e}")
        health_status['checks']['telegram_api'] = {
            'available': False,
            'error': str(e)
        }
        overall_healthy = False
    
    # Проверка хранилища чатов
    try:
        all_chats = chat_storage.get_all_chats()
        stats = chat_storage.get_stats()
        health_status['checks']['storage'] = {
            'available': True,
            'total_chats': len(all_chats),
            'stats': stats
        }
    except Exception as e:
        logger.warning(f"Health check: Ошибка доступа к хранилищу: {e}")
        health_status['checks']['storage'] = {
            'available': False,
            'error': str(e)
        }
        overall_healthy = False
    
    # Проверка памяти и ресурсов
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # Конвертируем в MB
            memory_mb = memory_info.rss / 1024 / 1024
            
            health_status['checks']['resources'] = {
                'available': True,
                'memory_mb': round(memory_mb, 2),
                'cpu_percent': round(cpu_percent, 2),
                'threads': process.num_threads()
            }
            
            # Предупреждение, если память превышает 500MB
            if memory_mb > 500:
                health_status['checks']['resources']['warning'] = 'Высокое использование памяти'
                overall_healthy = False
        except Exception as e:
            logger.warning(f"Health check: Ошибка проверки ресурсов: {e}")
            health_status['checks']['resources'] = {
                'available': False,
                'error': str(e)
            }
    else:
        # psutil не установлен, пропускаем проверку ресурсов
        health_status['checks']['resources'] = {
            'available': False,
            'error': 'psutil не установлен (опциональная зависимость)'
        }
    
    # Проверка конфигурации
    try:
        Config.validate()
        health_status['checks']['config'] = {
            'valid': True
        }
    except Exception as e:
        logger.warning(f"Health check: Ошибка конфигурации: {e}")
        health_status['checks']['config'] = {
            'valid': False,
            'error': str(e)
        }
        overall_healthy = False
    
    # Устанавливаем общий статус
    if not overall_healthy:
        health_status['status'] = 'degraded'
    
    # Определяем HTTP статус код
    status_code = 200 if overall_healthy else 503
    
    return jsonify(health_status), status_code


# Глобальные обработчики исключений
@app.errorhandler(404)
def not_found_error(error):
    """Обработчик для 404 ошибок"""
    logger.warning(f"404 ошибка: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint не найден'
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработчик для 500 ошибок"""
    logger.error(f"500 ошибка: {error}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500
    # Для обычных запросов возвращаем HTML страницу ошибки
    # Если шаблон не найден, возвращаем простой текст
    try:
        return render_template('500.html'), 500
    except Exception:
        return '<h1>500 Internal Server Error</h1><p>Внутренняя ошибка сервера</p>', 500


@app.errorhandler(400)
def bad_request_error(error):
    """Обработчик для 400 ошибок"""
    logger.warning(f"400 ошибка: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Неверный запрос'
        }), 400
    return render_template('400.html'), 400


@app.errorhandler(403)
def forbidden_error(error):
    """Обработчик для 403 ошибок"""
    logger.warning(f"403 ошибка: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Доступ запрещен'
        }), 403
    return render_template('403.html'), 403


@app.errorhandler(429)
def ratelimit_error(error):
    """Обработчик для 429 ошибок (Rate Limit)"""
    logger.warning(f"429 ошибка (Rate Limit): {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Превышен лимит запросов. Попробуйте позже.'
        }), 429
    return render_template('429.html'), 429


@app.errorhandler(Exception)
def handle_exception(error):
    """Глобальный обработчик всех необработанных исключений"""
    logger.error(f"Необработанное исключение: {error}", exc_info=True)
    
    # Если это API запрос, возвращаем JSON
    if request.path.startswith('/api/'):
        # Определяем код статуса в зависимости от типа ошибки
        status_code = 500
        error_message = 'Внутренняя ошибка сервера'
        
        if isinstance(error, TelegramError):
            # Обрабатываем TelegramError через наш обработчик
            telegram_error = handle_telegram_error(error)
            error_message = get_user_friendly_message(telegram_error)
            status_code = 503  # Service Unavailable
        elif isinstance(error, TelegramAPIError):
            # Уже обработанная ошибка
            error_message = get_user_friendly_message(error)
            status_code = 503
        elif isinstance(error, ValueError):
            status_code = 400
            error_message = str(error) or 'Неверные данные'
        elif isinstance(error, PermissionError):
            status_code = 403
            error_message = 'Доступ запрещен'
        
        return jsonify({
            'success': False,
            'error': error_message
        }), status_code
    
    # Для API endpoints возвращаем JSON, для остальных - HTML страницу ошибки
    if request.path.startswith('/api'):
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500
    
    # Для обычных запросов возвращаем HTML страницу ошибки
    # Если шаблон не найден, возвращаем простой текст
    try:
        return render_template('500.html'), 500
    except Exception:
        return '<h1>500 Internal Server Error</h1><p>Внутренняя ошибка сервера</p>', 500


def run_webapp():
    """Запуск веб-приложения"""
    app.run(
        host=Config.WEBAPP_HOST,
        port=Config.WEBAPP_PORT,
        debug=False
    )


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
@limiter.limit("5 per minute")  # 5 запросов в минуту для удаления
def delete_chat(chat_id: str):
    """API endpoint для удаления чата из списка"""
    # Преобразуем chat_id в int (поддерживаем отрицательные числа)
    try:
        chat_id = int(chat_id)
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'Некорректный ID чата'
        }), 400
    """API endpoint для удаления чата из списка"""
    correlation_id = get_correlation_id()
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        init_data = data.get('init_data', '')
        
        logger.info(f"[API] DELETE /api/chats/{chat_id} - запрос от пользователя {user_id} (correlation_id: {correlation_id[:8] if correlation_id else 'none'})")
        
        if not user_id:
            logger.warning(f"[API] DELETE /api/chats/{chat_id} - User ID не предоставлен")
            return jsonify({
                'success': False,
                'error': 'User ID не предоставлен'
            }), 400
        
        # Валидация данных Mini App
        if not validate_telegram_webapp_data(init_data):
            logger.warning(f"[API] Невалидные данные WebApp от пользователя {user_id}")
            return jsonify({
                'success': False,
                'error': 'Невалидные данные WebApp. Проверка подписи не пройдена.'
            }), 401
        
        # Проверяем, что пользователь является создателем чата
        bot = get_bot()
        from bot.services.chat_service import ChatService
        chat_service = ChatService(bot)
        
        # Отслеживаем время выполнения
        start_time = time.time()
        
        async def check_and_delete():
            # Проверяем права пользователя
            is_user_creator = await chat_service.is_user_creator(chat_id, user_id)
            if not is_user_creator:
                logger.warning(f"[API] Пользователь {user_id} не является создателем чата {chat_id}")
                return False, "Вы не являетесь создателем этого чата"
            
            # Удаляем чат из хранилища
            success = chat_storage.remove_chat(chat_id)
            if not success:
                return False, "Чат не найден в хранилище"
            
            # Инвалидируем кэш
            cache_key = f"chats_{user_id}"
            cache.delete(cache_key)
            cache.delete(f"members_{chat_id}_{user_id}")
            cache_operations_total.labels(operation='delete', status='success').inc()
            cache_operations_total.labels(operation='delete', status='success').inc()
            
            return True, None
        
        try:
            from bot.utils.async_loop import run_async
            success, error_message = run_async(check_and_delete())
            
            if not success:
                # Отслеживаем ошибки авторизации
                telegram_api_requests_total.labels(method='DELETE /api/chats/{id}', status='error').inc()
                telegram_api_request_duration_seconds.labels(method='DELETE /api/chats/{id}').observe(time.time() - start_time)
                errors_total.labels(error_type='authorization_error', endpoint='DELETE /api/chats/{id}').inc()
                logger.warning(f"[API] Ошибка при удалении чата {chat_id}: {error_message}")
                return jsonify({
                    'success': False,
                    'error': error_message
                }), 403
            
            # Отслеживаем успешные запросы
            telegram_api_requests_total.labels(method='DELETE /api/chats/{id}', status='success').inc()
            telegram_api_request_duration_seconds.labels(method='DELETE /api/chats/{id}').observe(time.time() - start_time)
            
            logger.info(f"[API] Чат {chat_id} успешно удален пользователем {user_id}")
            return jsonify({
                'success': True,
                'message': 'Чат успешно удален из списка'
            })
        except TelegramError as e:
            # Отслеживаем ошибки Telegram API
            telegram_api_requests_total.labels(method='DELETE /api/chats/{id}', status='error').inc()
            telegram_api_request_duration_seconds.labels(method='DELETE /api/chats/{id}').observe(time.time() - start_time)
            errors_total.labels(error_type='telegram_error', endpoint='DELETE /api/chats/{id}').inc()
            raise
        except Exception as e:
            # Отслеживаем общие ошибки
            errors_total.labels(error_type='general_error', endpoint='DELETE /api/chats/{id}').inc()
            raise
        
    except TelegramError as e:
        from bot.exceptions import handle_telegram_error, get_user_friendly_message
        telegram_error = handle_telegram_error(e)
        user_message = get_user_friendly_message(telegram_error)
        logger.error(f"[API] Ошибка Telegram API при удалении чата {chat_id}: {user_message}")
        return jsonify({
            'success': False,
            'error': user_message
        }), 503
    except Exception as e:
        logger.error(f"[API] Ошибка при удалении чата {chat_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Не удалось удалить чат'
        }), 500


if __name__ == '__main__':
    run_webapp()

