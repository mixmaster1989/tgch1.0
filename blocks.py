import tkinter as tk
from tkinter import ttk
from constants import BLOCK_TYPES

class Block(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Block.TFrame")
        
        # Заголовок блока
        self.header = ttk.Frame(self)
        self.header.pack(fill=tk.X, padx=5, pady=5)
        
        # Выпадающий список типов блоков
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            self.header,
            textvariable=self.type_var,
            values=list(BLOCK_TYPES.keys()),
            state="readonly"
        )
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_change)
        
        # Help иконка
        self.help_btn = ttk.Label(
            self.header,
            text="❓",
            cursor="hand2"
        )
        self.help_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка удаления
        self.delete_btn = ttk.Button(
            self.header,
            text="❌",
            command=self.destroy,
            width=3
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        
        # Кнопка дублирования
        self.duplicate_btn = ttk.Button(
            self.header,
            text="📋",
            command=self.duplicate,
            width=3
        )
        self.duplicate_btn.pack(side=tk.RIGHT, padx=5)
        
        # Контейнер для параметров
        self.params_frame = ttk.Frame(self)
        self.params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Привязываем события мыши
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
        # Drag&Drop
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Подсказка
        self.tooltip = None
        
    def on_enter(self, event):
        self.configure(style="BlockHover.TFrame")
        # Показываем подсказку
        if self.type_var.get() in BLOCK_TYPES:
            self.show_tooltip(BLOCK_TYPES[self.type_var.get()]["description"])
        
    def on_leave(self, event):
        self.configure(style="Block.TFrame")
        # Скрываем подсказку
        self.hide_tooltip()
        
    def show_tooltip(self, text):
        x, y, _, _ = self.bbox("all")
        x += self.winfo_rootx() + 25
        y += self.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(
            self.tooltip,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1
        )
        label.pack()
        
    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            
    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def on_drag(self, event):
        if not hasattr(self, '_drag_start_x'):
            return
            
        # Вычисляем смещение
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        
        # Получаем текущую позицию
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        
        # Перемещаем блок
        self.place(x=x, y=y)
        
    def stop_drag(self, event):
        if hasattr(self, '_drag_start_x'):
            del self._drag_start_x
            del self._drag_start_y
            
    def duplicate(self):
        """Дублирование блока"""
        new_block = Block(self.master)
        new_block.set_data(self.get_data())
        new_block.pack(fill=tk.X, pady=5)
        return new_block
        
    def on_type_change(self, event):
        # Очищаем старые параметры
        for widget in self.params_frame.winfo_children():
            widget.destroy()
            
        # Добавляем новые параметры в зависимости от типа
        block_type = self.type_var.get()
        if block_type in BLOCK_TYPES:
            params = BLOCK_TYPES[block_type]["params"]
            for param in params:
                self.add_param(param)
                
    def add_param(self, param):
        frame = ttk.Frame(self.params_frame)
        frame.pack(fill=tk.X, pady=2)
        
        label = ttk.Label(frame, text=param["name"])
        label.pack(side=tk.LEFT, padx=5)
        
        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
    def get_data(self):
        return {
            "type": self.type_var.get(),
            "params": {
                widget.winfo_children()[0]["text"]: widget.winfo_children()[1].get()
                for widget in self.params_frame.winfo_children()
            }
        }
        
    def set_data(self, data):
        """Загрузка данных блока"""
        self.type_var.set(data["type"])
        self.on_type_change(None)  # Обновляем параметры
        
        # Заполняем значения параметров
        for widget in self.params_frame.winfo_children():
            param_name = widget.winfo_children()[0]["text"]
            if param_name in data["params"]:
                widget.winfo_children()[1].delete(0, tk.END)
                widget.winfo_children()[1].insert(0, data["params"][param_name]) 