// Управление фильтрами и сортировкой
import { renderChats } from './render.js';
import { renderStats } from './stats.js';
import type { Chat, FilterType, SortBy, SortOrder } from './types.js';

let currentChats: Chat[] = [];
let currentStats: any = null;

/**
 * Применить фильтры и сортировку
 */
export function applyFilters(): void {
    if (!currentChats || currentChats.length === 0) {
        renderChats([], null);
        return;
    }
    
    let filtered = [...currentChats];
    
    // Фильтр по типу
    const filterType = (document.getElementById('filterType') as HTMLSelectElement)?.value as FilterType || 'all';
    if (filterType !== 'all') {
        filtered = filtered.filter(chat => chat.type === filterType);
    }
    
    // Поиск по названию
    const searchInput = document.getElementById('searchInput') as HTMLInputElement;
    const searchTerm = searchInput?.value.toLowerCase().trim() || '';
    if (searchTerm) {
        filtered = filtered.filter(chat => 
            (chat.title || '').toLowerCase().includes(searchTerm)
        );
    }
    
    // Сортировка
    const sortBy = (document.getElementById('sortBy') as HTMLSelectElement)?.value as SortBy || 'title';
    const sortOrder = (document.getElementById('sortOrder') as HTMLSelectElement)?.value as SortOrder || 'asc';
    
    if (sortBy === 'title') {
        filtered.sort((a, b) => {
            const cmp = (a.title || '').toLowerCase().localeCompare((b.title || '').toLowerCase());
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    } else if (sortBy === 'members_count') {
        filtered.sort((a, b) => {
            const aCount = a.members_count || 0;
            const bCount = b.members_count || 0;
            const cmp = aCount - bCount;
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    } else if (sortBy === 'type') {
        filtered.sort((a, b) => {
            const cmp = a.type.localeCompare(b.type);
            return sortOrder === 'asc' ? cmp : -cmp;
        });
    }
    
    // Отображаем отфильтрованные чаты
    renderChats(filtered, null);
    
    // Обновляем статистику для отфильтрованных чатов
    if (currentStats) {
        const filteredStats = {
            total: filtered.length,
            groups: filtered.filter(c => c.type === 'group').length,
            supergroups: filtered.filter(c => c.type === 'supergroup').length,
            private: 0,
            channels: 0
        };
        renderStats(filteredStats);
    }
}

/**
 * Поиск чатов
 */
export function performSearch(): void {
    applyFilters();
}

/**
 * Сброс фильтров
 */
export function resetFilters(): void {
    const searchInput = document.getElementById('searchInput') as HTMLInputElement;
    const filterType = document.getElementById('filterType') as HTMLSelectElement;
    const sortBy = document.getElementById('sortBy') as HTMLSelectElement;
    const sortOrder = document.getElementById('sortOrder') as HTMLSelectElement;
    
    if (searchInput) searchInput.value = '';
    if (filterType) filterType.value = 'all';
    if (sortBy) sortBy.value = 'title';
    if (sortOrder) sortOrder.value = 'asc';
    
    applyFilters();
}

/**
 * Установить текущие чаты и статистику
 */
export function setCurrentChats(chats: Chat[], stats: any): void {
    currentChats = chats;
    currentStats = stats;
}

// Экспортируем функции в глобальную область для использования в HTML
declare global {
    interface Window {
        applyFilters: () => void;
        performSearch: () => void;
        resetFilters: () => void;
    }
}

window.applyFilters = applyFilters;
window.performSearch = performSearch;
window.resetFilters = resetFilters;
