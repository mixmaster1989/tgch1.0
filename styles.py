from tkinter import ttk
import tkinter as tk

def setup_styles():
    style = ttk.Style()
    
    # Основной стиль для блоков
    style.configure(
        "Block.TFrame",
        background="#ffffff",
        relief="solid",
        borderwidth=1
    )
    
    # Стиль при наведении на блок
    style.configure(
        "BlockHover.TFrame",
        background="#f0f0f0",
        relief="solid",
        borderwidth=1
    )
    
    # Стиль для заголовков
    style.configure(
        "Header.TLabel",
        font=("Arial", 12, "bold"),
        padding=5
    )
    
    # Стиль для кнопок
    style.configure(
        "Accent.TButton",
        font=("Arial", 10),
        padding=10,
        background="#007bff",
        foreground="white"
    )
    
    # Стиль для вкладок
    style.configure(
        "TNotebook",
        background="#ffffff",
        borderwidth=0
    )
    
    style.configure(
        "TNotebook.Tab",
        padding=[10, 5],
        font=("Arial", 10)
    )
    
    # Стиль для полей ввода
    style.configure(
        "TEntry",
        padding=5,
        relief="solid",
        borderwidth=1
    ) 