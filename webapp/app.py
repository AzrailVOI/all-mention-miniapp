"""Flask приложение для Mini App"""
import logging
import hmac
import hashlib
import json
from flask import Flask, render_template, request, jsonify
from telegram import Bot
from telegram.error import TelegramError

from bot.config import Config
from bot.services.chat_storage_service import chat_storage

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.TOKEN  # Используем токен бота как секретный ключ

# Версия для cache busting
import time
APP_VERSION = str(int(time.time()))  # Используем timestamp как версию


def validate_telegram_webapp_data(init_data: str) -> bool:
    """
    Валидирует данные от Telegram WebApp
    В продакшене нужно использовать более строгую валидацию
    """
    try:
        # Простая проверка наличия данных
        # В реальном приложении нужно проверять подпись через секретный ключ
        if not init_data:
            return False
        
        # Проверяем наличие обязательных полей
        if 'user' not in init_data and 'query_id' not in init_data:
            return False
        
        return True
    except Exception as e:
        logger.error(f"Ошибка валидации данных WebApp: {e}")
        return False


@app.route('/')
def index():
    """Главная страница Mini App"""
    return render_template('index.html', version=APP_VERSION)


@app.route('/members')
def members_page():
    """Страница участников чата"""
    logger.info(f"[API] GET /members - запрос страницы участников")
    print(f"[API] GET /members - запрос страницы участников")
    return render_template('members.html', version=APP_VERSION)


@app.after_request
def add_no_cache_headers(response):
    """Добавляет заголовки для предотвращения кэширования"""
    if request.endpoint == 'static' or request.endpoint == 'index':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


@app.route('/api/chats', methods=['POST'])
def get_chats():
    """API endpoint для получения списка чатов напрямую из Telegram API"""
    import asyncio
    try:
        data = request.get_json()
        init_data = data.get('init_data', '')
        user_id = data.get('user_id')
        
        logger.info(f"[API] GET /api/chats - запрос от пользователя {user_id}")
        print(f"[API] GET /api/chats - запрос от пользователя {user_id}")
        
        if not user_id:
            logger.warning(f"[API] GET /api/chats - User ID не предоставлен")
            print(f"[API] GET /api/chats - User ID не предоставлен")
            return jsonify({
                'success': False,
                'error': 'User ID не предоставлен'
            }), 400
        
        # Валидация данных Mini App
        if not validate_telegram_webapp_data(init_data):
            logger.warning(f"[API] Невалидные данные от пользователя {user_id}")
            print(f"[API] Невалидные данные от пользователя {user_id}")
        
        # Создаем бота
        bot = Bot(token=Config.TOKEN)
        from bot.services.chat_service import ChatService
        
        # НЕ используем getUpdates, так как он конфликтует с polling в основном потоке
        # Используем только хранилище чатов, которое заполняется при событиях
        all_chat_ids = set()
        filtered_chats = []
        skipped_not_admin = 0
        skipped_not_creator = 0
        skipped_not_group = 0
        
        async def get_chats_from_telegram():
            nonlocal all_chat_ids, filtered_chats, skipped_not_admin, skipped_not_creator, skipped_not_group
            
            try:
                # Инициализируем бота перед использованием
                await bot.initialize()
                chat_service = ChatService(bot)
                
                # Получаем чаты только из хранилища
                # getUpdates нельзя использовать параллельно с polling
                stored_chats = chat_storage.get_all_chats()
                logger.info(f"[API] Чатов в хранилище: {len(stored_chats)}")
                print(f"[API] Чатов в хранилище: {len(stored_chats)}")
                
                for stored_chat in stored_chats:
                    all_chat_ids.add(stored_chat['id'])
                
                logger.info(f"[API] Всего чатов для проверки: {len(all_chat_ids)}")
                print(f"[API] Всего чатов для проверки: {len(all_chat_ids)}")
                
                # Если нет чатов, выводим предупреждение
                if len(all_chat_ids) == 0:
                    logger.warning(f"[API] ВНИМАНИЕ: Не найдено чатов в хранилище!")
                    logger.warning(f"[API] Чаты будут появляться автоматически при:")
                    logger.warning(f"[API] 1. Получении сообщений в группах")
                    logger.warning(f"[API] 2. Добавлении бота в группы (событие my_chat_member)")
                    logger.warning(f"[API] 3. Использовании команды /register в группе")
                    print(f"[API] ВНИМАНИЕ: Не найдено чатов в хранилище!")
                    print(f"[API] Чаты будут появляться автоматически при получении сообщений или событий")
                
                # Проверяем каждый чат
                for chat_id in all_chat_ids:
                    try:
                        # Получаем информацию о чате
                        chat = await bot.get_chat(chat_id)
                        
                        # Пропускаем, если это не группа или супергруппа
                        if chat.type not in ['group', 'supergroup']:
                            skipped_not_group += 1
                            continue
                        
                        chat_title = chat.title or 'Без названия'
                        logger.info(f"[API] Проверка чата {chat_id} ({chat_title}, {chat.type})")
                        print(f"[API] Проверка чата {chat_id} ({chat_title}, {chat.type})")
                        
                        # Проверяем, является ли бот администратором
                        is_bot_admin = await chat_service.is_bot_admin(chat_id)
                        logger.info(f"[API] Чат {chat_id}: бот админ = {is_bot_admin}")
                        print(f"[API] Чат {chat_id}: бот админ = {is_bot_admin}")
                        
                        if not is_bot_admin:
                            skipped_not_admin += 1
                            logger.warning(f"[API] Чат {chat_id} пропущен: бот не является администратором")
                            print(f"[API] Чат {chat_id} пропущен: бот не является администратором")
                            continue
                        
                        # Проверяем, является ли пользователь создателем
                        is_user_creator = await chat_service.is_user_creator(chat_id, user_id)
                        logger.info(f"[API] Чат {chat_id}: пользователь {user_id} создатель = {is_user_creator}")
                        print(f"[API] Чат {chat_id}: пользователь {user_id} создатель = {is_user_creator}")
                        
                        if not is_user_creator:
                            skipped_not_creator += 1
                            logger.warning(f"[API] Чат {chat_id} пропущен: пользователь {user_id} не является создателем")
                            print(f"[API] Чат {chat_id} пропущен: пользователь {user_id} не является создателем")
                            continue
                        
                        # Формируем данные чата
                        chat_data = {
                            'id': chat.id,
                            'title': chat.title or 'Без названия',
                            'type': chat.type,
                            'username': getattr(chat, 'username', None),
                            'members_count': getattr(chat, 'members_count', None)
                        }
                        
                        filtered_chats.append(chat_data)
                        
                        # Сохраняем в хранилище
                        chat_storage.register_chat(chat)
                        
                        logger.info(f"[API] Чат {chat_id} добавлен в результат")
                        print(f"[API] Чат {chat_id} добавлен в результат")
                        
                    except TelegramError as e:
                        # Игнорируем ошибки доступа к чатам
                        logger.debug(f"[API] Не удалось получить информацию о чате {chat_id}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"[API] Ошибка при обработке чата {chat_id}: {e}")
                        print(f"[API] Ошибка при обработке чата {chat_id}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"[API] Ошибка при получении обновлений: {e}")
                print(f"[API] Ошибка при получении обновлений: {e}")
        
        # Запускаем async функцию
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(get_chats_from_telegram())
        
        # Закрываем бота после использования
        try:
            loop.run_until_complete(bot.shutdown())
        except:
            pass
        
        logger.info(f"[API] Результат фильтрации: {len(filtered_chats)} чатов")
        logger.info(f"[API] Пропущено (не группа): {skipped_not_group}, (бот не админ): {skipped_not_admin}, (пользователь не создатель): {skipped_not_creator}")
        print(f"[API] Результат фильтрации: {len(filtered_chats)} чатов")
        print(f"[API] Пропущено (не группа): {skipped_not_group}, (бот не админ): {skipped_not_admin}, (пользователь не создатель): {skipped_not_creator}")
        
        # Подсчитываем статистику
        stats = {
            'total': len(filtered_chats),
            'groups': len([c for c in filtered_chats if c['type'] == 'group']),
            'supergroups': len([c for c in filtered_chats if c['type'] == 'supergroup']),
            'private': 0,
            'channels': 0
        }
        
        # Сортируем чаты по названию
        filtered_chats.sort(key=lambda x: x['title'].lower())
        
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
        
        logger.info(f"[API] GET /api/chats - успешно возвращено {len(filtered_chats)} чатов")
        print(f"[API] GET /api/chats - успешно возвращено {len(filtered_chats)} чатов")
        
        response_data = {
            'success': True,
            'chats': filtered_chats,
            'stats': stats
        }
        
        if info_message:
            response_data['info'] = info_message
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"[API] Ошибка при получении списка чатов: {e}", exc_info=True)
        print(f"[API] Ошибка при получении списка чатов: {e}")
        return jsonify({
            'success': False,
            'error': 'Не удалось загрузить список чатов'
        }), 500


@app.route('/api/chats/<chat_id>/members', methods=['POST'])
def get_chat_members(chat_id):
    """API endpoint для получения списка участников чата"""
    import asyncio
    # Преобразуем chat_id в int (может быть отрицательным для супергрупп)
    try:
        chat_id = int(chat_id)
    except (ValueError, TypeError):
        logger.warning(f"[API] GET /api/chats/{chat_id}/members - неверный формат chat_id")
        print(f"[API] GET /api/chats/{chat_id}/members - неверный формат chat_id")
        return jsonify({
            'success': False,
            'error': 'Неверный формат ID чата'
        }), 400
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        logger.info(f"[API] GET /api/chats/{chat_id}/members - запрос от пользователя {user_id}")
        print(f"[API] GET /api/chats/{chat_id}/members - запрос от пользователя {user_id}")
        
        if not user_id:
            logger.warning(f"[API] GET /api/chats/{chat_id}/members - User ID не предоставлен")
            print(f"[API] GET /api/chats/{chat_id}/members - User ID не предоставлен")
            return jsonify({
                'success': False,
                'error': 'User ID не предоставлен'
            }), 400
        
        bot = Bot(token=Config.TOKEN)
        from bot.services.chat_service import ChatService
        chat_service = ChatService(bot)
        
        # Проверяем права пользователя и бота
        async def check_and_get_members():
            # Инициализируем бота перед использованием
            await bot.initialize()
            # Проверяем, является ли пользователь создателем
            is_user_creator = await chat_service.is_user_creator(chat_id, user_id)
            logger.info(f"[API] Чат {chat_id}: пользователь {user_id} создатель = {is_user_creator}")
            print(f"[API] Чат {chat_id}: пользователь {user_id} создатель = {is_user_creator}")
            
            if not is_user_creator:
                return None, "Пользователь не является создателем группы"
            
            # Проверяем, является ли бот администратором
            is_bot_admin = await chat_service.is_bot_admin(chat_id)
            logger.info(f"[API] Чат {chat_id}: бот админ = {is_bot_admin}")
            print(f"[API] Чат {chat_id}: бот админ = {is_bot_admin}")
            
            if not is_bot_admin:
                return None, "Бот не является администратором группы"
            
            # Получаем список участников
            members = await chat_service.get_chat_members_list(chat_id)
            logger.info(f"[API] Получено {len(members)} участников для чата {chat_id}")
            print(f"[API] Получено {len(members)} участников для чата {chat_id}")
            return members, None
        
        # Запускаем async функцию
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        members, error = loop.run_until_complete(check_and_get_members())
        
        # Закрываем бота после использования
        try:
            loop.run_until_complete(bot.shutdown())
        except:
            pass
        
        if error:
            logger.warning(f"[API] GET /api/chats/{chat_id}/members - ошибка: {error}")
            print(f"[API] GET /api/chats/{chat_id}/members - ошибка: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 403
        
        logger.info(f"[API] GET /api/chats/{chat_id}/members - успешно возвращено {len(members)} участников")
        print(f"[API] GET /api/chats/{chat_id}/members - успешно возвращено {len(members)} участников")
        
        return jsonify({
            'success': True,
            'members': members
        })
        
    except TelegramError as e:
        logger.error(f"[API] Ошибка Telegram API при получении участников чата {chat_id}: {e}")
        print(f"[API] Ошибка Telegram API при получении участников чата {chat_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка Telegram API: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"[API] Ошибка при получении участников чата {chat_id}: {e}", exc_info=True)
        print(f"[API] Ошибка при получении участников чата {chat_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Не удалось загрузить список участников'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


def run_webapp():
    """Запуск веб-приложения"""
    app.run(
        host=Config.WEBAPP_HOST,
        port=Config.WEBAPP_PORT,
        debug=False
    )


if __name__ == '__main__':
    run_webapp()

