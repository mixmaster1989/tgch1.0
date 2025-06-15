import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext

class CodePreview:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        self.header = ttk.Label(
            self.frame,
            text="Предпросмотр кода",
            style="Header.TLabel"
        )
        self.header.pack(fill=tk.X, pady=(0, 10))
        
        # Текстовое поле с прокруткой
        self.text = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            width=80,
            height=30,
            font=("Consolas", 10)
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка копирования
        self.copy_btn = ttk.Button(
            self.frame,
            text="Копировать код",
            command=self.copy_code,
            style="Accent.TButton"
        )
        self.copy_btn.pack(pady=10)
        
    def update_code(self, code):
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, code)
        
    def copy_code(self):
        code = self.text.get(1.0, tk.END)
        self.frame.clipboard_clear()
        self.frame.clipboard_append(code) 