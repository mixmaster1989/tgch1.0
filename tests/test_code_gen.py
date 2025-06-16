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
    
    # Проверяем, что код не содержит ошибок
    errors = validate_code(code)
    assert len(errors) == 0

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
    
    # Проверяем, что код не содержит ошибок
    errors = validate_code(code)
    assert len(errors) == 0

def test_generate_code_empty_blocks():
    """Тест генерации кода с пустым списком блоков"""
    # Генерируем код
    code = generate_code([])
    
    # Проверяем, что код содержит необходимые элементы
    assert "//@version=5" in code
    assert "indicator" in code
    
    # Проверяем, что код не содержит ошибок
    errors = validate_code(code)
    assert len(errors) == 0

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