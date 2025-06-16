import sys
import os
import pytest

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import validate_code

def test_validate_code_valid():
    """Тест валидации корректного кода"""
    code = """
//@version=5
indicator("My Indicator", overlay=true)

ma = ta.sma(close, 14)
plot(ma, color=color.blue, title="MA")
"""
    errors = validate_code(code)
    assert len(errors) == 0

def test_validate_code_missing_version():
    """Тест валидации кода без версии"""
    code = """
indicator("My Indicator", overlay=true)

ma = ta.sma(close, 14)
plot(ma, color=color.blue, title="MA")
"""
    errors = validate_code(code)
    assert len(errors) > 0
    assert any("версия" in error for error in errors)

def test_validate_code_missing_indicator():
    """Тест валидации кода без объявления индикатора"""
    code = """
//@version=5

ma = ta.sma(close, 14)
plot(ma, color=color.blue, title="MA")
"""
    errors = validate_code(code)
    assert len(errors) > 0
    assert any("индикатора" in error for error in errors)

def test_validate_code_param_error():
    """Тест валидации кода с ошибкой в параметрах"""
    code = """
//@version=5
indicator("My Indicator", overlay=true)

ma = ta.sma
plot(ma, color=color.blue, title="MA")
"""
    errors = validate_code(code)
    assert len(errors) > 0
    assert any("параметрах" in error for error in errors)

def test_validate_code_bracket_mismatch():
    """Тест валидации кода с несоответствием скобок"""
    code = """
//@version=5
indicator("My Indicator", overlay=true)

ma = ta.sma(close, 14
plot(ma, color=color.blue, title="MA")
"""
    errors = validate_code(code)
    assert len(errors) > 0
    assert any("скобок" in error for error in errors)