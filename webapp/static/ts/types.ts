// Типы для Telegram WebApp
export interface TelegramWebApp {
    ready(): void;
    expand(): void;
    close(): void;
    initData: string;
    initDataUnsafe: {
        user?: TelegramUser;
    };
    BackButton?: {
        show(): void;
        hide(): void;
    };
}

export interface TelegramUser {
    id: number;
    first_name: string;
    last_name?: string;
    username?: string;
    language_code?: string;
}

// Типы для чатов
export interface Chat {
    id: number;
    title: string;
    type: 'group' | 'supergroup' | 'private' | 'channel';
    photo_url?: string;
    members_count?: number;
}

export interface ChatStats {
    total: number;
    groups: number;
    supergroups: number;
    private: number;
    channels: number;
}

export interface ChatListResponse {
    success: boolean;
    chats: Chat[];
    stats: ChatStats;
    cached?: boolean;
    warning?: string;
    error?: string;
    pagination?: {
        page: number;
        per_page: number;
        total: number;
        total_pages: number;
    };
}

// Типы для фильтров
export type FilterType = 'all' | 'group' | 'supergroup';
export type SortBy = 'title' | 'members_count' | 'type';
export type SortOrder = 'asc' | 'desc';

export interface FilterState {
    searchTerm: string;
    filterType: FilterType;
    sortBy: SortBy;
    sortOrder: SortOrder;
}

// Типы для модального окна
export interface ModalElement extends HTMLElement {
    style: CSSStyleDeclaration;
}

declare global {
    interface Window {
        Telegram: {
            WebApp: TelegramWebApp;
        };
        lucide: {
            createIcons(): void;
        };
    }
}
