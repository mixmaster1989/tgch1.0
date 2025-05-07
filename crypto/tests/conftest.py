"""
Конфигурация для тестов криптомодуля
"""

import pytest
import os
import sys
import logging

# Отключаем логирование во время тестов
@pytest.fixture(autouse=True)
def disable_logging():
    """Отключает логирование во время тестов"""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)

# Добавляем корневую директорию проекта в sys.path
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Добавляет корневую директорию проекта в sys.path"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    yield