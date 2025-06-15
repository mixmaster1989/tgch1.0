import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from utils import save_project, load_project, export_to_file

class SettingsDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Настройки")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        # Стили
        ttk.Label(
            self.dialog,
            text="Настройки",
            style="Header.TLabel"
        ).pack(pady=10)
        
        # Тема
        theme_frame = ttk.Frame(self.dialog)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(
            theme_frame,
            text="Тема:"
        ).pack(side=tk.LEFT)
        
        self.theme_var = tk.StringVar(value="light")
        ttk.Radiobutton(
            theme_frame,
            text="Светлая",
            variable=self.theme_var,
            value="light"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            theme_frame,
            text="Тёмная",
            variable=self.theme_var,
            value="dark"
        ).pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=20)
        
        ttk.Button(
            btn_frame,
            text="Сохранить",
            command=self.save,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
    def save(self):
        # TODO: Сохранение настроек
        self.dialog.destroy()

class HelpDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Справка")
        self.dialog.geometry("600x400")
        
        # Заголовок
        ttk.Label(
            self.dialog,
            text="Справка по PineSlicer",
            style="Header.TLabel"
        ).pack(pady=10)
        
        # Текст справки
        text = tk.Text(
            self.dialog,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_text = """
        PineSlicer - это визуальный конструктор кода для Pine Script.
        
        Основные возможности:
        1. Создание блоков кода
        2. Настройка параметров блоков
        3. Предпросмотр сгенерированного кода
        4. Сохранение и загрузка проектов
        5. Экспорт кода в файл
        
        Как использовать:
        1. Нажмите "Добавить блок" для создания нового блока
        2. Выберите тип блока из выпадающего списка
        3. Заполните параметры блока
        4. Переключитесь на вкладку "Предпросмотр" для просмотра кода
        5. Используйте кнопку "Копировать код" для копирования в буфер обмена
        
        Сохранение проекта:
        - Используйте меню "Файл" -> "Сохранить проект"
        - Проекты сохраняются в формате JSON
        
        Экспорт кода:
        - Используйте меню "Файл" -> "Экспорт кода"
        - Код экспортируется в файл .pine
        """
        
        text.insert(1.0, help_text)
        text.config(state=tk.DISABLED)
        
        # Кнопка закрытия
        ttk.Button(
            self.dialog,
            text="Закрыть",
            command=self.dialog.destroy,
            style="Accent.TButton"
        ).pack(pady=10)

def show_save_dialog(parent, blocks):
    """Диалог сохранения проекта"""
    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if filename:
        if save_project(blocks, filename):
            messagebox.showinfo("Успех", "Проект успешно сохранен")

def show_load_dialog(parent):
    """Диалог загрузки проекта"""
    filename = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if filename:
        return load_project(filename)
    return None

def show_export_dialog(parent, code):
    """Диалог экспорта кода"""
    filename = filedialog.asksaveasfilename(
        defaultextension=".pine",
        filetypes=[("Pine Script files", "*.pine"), ("All files", "*.*")]
    )
    if filename:
        if export_to_file(code, filename):
            messagebox.showinfo("Успех", "Код успешно экспортирован") 