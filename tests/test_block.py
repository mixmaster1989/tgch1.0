import sys
import os
import pytest

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from block import Block

def test_block_init():
    """Тест инициализации блока"""
    block = Block("Тестовый блок")
    assert block.type == "Тестовый блок"
    assert block.params == {}

def test_block_init_with_params():
    """Тест инициализации блока с параметрами"""
    params = {"param1": "value1", "param2": 42}
    block = Block("Тестовый блок", params)
    assert block.type == "Тестовый блок"
    assert block.params == params

def test_block_get_data():
    """Тест получения данных блока"""
    params = {"param1": "value1", "param2": 42}
    block = Block("Тестовый блок", params)
    data = block.get_data()
    assert data["type"] == "Тестовый блок"
    assert data["params"] == params

def test_block_duplicate():
    """Тест дублирования блока"""
    params = {"param1": "value1", "param2": 42}
    block = Block("Тестовый блок", params)
    duplicate = block.duplicate()
    
    # Проверяем, что это новый объект
    assert duplicate is not block
    
    # Проверяем, что данные скопированы
    assert duplicate.type == block.type
    assert duplicate.params == block.params
    
    # Проверяем, что это глубокая копия параметров
    duplicate.params["param1"] = "changed"
    assert block.params["param1"] == "value1"