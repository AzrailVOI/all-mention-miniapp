"""
Unit-тесты для ChatStorageService.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime
from telegram import Chat

from bot.services.chat_storage_service import ChatStorageService
from bot.constants import ChatType


class TestChatStorageService:
    """Тесты для ChatStorageService."""
    
    def test_register_chat_new(self, chat_storage_service, sample_chat):
        """Тест регистрации нового чата."""
        initial_count = len(chat_storage_service.get_all_chats())
        chat_storage_service.register_chat(sample_chat)
        
        assert len(chat_storage_service.get_all_chats()) == initial_count + 1
        chat_data = chat_storage_service.get_chat(sample_chat.id)
        assert chat_data is not None
        assert chat_data['id'] == sample_chat.id
        assert chat_data['title'] == sample_chat.title
        assert chat_data['type'] == sample_chat.type
    
    def test_register_chat_update(self, chat_storage_service, sample_chat):
        """Тест обновления существующего чата."""
        # Регистрируем чат первый раз
        chat_storage_service.register_chat(sample_chat)
        
        # Обновляем чат
        sample_chat.title = "Updated Title"
        chat_storage_service.register_chat(sample_chat)
        
        chat_data = chat_storage_service.get_chat(sample_chat.id)
        assert chat_data['title'] == "Updated Title"
        assert len(chat_storage_service.get_all_chats()) == 1
    
    def test_get_chat_existing(self, chat_storage_service, sample_chat):
        """Тест получения существующего чата."""
        chat_storage_service.register_chat(sample_chat)
        chat_data = chat_storage_service.get_chat(sample_chat.id)
        
        assert chat_data is not None
        assert chat_data['id'] == sample_chat.id
    
    def test_get_chat_nonexistent(self, chat_storage_service):
        """Тест получения несуществующего чата."""
        chat_data = chat_storage_service.get_chat(999999999)
        assert chat_data is None
    
    def test_get_all_chats_empty(self, chat_storage_service):
        """Тест получения всех чатов из пустого хранилища."""
        chats = chat_storage_service.get_all_chats()
        assert isinstance(chats, list)
        assert len(chats) == 0
    
    def test_get_all_chats_multiple(self, chat_storage_service, sample_chat):
        """Тест получения всех чатов с несколькими чатами."""
        # Создаем несколько чатов
        chat1 = Mock(spec=Chat)
        chat1.id = 1
        chat1.title = "Chat 1"
        chat1.type = ChatType.GROUP
        chat1.username = None
        chat1.members_count = 5
        
        chat2 = Mock(spec=Chat)
        chat2.id = 2
        chat2.title = "Chat 2"
        chat2.type = ChatType.SUPERGROUP
        chat2.username = None
        chat2.members_count = 10
        
        chat_storage_service.register_chat(chat1)
        chat_storage_service.register_chat(chat2)
        
        chats = chat_storage_service.get_all_chats()
        assert len(chats) == 2
        assert any(c['id'] == 1 for c in chats)
        assert any(c['id'] == 2 for c in chats)
    
    def test_get_chats_by_type(self, chat_storage_service):
        """Тест получения чатов по типу."""
        # Создаем чаты разных типов
        group_chat = Mock(spec=Chat)
        group_chat.id = 1
        group_chat.title = "Group"
        group_chat.type = ChatType.GROUP
        group_chat.username = None
        group_chat.members_count = None
        
        supergroup_chat = Mock(spec=Chat)
        supergroup_chat.id = 2
        supergroup_chat.title = "Supergroup"
        supergroup_chat.type = ChatType.SUPERGROUP
        supergroup_chat.username = None
        supergroup_chat.members_count = None
        
        chat_storage_service.register_chat(group_chat)
        chat_storage_service.register_chat(supergroup_chat)
        
        groups = chat_storage_service.get_chats_by_type('group')
        assert len(groups) == 1
        assert groups[0]['type'] == 'group'
        
        supergroups = chat_storage_service.get_chats_by_type('supergroup')
        assert len(supergroups) == 1
        assert supergroups[0]['type'] == 'supergroup'
    
    def test_get_stats(self, chat_storage_service):
        """Тест получения статистики по чатам."""
        # Создаем чаты разных типов
        group_chat = Mock(spec=Chat)
        group_chat.id = 1
        group_chat.title = "Group"
        group_chat.type = ChatType.GROUP
        group_chat.username = None
        group_chat.members_count = None
        
        supergroup_chat = Mock(spec=Chat)
        supergroup_chat.id = 2
        supergroup_chat.title = "Supergroup"
        supergroup_chat.type = ChatType.SUPERGROUP
        supergroup_chat.username = None
        supergroup_chat.members_count = None
        
        chat_storage_service.register_chat(group_chat)
        chat_storage_service.register_chat(supergroup_chat)
        
        stats = chat_storage_service.get_stats()
        assert stats['total'] == 2
        assert stats['groups'] == 1
        assert stats['supergroups'] == 1
        assert stats['private'] == 0
        assert stats['channels'] == 0
    
    def test_remove_chat_existing(self, chat_storage_service, sample_chat):
        """Тест удаления существующего чата."""
        chat_storage_service.register_chat(sample_chat)
        assert chat_storage_service.get_chat(sample_chat.id) is not None
        
        result = chat_storage_service.remove_chat(sample_chat.id)
        assert result is True
        assert chat_storage_service.get_chat(sample_chat.id) is None
    
    def test_remove_chat_nonexistent(self, chat_storage_service):
        """Тест удаления несуществующего чата."""
        result = chat_storage_service.remove_chat(999999999)
        assert result is False
    
    def test_persistence(self, temp_storage_file, sample_chat):
        """Тест сохранения и загрузки из файла."""
        # Создаем первый экземпляр и регистрируем чат
        storage1 = ChatStorageService(storage_file=temp_storage_file)
        storage1.register_chat(sample_chat)
        
        # Создаем второй экземпляр с тем же файлом
        storage2 = ChatStorageService(storage_file=temp_storage_file)
        
        # Проверяем, что чат загружен из файла
        chat_data = storage2.get_chat(sample_chat.id)
        assert chat_data is not None
        assert chat_data['id'] == sample_chat.id
        assert chat_data['title'] == sample_chat.title
