"""
Конфигурационный файл для проекта
"""

# Версия приложения
APP_VERSION = "1.0.0"

# Настройки приложения
APP_NAME = "Конструктор индикаторов TradingView"
APP_DESCRIPTION = "Визуальный конструктор индикаторов для TradingView"
APP_AUTHOR = "TradingView Indicator Builder Team"
APP_YEAR = "2023-2025"

# Настройки интерфейса
UI_THEME = "dark"  # dark или light
UI_FONT_FAMILY = "Arial"
UI_TITLE_FONT_SIZE = 24
UI_NORMAL_FONT_SIZE = 14
UI_CODE_FONT_FAMILY = "Consolas"
UI_CODE_FONT_SIZE = 12

# Настройки цветов (темная тема)
COLORS_DARK = {
    "background": "#1e1e1e",
    "secondary_background": "#2b2b2b",
    "card_background": "#23272e",
    "card_hover": "#2c313c",
    "text": "#ffffff",
    "secondary_text": "#aaaaaa",
    "border": "#3d3d3d",
    "border_hover": "#4a4a4a",
    "accent": "#4a90e2",
    "success": "#4CAF50",
    "success_hover": "#45a049",
    "warning": "#FF9800",
    "warning_hover": "#F57C00",
    "error": "#f44336",
    "error_hover": "#d32f2f",
    "info": "#2196F3",
    "info_hover": "#1976D2",
    "neutral": "#607D8B",
    "neutral_hover": "#455A64",
    "purple": "#9C27B0",
    "purple_hover": "#7B1FA2",
}

# Настройки цветов (светлая тема)
COLORS_LIGHT = {
    "background": "#f5f5f5",
    "secondary_background": "#e0e0e0",
    "card_background": "#ffffff",
    "card_hover": "#f0f0f0",
    "text": "#212121",
    "secondary_text": "#757575",
    "border": "#bdbdbd",
    "border_hover": "#9e9e9e",
    "accent": "#2196F3",
    "success": "#4CAF50",
    "success_hover": "#388E3C",
    "warning": "#FF9800",
    "warning_hover": "#F57C00",
    "error": "#f44336",
    "error_hover": "#d32f2f",
    "info": "#2196F3",
    "info_hover": "#1976D2",
    "neutral": "#607D8B",
    "neutral_hover": "#455A64",
    "purple": "#9C27B0",
    "purple_hover": "#7B1FA2",
}

# Получение текущей цветовой схемы
def get_colors():
    return COLORS_DARK if UI_THEME == "dark" else COLORS_LIGHT

# Настройки логирования
LOG_FILE = "error.log"
LOG_LEVEL = "ERROR"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s %(levelname)s:%(message)s"

# Настройки генерации кода
CODE_INDENT = 4
CODE_MAX_LINE_LENGTH = 80
CODE_VALIDATE_ON_GENERATE = True
CODE_AUTO_FORMAT = True

# Настройки файлов
DEFAULT_SAVE_DIR = "saved_indicators"
BACKUP_DIR = "backups"
EXAMPLES_DIR = "examples"

# Настройки автосохранения
AUTOSAVE_ENABLED = True
AUTOSAVE_INTERVAL = 300  # в секундах (5 минут)
AUTOSAVE_FILE = "autosave.json"

# Настройки для Pine Script
PINE_SCRIPT_VERSION = 5
PINE_SCRIPT_DEFAULT_OVERLAY = True