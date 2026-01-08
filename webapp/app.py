"""Flask приложение для Mini App"""
import logging
import time
import json
from typing import Optional, Dict, Any
from functools import wraps
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from telegram.error import TelegramError
from pydantic import ValidationError

from bot.config import Config
from bot.services.chat_storage_service import chat_storage
from bot.infrastructure.telegram_client import get_telegram_client
from bot.utils.webapp_validator import validate_telegram_webapp_data, parse_webapp_data
from bot.utils.errors import handle_telegram_error, get_user_friendly_message
from bot.utils.retry import retry_async, RetryConfig
from bot.utils.cache import get_cache
from bot.utils.async_helpers import run_async_safe
from bot.utils.batching import batch_process_with_filter
from webapp.validators import ChatListRequest, ChatMembersRequest, validate_chat_id

try:
    import sass  # type: ignore
except ImportError:  # pragma: no cover - опциональная зависимость
    sass = None

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.WEBAPP_SECRET_KEY


def _compile_scss() -> None:
    """
    Компилирует SCSS в CSS при старте приложения.
    Если libsass недоступен, просто логируем предупреждение.
    """
    if sass is None:
        logger.warning("SCSS не скомпилирован: пакет 'libsass' не установлен")
        return

    try:
        import pathlib

        base_dir = pathlib.Path(__file__).resolve().parent
        scss_dir = base_dir / "static" / "scss"
        scss_path = scss_dir / "style.scss"
        css_path = base_dir / "static" / "css" / "style.css"

        # libsass требует include_paths для правильной работы @import
        css = sass.compile(
            filename=str(scss_path),
            include_paths=[str(scss_dir)]
        )
        css_path.write_text(css, encoding="utf-8")
        logger.info(f"SCSS успешно скомпилирован в {css_path}")
    except Exception as e:  # pragma: no cover - защитный код
        logger.error(f"Ошибка компиляции SCSS: {e}", exc_info=True)


_compile_scss()

# Метрики производительности
_metrics = {
    'api_requests': {},
    'api_response_times': []
}

def track_metrics(endpoint_name: str):
    """Декоратор для отслеживания метрик производительности"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Обновляем метрики
                if endpoint_name not in _metrics['api_requests']:
                    _metrics['api_requests'][endpoint_name] = 0
                _metrics['api_requests'][endpoint_name] += 1
                
                _metrics['api_response_times'].append({
                    'endpoint': endpoint_name,
                    'response_time': response_time,
                    'timestamp': time.time(),
                    'status': 'success'
                })
                
                # Храним только последние 1000 записей
                if len(_metrics['api_response_times']) > 1000:
                    _metrics['api_response_times'] = _metrics['api_response_times'][-1000:]
                
                logger.debug(f"[Metrics] {endpoint_name}: {response_time:.3f}s")
                return result
            except Exception as e:
                response_time = time.time() - start_time
                _metrics['api_response_times'].append({
                    'endpoint': endpoint_name,
                    'response_time': response_time,
                    'timestamp': time.time(),
                    'status': 'error',
                    'error': str(e)
                })
                raise
        return wrapper
    return decorator

# Настройка CORS - разрешаем только запросы от Telegram WebApp
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Telegram WebApp может приходить с разных доменов
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Настройка Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # In-memory storage (можно заменить на Redis)
)

# Версия для cache busting
APP_VERSION = str(int(time.time()))

# TelegramClient теперь управляется через get_telegram_client()
# Удалено: глобальный Bot экземпляр заменен на TelegramClient




@app.route('/')
def index():
    """Главная страница Mini App"""
    return render_template('index.html', version=APP_VERSION)


@app.route('/members')
def members_page():
    """Страница участников чата"""
    logger.info("[API] GET /members - запрос страницы участников")
    return render_template('members.html', version=APP_VERSION)


@app.after_request
def add_security_headers(response):
    """
    Добавляет security headers и заголовки для предотвращения кэширования.
    
    Security headers:
    - Content-Security-Policy: ограничивает источники контента
    - X-Frame-Options: предотвращает clickjacking
    - X-Content-Type-Options: предотвращает MIME-sniffing
    - Referrer-Policy: контролирует передачу referrer
    - Permissions-Policy: ограничивает доступ к API браузера
    """
    # Security headers для всех ответов
    # CSP для Telegram WebApp - разрешаем только необходимые источники
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://telegram.org https://unpkg.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https://api.telegram.org; "
        "frame-src 'self' https://telegram.org; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self' https://telegram.org; "
        "upgrade-insecure-requests;"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Предотвращение clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Предотвращение MIME-sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Контроль referrer
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy (ограничение доступа к API браузера)
    response.headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=(), '
        'payment=(), '
        'usb=()'
    )
    
    # Заголовки для предотвращения кэширования (только для HTML страниц)
    if request.endpoint == 'static' or request.endpoint == 'index' or request.endpoint == 'members_page':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    else:
        # Для API endpoints - короткое кэширование
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    
    return response


@app.errorhandler(429)
def handle_rate_limit(e):
    """Обработчик ошибок rate limiting"""
    logger.warning(f"Rate limit exceeded: {e}")
    return jsonify({
        'success': False,
        'error': 'Превышен лимит запросов. Попробуйте позже.'
    }), 429


@app.errorhandler(ValidationError)
def handle_validation_error(e: ValidationError):
    """Обработчик ошибок валидации pydantic"""
    logger.warning(f"Validation error: {e}")
    return jsonify({
        'success': False,
        'error': 'Ошибка валидации данных',
        'details': e.errors()
    }), 400


@app.errorhandler(404)
def handle_not_found(e):
    """Обработчик 404 ошибок"""
    # Для API endpoints возвращаем JSON
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint не найден'
        }), 404
    # Для остальных - стандартная обработка Flask
    return f"Страница не найдена: {request.path}", 404


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    """Глобальный обработчик исключений"""
    # Пропускаем 404 ошибки - они обрабатываются отдельно
    from werkzeug.exceptions import NotFound
    if isinstance(e, NotFound):
        raise  # Пробрасываем дальше для обработки handle_not_found
    
    logger.error(f"Необработанное исключение: {e}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'Внутренняя ошибка сервера'
    }), 500


@app.route('/api/chats', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limiting: 10 запросов в минуту
@track_metrics('get_chats')
def get_chats():
    """API endpoint для получения списка чатов"""
    try:
        data = request.get_json() or {}
        
        # Валидация данных через pydantic
        try:
            validated_data = ChatListRequest(**data)
            user_id = validated_data.user_id
            init_data = validated_data.init_data
            page = validated_data.page
            per_page = validated_data.per_page
        except ValidationError as e:
            logger.warning(f"[API] POST /api/chats - ошибка валидации: {e}")
            return jsonify({
                'success': False,
                'error': 'Невалидные данные запроса',
                'details': e.errors()
            }), 400
        
        # Дополнительная валидация WebApp данных
        if not validate_telegram_webapp_data(init_data):
            logger.warning(f"[API] POST /api/chats - невалидные данные WebApp от пользователя {user_id}")
            return jsonify({
                'success': False,
                'error': 'Невалидные данные WebApp'
            }), 400
        
        logger.info(f"[API] POST /api/chats - запрос от пользователя {user_id}")
        
        cache = get_cache()
        cache_key = f"chats:{user_id}"
        
        # Проверяем кэш
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"[API] Возвращаем кэшированные данные для пользователя {user_id}")
            return jsonify(cached_result)
        
        telegram_client = get_telegram_client()
        from bot.services.chat_service import ChatService
        
        all_chat_ids = set()
        filtered_chats = []
        skipped_not_admin = 0
        skipped_not_creator = 0
        skipped_not_group = 0
        use_cached_on_error = False
        
        async def get_chats_from_telegram():
            nonlocal all_chat_ids, filtered_chats, skipped_not_admin, skipped_not_creator, skipped_not_group
            
            try:
                # Инициализируем клиент перед использованием
                await telegram_client.initialize()
                chat_service = ChatService(telegram_client.bot)
                
                # Получаем чаты только из хранилища
                stored_chats = chat_storage.get_all_chats()
                logger.info(f"[API] Чатов в хранилище: {len(stored_chats)}")
                
                for stored_chat in stored_chats:
                    all_chat_ids.add(stored_chat['id'])
                
                logger.info(f"[API] Всего чатов для проверки: {len(all_chat_ids)}")
                
                # Если нет чатов, выводим предупреждение
                if len(all_chat_ids) == 0:
                    logger.warning("[API] ВНИМАНИЕ: Не найдено чатов в хранилище!")
                    logger.warning("[API] Чаты будут появляться автоматически при:")
                    logger.warning("[API] 1. Получении сообщений в группах")
                    logger.warning("[API] 2. Добавлении бота в группы (событие my_chat_member)")
                    logger.warning("[API] 3. Использовании команды /register в группе")
                
                # Retry конфигурация для операций с Telegram API
                retry_config = RetryConfig(
                    max_attempts=3,
                    initial_delay=1.0,
                    max_delay=10.0
                )
                
                # Функция-процессор для обработки одного чата
                async def process_chat(chat_id: int):
                    """Обрабатывает один чат и возвращает данные или None"""
                    nonlocal skipped_not_group, skipped_not_admin, skipped_not_creator
                    try:
                        # Получаем информацию о чате через TelegramClient (с встроенным retry)
                        chat = await telegram_client.get_chat(chat_id)
                        
                        # Пропускаем, если это не группа или супергруппа
                        if chat.type not in ['group', 'supergroup']:
                            skipped_not_group += 1
                            return None
                        
                        chat_title = chat.title or 'Без названия'
                        logger.debug(f"[API] Проверка чата {chat_id} ({chat_title}, {chat.type})")
                        
                        # Проверяем, является ли бот администратором (с retry)
                        is_bot_admin = await retry_async(
                            chat_service.is_bot_admin,
                            chat_id,
                            config=retry_config
                        )
                        logger.debug(f"[API] Чат {chat_id}: бот админ = {is_bot_admin}")
                        
                        if not is_bot_admin:
                            skipped_not_admin += 1
                            logger.debug(f"[API] Чат {chat_id} пропущен: бот не является администратором")
                            return None
                        
                        # Проверяем, является ли пользователь создателем (с retry)
                        is_user_creator = await retry_async(
                            chat_service.is_user_creator,
                            chat_id,
                            user_id,
                            config=retry_config
                        )
                        logger.debug(f"[API] Чат {chat_id}: пользователь {user_id} создатель = {is_user_creator}")
                        
                        if not is_user_creator:
                            skipped_not_creator += 1
                            logger.debug(f"[API] Чат {chat_id} пропущен: пользователь {user_id} не является создателем")
                            return None
                        
                        # Получаем фото чата (если есть) - ленивая загрузка, пропускаем для оптимизации
                        # Фото можно загружать отдельно при необходимости
                        chat_photo_url = None
                        
                        # Формируем данные чата
                        chat_data = {
                            'id': chat.id,
                            'title': chat.title or 'Без названия',
                            'type': chat.type,
                            'username': getattr(chat, 'username', None),
                            'members_count': getattr(chat, 'members_count', None),
                            'photo_url': None
                        }
                        
                        # Сохраняем в хранилище
                        chat_storage.register_chat(chat)
                        
                        logger.debug(f"[API] Чат {chat_id} добавлен в результат")
                        return chat_data
                        
                    except TelegramError as e:
                        # Обрабатываем ошибки Telegram API
                        handled_error = handle_telegram_error(e, f"chat_id={chat_id}")
                        logger.debug(f"[API] Не удалось получить информацию о чате {chat_id}: {handled_error}")
                        return None
                    except Exception as e:
                        logger.error(f"[API] Ошибка при обработке чата {chat_id}: {e}", exc_info=True)
                        return None
                
                # Обрабатываем чаты параллельно с ограничением (максимум 5 одновременных запросов)
                # Это значительно ускорит обработку большого количества чатов
                chat_list = list(all_chat_ids)
                logger.info(f"[API] Начинаем параллельную обработку {len(chat_list)} чатов (max_concurrent=5)")
                
                processed_chats = await batch_process_with_filter(
                    items=chat_list,
                    processor=process_chat,
                    max_concurrent=5,  # Ограничение для избежания rate limits
                    error_handler=lambda chat_id, e: logger.warning(
                        f"[API] Ошибка при батч-обработке чата {chat_id}: {e}"
                    )
                )
                
                filtered_chats.extend(processed_chats)
                logger.info(f"[API] Параллельная обработка завершена: обработано {len(processed_chats)} чатов")
                        
            except Exception as e:
                logger.error(f"[API] Ошибка при получении чатов: {e}", exc_info=True)
                raise
        
        # Запускаем async функцию через безопасный helper
        try:
            run_async_safe(get_chats_from_telegram())
        except Exception as e:
            logger.error(f"[API] Ошибка при получении чатов: {e}", exc_info=True)
            # Graceful degradation: пытаемся вернуть кэшированные данные
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.warning(f"[API] Используем кэшированные данные из-за ошибки API")
                cached_result['cached'] = True
                cached_result['warning'] = 'Данные могут быть устаревшими из-за ошибки API'
                return jsonify(cached_result)
            raise
        
        logger.info(f"[API] Результат фильтрации: {len(filtered_chats)} чатов")
        logger.info(f"[API] Пропущено (не группа): {skipped_not_group}, "
                   f"(бот не админ): {skipped_not_admin}, "
                   f"(пользователь не создатель): {skipped_not_creator}")
        
        # Подсчитываем статистику
        stats = {
            'total': len(filtered_chats),
            'groups': len([c for c in filtered_chats if c['type'] == 'group']),
            'supergroups': len([c for c in filtered_chats if c['type'] == 'supergroup']),
            'private': 0,
            'channels': 0
        }
        
        # Получаем параметры сортировки из запроса
        sort_by = data.get('sort_by', 'title')  # title, members_count, type
        sort_order = data.get('sort_order', 'asc')  # asc, desc
        
        # Сортировка
        if sort_by == 'title':
            filtered_chats.sort(key=lambda x: x['title'].lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'members_count':
            filtered_chats.sort(key=lambda x: x.get('members_count', 0) or 0, reverse=(sort_order == 'desc'))
        elif sort_by == 'type':
            filtered_chats.sort(key=lambda x: x['type'], reverse=(sort_order == 'desc'))
        else:
            # По умолчанию по названию
            filtered_chats.sort(key=lambda x: x['title'].lower())
        
        # Пагинация
        total_chats = len(filtered_chats)
        total_pages = (total_chats + per_page - 1) // per_page if total_chats > 0 else 1
        
        # Проверяем, что запрошенная страница существует
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        # Вычисляем индексы для среза
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Получаем чаты для текущей страницы
        paginated_chats = filtered_chats[start_idx:end_idx]
        
        # Метаданные пагинации
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_chats,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
        
        # Добавляем информационное сообщение, если чатов нет
        info_message = None
        if len(filtered_chats) == 0 and len(all_chat_ids) == 0:
            info_message = (
                "Чаты не найдены. Telegram Bot API не предоставляет способ получить список всех чатов.\n\n"
                "Чаты будут автоматически регистрироваться при:\n"
                "• Получении любого сообщения в группе\n"
                "• Добавлении бота в группу (событие my_chat_member)\n"
                "• Использовании команды /register в группе\n\n"
                "Отправьте любое сообщение в группе или используйте /register для регистрации."
            )
        
        logger.info(f"[API] POST /api/chats - страница {page}/{total_pages}, возвращено {len(paginated_chats)} из {total_chats} чатов")
        
        response_data = {
            'success': True,
            'chats': paginated_chats,
            'stats': stats,
            'pagination': pagination
        }
        
        if info_message:
            response_data['info'] = info_message
        
        # Сохраняем в кэш (TTL: 5 минут)
        # ВАЖНО: кэшируем полный список, а не только текущую страницу
        cache_data = {
            'success': True,
            'chats': filtered_chats,  # Полный список для кэша
            'stats': stats,
            'pagination': {
                'total': total_chats,
                'total_pages': total_pages
            }
        }
        cache.set(cache_key, cache_data, ttl=300.0)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"[API] Ошибка при получении списка чатов: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Не удалось загрузить список чатов'
        }), 500


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
@limiter.limit("10 per minute")  # Rate limiting: 10 запросов в минуту
@track_metrics('delete_chat')
def delete_chat(chat_id: str):
    """API endpoint для удаления чата из списка"""
    try:
        chat_id_int = validate_chat_id(chat_id)
    except ValueError as e:
        logger.warning(f"[API] DELETE /api/chats/{chat_id} - {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id не указан'
            }), 400
        
        # Удаляем чат из хранилища
        chat_storage.delete_chat(chat_id_int)
        
        # Инвалидируем кэш
        cache = get_cache()
        cache.invalidate_pattern(f"chats:{user_id}")
        cache.invalidate_pattern(f"members:{chat_id_int}:")
        
        logger.info(f"[API] Чат {chat_id_int} удален из списка пользователем {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Чат успешно удален из списка'
        })
    except Exception as e:
        logger.error(f"[API] Ошибка при удалении чата {chat_id_int}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Не удалось удалить чат'
        }), 500


@app.route('/api/chats/<chat_id>/members', methods=['POST'])
@limiter.limit("20 per minute")  # Rate limiting: 20 запросов в минуту
@track_metrics('get_chat_members')
def get_chat_members(chat_id: str):
    """API endpoint для получения списка участников чата"""
    # Валидация chat_id
    try:
        chat_id_int = validate_chat_id(chat_id)
    except ValueError as e:
        logger.warning(f"[API] POST /api/chats/{chat_id}/members - {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    try:
        data = request.get_json() or {}
        
        # Валидация данных через pydantic
        try:
            validated_data = ChatMembersRequest(**data)
            user_id = validated_data.user_id
        except ValidationError as e:
            logger.warning(f"[API] POST /api/chats/{chat_id_int}/members - ошибка валидации: {e}")
            return jsonify({
                'success': False,
                'error': 'Невалидные данные запроса',
                'details': e.errors()
            }), 400
        
        logger.info(f"[API] POST /api/chats/{chat_id_int}/members - запрос от пользователя {user_id}")
        
        cache = get_cache()
        cache_key = f"members:{chat_id_int}:{user_id}"
        
        # Проверяем кэш
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"[API] Возвращаем кэшированные данные участников для чата {chat_id_int}")
            return jsonify(cached_result)
        
        telegram_client = get_telegram_client()
        from bot.services.chat_service import ChatService
        chat_service = ChatService(telegram_client.bot)
        
        # Проверяем права пользователя и бота
        async def check_and_get_members():
            try:
                # Инициализируем клиент перед использованием
                await telegram_client.initialize()
                
                # Retry конфигурация для операций с Telegram API
                retry_config = RetryConfig(
                    max_attempts=3,
                    initial_delay=1.0,
                    max_delay=10.0
                )
                
                # Проверяем, является ли пользователь создателем (с retry)
                try:
                    is_user_creator = await retry_async(
                        chat_service.is_user_creator,
                        chat_id_int,
                        user_id,
                        config=retry_config
                    )
                    logger.debug(f"[API] Чат {chat_id_int}: пользователь {user_id} создатель = {is_user_creator}")
                except Exception as e:
                    logger.error(f"[API] Ошибка при проверке прав создателя (после retry): {e}", exc_info=True)
                    # При ошибке после retry возвращаем False
                    is_user_creator = False
                
                if not is_user_creator:
                    return None, "Пользователь не является создателем группы"
                
                # Проверяем, является ли бот администратором (с retry)
                try:
                    is_bot_admin = await retry_async(
                        chat_service.is_bot_admin,
                        chat_id_int,
                        config=retry_config
                    )
                    logger.debug(f"[API] Чат {chat_id_int}: бот админ = {is_bot_admin}")
                except Exception as e:
                    logger.error(f"[API] Ошибка при проверке прав бота (после retry): {e}", exc_info=True)
                    # При ошибке после retry возвращаем False
                    is_bot_admin = False
                
                if not is_bot_admin:
                    return None, "Бот не является администратором группы"
                
                # Получаем список участников
                members = await chat_service.get_chat_members_list(chat_id_int)
                logger.info(f"[API] Получено {len(members)} участников для чата {chat_id_int}")
                
                # Ленивая загрузка фото профиля - не загружаем сразу
                # Фото будет загружено на фронтенде при необходимости
                # Это оптимизирует время ответа API
                
                return members, None
            except TelegramError as e:
                handled_error = handle_telegram_error(e, f"chat_id={chat_id_int}, user_id={user_id}")
                error_msg = get_user_friendly_message(handled_error)
                logger.error(f"[API] Ошибка Telegram API: {error_msg}")
                return None, error_msg
            except Exception as e:
                logger.error(f"[API] Ошибка при получении участников: {e}", exc_info=True)
                return None, "Не удалось получить список участников"
        
        # Запускаем async функцию через безопасный helper
        try:
            members, error = run_async_safe(check_and_get_members())
        except Exception as e:
            logger.error(f"[API] Ошибка при получении участников: {e}", exc_info=True)
            # Graceful degradation: пытаемся вернуть кэшированные данные
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.warning(f"[API] Используем кэшированные данные участников из-за ошибки API")
                cached_result['cached'] = True
                cached_result['warning'] = 'Данные могут быть устаревшими из-за ошибки API'
                return jsonify(cached_result)
            raise
        
        if error:
            logger.warning(f"[API] POST /api/chats/{chat_id_int}/members - ошибка: {error}")
            # Пытаемся вернуть кэшированные данные при ошибке доступа
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.warning(f"[API] Используем кэшированные данные участников из-за ошибки доступа")
                cached_result['cached'] = True
                cached_result['warning'] = f'Данные могут быть устаревшими. Ошибка: {error}'
                return jsonify(cached_result)
            return jsonify({
                'success': False,
                'error': error
            }), 403
        
        logger.info(f"[API] POST /api/chats/{chat_id_int}/members - успешно возвращено {len(members)} участников")
        
        response_data = {
            'success': True,
            'members': members
        }
        
        # Сохраняем в кэш (TTL: 15 минут, участники меняются реже)
        cache.set(cache_key, response_data, ttl=900.0)
        
        return jsonify(response_data)
        
    except TelegramError as e:
        handled_error = handle_telegram_error(e, f"chat_id={chat_id_int}")
        error_msg = get_user_friendly_message(handled_error)
        logger.error(f"[API] Ошибка Telegram API при получении участников чата {chat_id_int}: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
    except Exception as e:
        logger.error(f"[API] Ошибка при получении участников чата {chat_id_int}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Не удалось загрузить список участников'
        }), 500


@app.route('/api/metrics')
def get_metrics():
    """Endpoint для получения метрик производительности"""
    # Вычисляем среднее время ответа по каждому endpoint
    avg_times = {}
    for metric in _metrics['api_response_times']:
        endpoint = metric['endpoint']
        if endpoint not in avg_times:
            avg_times[endpoint] = {'times': [], 'errors': 0}
        if metric['status'] == 'success':
            avg_times[endpoint]['times'].append(metric['response_time'])
        else:
            avg_times[endpoint]['errors'] += 1
    
    # Вычисляем средние значения
    metrics_summary = {}
    for endpoint, data in avg_times.items():
        if data['times']:
            metrics_summary[endpoint] = {
                'avg_response_time': sum(data['times']) / len(data['times']),
                'min_response_time': min(data['times']),
                'max_response_time': max(data['times']),
                'total_requests': len(data['times']) + data['errors'],
                'errors': data['errors'],
                'success_rate': len(data['times']) / (len(data['times']) + data['errors']) if (len(data['times']) + data['errors']) > 0 else 0
            }
    
    return jsonify({
        'requests': _metrics['api_requests'],
        'response_times': metrics_summary,
        'total_metrics': len(_metrics['api_response_times'])
    })

@app.route('/health')
def health():
    """Health check endpoint с расширенной проверкой"""
    import asyncio
    from bot.utils.cache import get_cache
    
    health_status = {
        'status': 'ok',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Проверка кэша
    try:
        cache = get_cache()
        cache_stats = cache.get_stats()
        health_status['checks']['cache'] = {
            'status': 'ok',
            'stats': cache_stats
        }
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'error',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Проверка Telegram API
    try:
        telegram_client = get_telegram_client()
        
        async def check_telegram_api():
            try:
                # Используем TelegramClient для получения информации о боте
                bot_info = await telegram_client.get_me()
                return {'status': 'ok', 'bot_id': bot_info.id, 'bot_username': bot_info.username}
            except Exception as e:
                return {'status': 'error', 'error': str(e)}
        
        telegram_check = run_async_safe(check_telegram_api())
        health_status['checks']['telegram_api'] = telegram_check
        
        if telegram_check['status'] != 'ok':
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['telegram_api'] = {
            'status': 'error',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Проверка хранилища чатов
    try:
        stats = chat_storage.get_stats()
        health_status['checks']['chat_storage'] = {
            'status': 'ok',
            'total_chats': stats['total']
        }
    except Exception as e:
        health_status['checks']['chat_storage'] = {
            'status': 'error',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'ok' else 503
    return jsonify(health_status), status_code


def run_webapp():
    """Запуск веб-приложения"""
    app.run(
        host=Config.WEBAPP_HOST,
        port=Config.WEBAPP_PORT,
        debug=False
    )


if __name__ == '__main__':
    run_webapp()
