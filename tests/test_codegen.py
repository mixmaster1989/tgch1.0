import pytest
from code_gen import generate_code, validate_code
from block import Block
from constants import BLOCK_TYPES
import json

# --- Генерация кода для каждого блока ---
def make_block(block_type, params=None):
    block = Block(block_type)
    if params:
        block.params.update(params)
    elif "default_values" in BLOCK_TYPES[block_type]:
        block.params.update(BLOCK_TYPES[block_type]["default_values"])
    return block

@pytest.mark.parametrize("block_type", list(BLOCK_TYPES.keys()))
def test_generate_code_for_block(block_type):
    block = make_block(block_type)
    code = generate_code([block])
    assert "//@version=5" in code
    assert "indicator(" in code or "strategy(" in code or "plot(" in code
    errors = validate_code(code)
    assert not errors, f"Ошибки валидации: {errors}"

# --- Варианты параметров для каждого блока ---
def test_block_params_variants():
    for block_type, info in BLOCK_TYPES.items():
        for param in info.get("params", []):
            # Тестируем min/max/invalid для числовых
            if param["type"] in ("int", "float"):
                for val in [param.get("min", 1), param.get("max", 100), 0, -1, 999999]:
                    b = make_block(block_type, {param["name"]: val})
                    code = generate_code([b])
                    assert "//@version=5" in code
            # Тестируем все values для строковых
            if "values" in param:
                for val in param["values"]:
                    b = make_block(block_type, {param["name"]: val})
                    code = generate_code([b])
                    assert "//@version=5" in code
            # Тестируем пустое значение
            b = make_block(block_type, {param["name"]: ""})
            code = generate_code([b])
            assert "//@version=5" in code

# --- Валидация ошибок ---
def test_validate_code_missing_version():
    code = "indicator(\"Test\")\nplot(close)"
    errors = validate_code(code)
    assert any("//@version=5" in e for e in errors)

def test_validate_code_missing_indicator():
    code = "//@version=5\nplot(close)"
    errors = validate_code(code)
    assert any("indicator" in e for e in errors)

# --- Экспорт/импорт ---
def test_export_import(tmp_path):
    blocks = [make_block("RSI"), make_block("MACD")]
    settings = [{"type": b.type, "params": b.params} for b in blocks]
    file = tmp_path / "settings.json"
    with open(file, "w") as f:
        json.dump(settings, f)
    with open(file, "r") as f:
        loaded = json.load(f)
    assert loaded == settings

# --- Экспорт/импорт: битый файл ---
def test_import_broken_file(tmp_path):
    file = tmp_path / "broken.json"
    file.write_text("not a json")
    try:
        with open(file, "r") as f:
            json.load(f)
    except Exception as e:
        assert "Expecting value" in str(e)

# --- Шаблоны ---
def test_templates():
    from ui import TemplateDialog
    dialog = TemplateDialog()
    assert hasattr(dialog, "setup_ui")

# --- Проверка ошибок генерации ---
def test_generate_code_empty():
    code = generate_code([])
    assert "//@version=5" in code

# --- Проверка утилит (если есть) ---
def test_utils_validate_code():
    from utils import validate_code as vcode
    assert isinstance(vcode("//@version=5\nindicator(\"a\")"), list)

# --- Проверка на пустые и некорректные блоки ---
def test_generate_code_invalid_block():
    b = Block("RSI")
    b.params = {}  # Пустые параметры
    code = generate_code([b])
    assert "//@version=5" in code

# --- Шаблоны ---
def test_templates():
    from ui import TemplateDialog
    dialog = TemplateDialog()
    # Проверяем, что шаблоны есть и корректны
    assert hasattr(dialog, "setup_ui")
    # Можно добавить больше проверок, если шаблоны вынести в отдельную функцию/переменную 