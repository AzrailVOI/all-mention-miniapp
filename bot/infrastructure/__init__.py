"""Инфраструктурный слой для работы с внешними системами"""
from bot.infrastructure.telegram_client import TelegramClient, get_telegram_client

__all__ = ['TelegramClient', 'get_telegram_client']
