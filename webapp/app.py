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
    return render_template('index.html')


@app.route('/api/chats', methods=['POST'])
def get_chats():
    """API endpoint для получения списка чатов"""
    import asyncio
    try:
        data = request.get_json()
        init_data = data.get('init_data', '')
        user_id = data.get('user_id')
        
        # Валидация данных (упрощенная)
        # В продакшене нужно добавить полную валидацию подписи
        if not validate_telegram_webapp_data(init_data):
            logger.warning(f"Невалидные данные от пользователя {user_id}")
            # В режиме разработки разрешаем запросы без валидации
        
        # Получаем список чатов из хранилища
        chats = chat_storage.get_all_chats()
        
        # Обновляем информацию о чатах из Telegram API (синхронно)
        bot = Bot(token=Config.TOKEN)
        updated_chats = []
        
        async def update_chats():
            nonlocal updated_chats
            for chat_data in chats:
                try:
                    # Пытаемся обновить информацию о чате
                    updated = await chat_storage.update_chat_info(bot, chat_data['id'])
                    if updated:
                        updated_chats.append(updated)
                    else:
                        # Если не удалось обновить, используем старые данные
                        updated_chats.append(chat_data)
                except TelegramError as e:
                    logger.warning(f"Не удалось обновить информацию о чате {chat_data['id']}: {e}")
                    # Используем старые данные
                    updated_chats.append(chat_data)
        
        # Запускаем async функцию
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(update_chats())
        
        # Получаем статистику
        stats = chat_storage.get_stats()
        
        # Сортируем чаты по типу и названию
        updated_chats.sort(key=lambda x: (x['type'], x['title']))
        
        return jsonify({
            'success': True,
            'chats': updated_chats,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}", exc_info=True)
        # В случае ошибки возвращаем данные из хранилища без обновления
        chats = chat_storage.get_all_chats()
        stats = chat_storage.get_stats()
        return jsonify({
            'success': True,
            'chats': chats,
            'stats': stats
        })


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

