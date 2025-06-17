"""
Модуль для автосохранения проекта
"""

import os
import json
import threading
import time
import logging
from datetime import datetime

class AutoSave:
    """Класс для автоматического сохранения проекта"""
    
    def __init__(self, save_interval=300, autosave_file="autosave.json"):
        """
        Инициализация автосохранения
        
        Args:
            save_interval (int): Интервал автосохранения в секундах
            autosave_file (str): Имя файла для автосохранения
        """
        self.save_interval = save_interval
        self.autosave_file = autosave_file
        self.running = False
        self.thread = None
        self.get_blocks_callback = None
    
    def start(self, get_blocks_callback):
        """
        Запуск автосохранения
        
        Args:
            get_blocks_callback (callable): Функция для получения блоков
        """
        if self.running:
            return
        
        self.get_blocks_callback = get_blocks_callback
        self.running = True
        self.thread = threading.Thread(target=self._autosave_loop)
        self.thread.daemon = True
        self.thread.start()
        logging.info(f"Автосохранение запущено с интервалом {self.save_interval} секунд")
    
    def stop(self):
        """Остановка автосохранения"""
        self.running = False
        if self.thread:
            self.thread.join(1.0)
            self.thread = None
        logging.info("Автосохранение остановлено")
    
    def _autosave_loop(self):
        """Цикл автосохранения"""
        while self.running:
            try:
                time.sleep(self.save_interval)
                if self.running and self.get_blocks_callback:
                    self._save_blocks()
            except Exception as e:
                logging.error(f"Ошибка при автосохранении: {str(e)}")
    
    def _save_blocks(self):
        """Сохранение блоков"""
        try:
            blocks = self.get_blocks_callback()
            if not blocks:
                return
            
            # Преобразуем блоки в JSON
            settings = []
            for block in blocks:
                settings.append(block.get_data())
            
            # Создаем директорию для автосохранения, если она не существует
            autosave_dir = os.path.dirname(self.autosave_file)
            if autosave_dir and not os.path.exists(autosave_dir):
                os.makedirs(autosave_dir)
            
            # Сохраняем в файл
            with open(self.autosave_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            logging.info(f"Автосохранение выполнено: {len(blocks)} блоков сохранено в {self.autosave_file}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении блоков: {str(e)}")
    
    def load_autosave(self, block_class):
        """
        Загрузка автосохраненных блоков
        
        Args:
            block_class: Класс блока для создания экземпляров
            
        Returns:
            list: Список загруженных блоков или None, если файл не найден
        """
        try:
            if not os.path.exists(self.autosave_file):
                return None
            
            # Загружаем данные из файла
            with open(self.autosave_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Создаем блоки
            blocks = []
            for s in settings:
                if "block_type" in s and "params" in s:
                    block = block_class(s["block_type"], s["params"])
                    blocks.append(block)
            
            logging.info(f"Загружено {len(blocks)} блоков из автосохранения: {self.autosave_file}")
            return blocks
        except Exception as e:
            logging.error(f"Ошибка при загрузке автосохранения: {str(e)}")
            return None

# Создаем экземпляр автосохранения
autosave = AutoSave()