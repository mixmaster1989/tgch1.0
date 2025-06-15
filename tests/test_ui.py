import pytest
from PyQt5.QtWidgets import QApplication
from ui import MainWindow

@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window

def test_add_block_and_generate_code(app, qtbot):
    # Нажать кнопку "Добавить блок"
    add_btn = app.findChild(type(app).findChild, "➕ Добавить блок")
    assert add_btn is not None
    qtbot.mouseClick(add_btn, qtbot.LeftButton)
    # Открывается диалог выбора блока — эмулируем выбор первого блока
    dialog = app.findChild(type(app).findChild, "BlockSelectDialog")
    assert dialog is not None
    # Выбираем первый тип блока
    first_card = dialog.findChild(type(dialog).findChild)
    qtbot.mouseClick(first_card, qtbot.LeftButton)
    # Проверяем, что блок добавился
    assert len(app.blocks) == 1
    # Нажать "Сгенерировать код"
    gen_btn = app.findChild(type(app).findChild, "⚡ Сгенерировать код")
    qtbot.mouseClick(gen_btn, qtbot.LeftButton)
    # Проверить, что код появился
    assert "//@version=5" in app.code_area.toPlainText()

def test_export_import_ui(app, qtbot, tmp_path):
    # Добавить блок
    app.create_block(list(app.blocks_area.children())[0].type)
    # Экспорт
    file = tmp_path / "settings.json"
    app.export_settings = lambda: file.write_text("[]")
    app.export_settings()
    assert file.exists()
    # Импорт
    app.import_settings = lambda: file.read_text()
    data = app.import_settings()
    assert data == "[]" 