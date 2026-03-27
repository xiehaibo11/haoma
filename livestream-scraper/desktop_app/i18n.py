"""
Internationalization (i18n) support for the desktop application.
Supports multiple languages with easy extensibility.
"""

import json
import os
from typing import Dict, Optional


class I18n:
    """
    Internationalization manager.
    Handles translations and language switching.
    """
    
    # Built-in translations
    TRANSLATIONS = {
        'en': {
            'app_title': 'Live Stream Phone Extractor - Leisu.com',
            'url_section': 'Target URL',
            'preset1': 'Preset 1',
            'preset2': 'Preset 2',
            'start_extraction': '▶ Start Extraction',
            'stop_extraction': '⏹ Stop Extraction',
            'refresh_data': '🔄 Refresh Data',
            'export_csv': '📁 Export CSV',
            'search': 'Search:',
            'search_btn': 'Search',
            'data_section': 'Extracted Data',
            'col_id': 'ID',
            'col_phone': 'Phone Number',
            'col_username': 'Username',
            'col_context': 'Context',
            'col_time': 'Extracted At',
            'stats_total': 'Total: {}',
            'stats_today': 'Today: {}',
            'stats_unique_phones': 'Unique Phones: {}',
            'stats_unique_users': 'Unique Users: {}',
            'clear_all': 'Clear All Data',
            'status_ready': 'Ready',
            'status_running': 'Running',
            'status_stopped': 'Stopped',
            'status_found': 'Found {} new phone number(s)',
            'error_url': 'Please enter a URL',
            'confirm_clear': 'Are you sure you want to delete ALL data?\nThis cannot be undone!',
            'confirm_delete': 'Delete this record?',
            'export_success': 'Data exported to:\n{}',
            'export_error': 'Failed to export data',
            'menu_copy_phone': 'Copy Phone',
            'menu_copy_username': 'Copy Username',
            'menu_delete': 'Delete Record',
            'dialog_details': 'Record Details',
            'dialog_close': 'Close',
            'language': 'Language:',
            'lang_english': 'English',
            'lang_chinese': 'Chinese (中文)',
            'copied': 'Copied: {}',
            'record_deleted': 'Record deleted',
            'all_data_cleared': 'All data has been cleared',
            'db_error': 'Database error: {}',
        },
        'zh': {
            'app_title': '直播手机号提取器 - Leisu.com',
            'url_section': '目标网址',
            'preset1': '预设 1',
            'preset2': '预设 2',
            'start_extraction': '▶ 开始提取',
            'stop_extraction': '⏹ 停止提取',
            'refresh_data': '🔄 刷新数据',
            'export_csv': '📁 导出CSV',
            'search': '搜索:',
            'search_btn': '搜索',
            'data_section': '提取的数据',
            'col_id': 'ID',
            'col_phone': '手机号码',
            'col_username': '用户名',
            'col_context': '内容',
            'col_time': '提取时间',
            'stats_total': '总计: {}',
            'stats_today': '今日: {}',
            'stats_unique_phones': '唯一号码: {}',
            'stats_unique_users': '唯一用户: {}',
            'clear_all': '清空所有数据',
            'status_ready': '就绪',
            'status_running': '运行中',
            'status_stopped': '已停止',
            'status_found': '发现 {} 个新号码',
            'error_url': '请输入网址',
            'confirm_clear': '确定要删除所有数据吗？\n此操作无法撤销！',
            'confirm_delete': '删除这条记录？',
            'export_success': '数据已导出到:\n{}',
            'export_error': '导出失败',
            'menu_copy_phone': '复制手机号',
            'menu_copy_username': '复制用户名',
            'menu_delete': '删除记录',
            'dialog_details': '记录详情',
            'dialog_close': '关闭',
            'language': '语言:',
            'lang_english': '英文 (English)',
            'lang_chinese': '中文',
            'copied': '已复制: {}',
            'record_deleted': '记录已删除',
            'all_data_cleared': '所有数据已清空',
            'db_error': '数据库错误: {}',
        }
    }
    
    def __init__(self, default_lang: str = 'zh'):
        """
        Initialize i18n manager.
        
        Args:
            default_lang: Default language code ('en', 'zh', etc.)
        """
        self.current_lang = default_lang
        self.custom_translations: Dict[str, Dict[str, str]] = {}
        
        # Load custom translations if exist
        self._load_custom_translations()
    
    def _load_custom_translations(self):
        """Load custom translations from file."""
        trans_file = 'translations.json'
        if os.path.exists(trans_file):
            try:
                with open(trans_file, 'r', encoding='utf-8') as f:
                    self.custom_translations = json.load(f)
            except:
                pass
    
    def _save_custom_translations(self):
        """Save custom translations to file."""
        try:
            with open('translations.json', 'w', encoding='utf-8') as f:
                json.dump(self.custom_translations, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def set_language(self, lang: str):
        """
        Set current language.
        
        Args:
            lang: Language code ('en', 'zh', etc.)
        """
        if lang in self.TRANSLATIONS or lang in self.custom_translations:
            self.current_lang = lang
    
    def get_language(self) -> str:
        """Get current language code."""
        return self.current_lang
    
    def get_supported_languages(self) -> list:
        """Get list of supported language codes."""
        builtin = list(self.TRANSLATIONS.keys())
        custom = list(self.custom_translations.keys())
        return list(set(builtin + custom))
    
    def _(self, key: str, *args) -> str:
        """
        Get translated string.
        
        Args:
            key: Translation key
            *args: Format arguments
            
        Returns:
            Translated string
        """
        # Try custom translations first
        if self.current_lang in self.custom_translations:
            if key in self.custom_translations[self.current_lang]:
                text = self.custom_translations[self.current_lang][key]
                return text.format(*args) if args else text
        
        # Try built-in translations
        if self.current_lang in self.TRANSLATIONS:
            if key in self.TRANSLATIONS[self.current_lang]:
                text = self.TRANSLATIONS[self.current_lang][key]
                return text.format(*args) if args else text
        
        # Fallback to English
        if key in self.TRANSLATIONS.get('en', {}):
            text = self.TRANSLATIONS['en'][key]
            return text.format(*args) if args else text
        
        # Return key if not found
        return key.format(*args) if args else key
    
    def add_translation(self, lang: str, key: str, text: str):
        """
        Add custom translation.
        
        Args:
            lang: Language code
            key: Translation key
            text: Translated text
        """
        if lang not in self.custom_translations:
            self.custom_translations[lang] = {}
        
        self.custom_translations[lang][key] = text
        self._save_custom_translations()


# Global i18n instance
_i18n = I18n()


def set_language(lang: str):
    """Set global language."""
    _i18n.set_language(lang)


def get_language() -> str:
    """Get global language."""
    return _i18n.get_language()


def _(key: str, *args) -> str:
    """Shorthand for translation."""
    return _i18n._(key, *args)


def get_supported_languages() -> list:
    """Get supported languages."""
    return _i18n.get_supported_languages()
