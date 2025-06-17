import sys
import os
import pytest

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_gen import generate_code
from block import Block
from utils import validate_code

def test_generate_code_basic():
    """Тест базовой генерации кода"""
    # Создаем простой блок
    block = Block("Скользящая средняя", {
        "Тип": "EMA",
        "Период": "14",
        "Источник": "close"
    })
    
    # Генерируем код
    code = generate_code([block])
    
    # Проверяем, что код содержит необходимые элементы
    assert "//@version=5" in code
    assert "indicator" in code
    assert "ta.ema" in code
    assert "close" in code
    assert "14" in code
    assert "plot(ma, color=color.blue, title=\"MA\")" in code

def test_generate_code_multiple_blocks():
    """Тест генерации кода с несколькими блоками"""
    # Создаем блоки
    blocks = [
        Block("Индикатор", {
            "Название": "Тестовый индикатор",
            "Временной интервал": "1d",
            "Тип графика": "candle"
        }),
        Block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        }),
        Block("RSI", {
            "Период": "14",
            "Источник": "close"
        })
    ]
    
    # Генерируем код
    code = generate_code(blocks)
    
    # Проверяем, что код содержит необходимые элементы
    assert "//@version=5" in code
    assert "indicator" in code
    assert "Тестовый индикатор" in code
    assert "ta.ema" in code
    assert "ta.rsi" in code
    assert "plot(ma, color=color.blue, title=\"MA\")" in code
    assert "plot(rsi, color=color.purple, title=\"RSI\")" in code

def test_generate_code_empty_blocks():
    """Тест генерации кода с пустым списком блоков"""
    # Генерируем код
    code = generate_code([])
    
    # Проверяем, что код содержит необходимые элементы
    assert "//@version=5" in code
    assert "indicator" in code
    assert "My Indicator" in code

def test_generate_code_invalid_block():
    """Тест генерации кода с некорректным блоком"""
    # Создаем блок с некорректным типом
    block = Block("Несуществующий тип", {
        "Параметр": "Значение"
    })
    
    # Генерируем код
    code = generate_code([block])
    
    # Проверяем, что код содержит необходимые элементы
    assert "//@version=5" in code
    assert "indicator" in code
    assert "My Indicator" in code

def test_block_params_variants():
    """Тест различных вариантов параметров блоков"""
    # Тестируем разные типы скользящих средних
    ma_types = ["SMA", "EMA", "WMA", "VWMA"]
    for ma_type in ma_types:
        block = Block("Скользящая средняя", {
            "Тип": ma_type,
            "Период": "14",
            "Источник": "close"
        })
        code = generate_code([block])
        assert f"ta.{ma_type.lower()}" in code

def test_validate_code_missing_version():
    """Тест валидации кода без версии"""
    code = "indicator(\"Test\")"
    errors = validate_code(code)
    assert len(errors) > 0
    assert any("version" in error.lower() for error in errors)

def test_validate_code_missing_indicator():
    """Тест валидации кода без индикатора"""
    code = "//@version=5"
    errors = validate_code(code)
    assert len(errors) > 0
    assert any("indicator" in error.lower() for error in errors)

def test_export_import():
    """Тест экспорта и импорта кода"""
    # Создаем тестовый код
    original_code = "//@version=5\nindicator(\"Test\")\nplot(close)"
    
    # Экспортируем код
    export_path = "test_export.pine"
    with open(export_path, "w") as f:
        f.write(original_code)
    
    # Импортируем код
    with open(export_path, "r") as f:
        imported_code = f.read()
    
    # Проверяем совпадение
    assert original_code == imported_code
    
    # Удаляем тестовый файл
    os.remove(export_path)

def test_import_broken_file():
    """Тест импорта некорректного файла"""
    # Создаем некорректный файл
    broken_code = "invalid code"
    export_path = "test_broken.pine"
    with open(export_path, "w") as f:
        f.write(broken_code)
    
    # Пытаемся импортировать
    with open(export_path, "r") as f:
        imported_code = f.read()
    
    # Проверяем, что код импортировался как есть
    assert broken_code == imported_code
    
    # Удаляем тестовый файл
    os.remove(export_path)

def test_templates():
    """Тест шаблонов индикаторов"""
    # Создаем блок с шаблоном
    block = Block("Стратегия", {
        "Название": "Тестовая стратегия",
        "Начальный капитал": "10000",
        "Комиссия": "0.1"
    })
    
    # Генерируем код
    code = generate_code([block])
    
    # Проверяем, что код содержит необходимые элементы
    assert "//@version=5" in code
    assert "strategy" in code
    assert "Тестовая стратегия" in code
    assert "initial_capital=10000" in code
    assert "commission_value=0.1" in code

def test_generate_code_empty():
    """Тест генерации пустого кода"""
    code = generate_code([])
    assert "//@version=5" in code
    assert "indicator" in code
    assert "My Indicator" in code

def test_utils_validate_code():
    """Тест утилиты валидации кода"""
    # Тестируем корректный код
    valid_code = "//@version=5\nindicator(\"Test\")\nplot(close)"
    errors = validate_code(valid_code)
    assert len(errors) == 0
    
    # Тестируем некорректный код
    invalid_code = "invalid code"
    errors = validate_code(invalid_code)
    assert len(errors) > 0