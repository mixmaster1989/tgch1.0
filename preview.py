"""
Модуль для предварительного просмотра индикаторов
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QComboBox, QLineEdit, QTextEdit, QFrame, QDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QPixmap, QLinearGradient, QBrush
import random
import math

class PreviewWidget(QWidget):
    """Виджет для предварительного просмотра индикатора"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.data = self._generate_data(100)
        self.indicators = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Обновление каждую секунду
    
    def _generate_data(self, count):
        """Генерирует случайные данные для графика"""
        data = []
        price = 100.0
        for i in range(count):
            open_price = price
            high_price = open_price + random.uniform(0, 5)
            low_price = open_price - random.uniform(0, 5)
            close_price = random.uniform(low_price, high_price)
            volume = random.uniform(1000, 10000)
            data.append({
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            })
            price = close_price
        return data
    
    def update_data(self):
        """Обновляет данные графика"""
        if len(self.data) > 100:
            self.data.pop(0)
        
        last_price = self.data[-1]["close"]
        open_price = last_price
        high_price = open_price + random.uniform(0, 5)
        low_price = open_price - random.uniform(0, 5)
        close_price = random.uniform(low_price, high_price)
        volume = random.uniform(1000, 10000)
        
        self.data.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        })
        
        self.update()
    
    def add_indicator(self, indicator_type, params=None):
        """Добавляет индикатор для отображения"""
        self.indicators.append({
            "block_type": indicator_type,
            "params": params or {}
        })
        self.update()
    
    def clear_indicators(self):
        """Очищает все индикаторы"""
        self.indicators = []
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка графика"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Фон
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        
        # Если нет данных, выходим
        if not self.data:
            return
        
        # Размеры области отрисовки
        width = self.width()
        height = self.height()
        padding = 40
        chart_width = width - 2 * padding
        chart_height = height - 2 * padding
        
        # Находим минимальные и максимальные значения
        min_price = min(candle["low"] for candle in self.data)
        max_price = max(candle["high"] for candle in self.data)
        price_range = max_price - min_price
        
        # Добавляем отступы сверху и снизу
        min_price -= price_range * 0.1
        max_price += price_range * 0.1
        price_range = max_price - min_price
        
        # Рисуем сетку
        painter.setPen(QPen(QColor("#333333"), 1, Qt.DashLine))
        for i in range(5):
            y = padding + i * chart_height / 4
            painter.drawLine(int(padding), int(y), int(width - padding), int(y))
            price = max_price - i * price_range / 4
            painter.setPen(QPen(QColor("#666666"), 1))
            painter.drawText(5, int(y + 5), f"{price:.2f}")
            painter.setPen(QPen(QColor("#333333"), 1, Qt.DashLine))
        
        # Рисуем свечи
        candle_width = chart_width / len(self.data)
        for i, candle in enumerate(self.data):
            x = padding + i * candle_width
            
            # Преобразуем цены в координаты
            open_y = padding + chart_height * (1 - (candle["open"] - min_price) / price_range)
            close_y = padding + chart_height * (1 - (candle["close"] - min_price) / price_range)
            high_y = padding + chart_height * (1 - (candle["high"] - min_price) / price_range)
            low_y = padding + chart_height * (1 - (candle["low"] - min_price) / price_range)
            
            # Определяем цвет свечи
            if candle["close"] >= candle["open"]:
                candle_color = QColor("#4CAF50")  # Зеленый для растущих свечей
            else:
                candle_color = QColor("#F44336")  # Красный для падающих свечей
            
            # Рисуем тело свечи
            painter.setPen(QPen(candle_color, 1))
            painter.setBrush(QBrush(candle_color))
            body_width = max(1, candle_width * 0.8)
            painter.drawRect(int(x + (candle_width - body_width) / 2), int(min(open_y, close_y)), 
                           int(body_width), int(abs(close_y - open_y) or 1))
            
            # Рисуем тени
            center_x = x + candle_width / 2
            painter.drawLine(int(center_x), int(high_y), int(center_x), int(min(open_y, close_y)))
            painter.drawLine(int(center_x), int(max(open_y, close_y)), int(center_x), int(low_y))
        
        # Рисуем индикаторы
        for indicator in self.indicators:
            if indicator["block_type"] == "Скользящая средняя":
                self._draw_ma(painter, indicator["params"], padding, chart_width, chart_height, min_price, price_range)
            elif indicator["block_type"] == "RSI":
                self._draw_rsi(painter, indicator["params"], padding, chart_width, chart_height)
            elif indicator["block_type"] == "MACD":
                self._draw_macd(painter, indicator["params"], padding, chart_width, chart_height)
            elif indicator["block_type"] == "Bollinger Bands":
                self._draw_bollinger(painter, indicator["params"], padding, chart_width, chart_height, min_price, price_range)
    
    def _draw_ma(self, painter, params, padding, chart_width, chart_height, min_price, price_range):
        """Рисует скользящую среднюю"""
        period = int(params.get("Период", "14"))
        ma_type = params.get("Тип", "EMA")
        
        # Рассчитываем MA
        ma_values = []
        for i in range(len(self.data)):
            if i < period - 1:
                ma_values.append(None)
                continue
            
            # Простая реализация для демонстрации
            if ma_type == "SMA":
                values = [self.data[j]["close"] for j in range(i - period + 1, i + 1)]
                ma_values.append(sum(values) / len(values))
            else:  # EMA и другие типы для простоты реализуем как SMA
                values = [self.data[j]["close"] for j in range(i - period + 1, i + 1)]
                ma_values.append(sum(values) / len(values))
        
        # Рисуем линию MA
        painter.setPen(QPen(QColor("#2196F3"), 2))
        path_points = []
        for i, ma in enumerate(ma_values):
            if ma is None:
                continue
            
            x = padding + i * chart_width / len(self.data)
            y = padding + chart_height * (1 - (ma - min_price) / price_range)
            
            if not path_points:
                path_points.append((x, y))
            else:
                painter.drawLine(int(path_points[-1][0]), int(path_points[-1][1]), int(x), int(y))
                path_points.append((x, y))
    
    def _draw_rsi(self, painter, params, padding, chart_width, chart_height):
        """Рисует RSI"""
        # Для демонстрации просто рисуем случайную линию в нижней части графика
        painter.setPen(QPen(QColor("#9C27B0"), 2))
        
        # Рисуем область RSI
        rsi_height = chart_height * 0.2
        rsi_top = padding + chart_height - rsi_height
        
        # Рисуем фон
        painter.fillRect(int(padding), int(rsi_top), int(chart_width), int(rsi_height), QColor("#2b2b2b"))
        
        # Рисуем уровни
        painter.setPen(QPen(QColor("#666666"), 1, Qt.DashLine))
        painter.drawLine(int(padding), int(rsi_top + rsi_height * 0.3), int(padding + chart_width), int(rsi_top + rsi_height * 0.3))  # Уровень 70
        painter.drawLine(int(padding), int(rsi_top + rsi_height * 0.7), int(padding + chart_width), int(rsi_top + rsi_height * 0.7))  # Уровень 30
        
        # Рисуем линию RSI
        painter.setPen(QPen(QColor("#9C27B0"), 2))
        prev_x = padding
        prev_y = rsi_top + rsi_height / 2
        for i in range(1, 100):
            x = padding + i * chart_width / 100
            y = rsi_top + rsi_height / 2 + math.sin(i / 10) * rsi_height / 4
            painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x = x
            prev_y = y
    
    def _draw_macd(self, painter, params, padding, chart_width, chart_height):
        """Рисует MACD"""
        # Для демонстрации просто рисуем случайные линии и гистограмму в нижней части графика
        
        # Рисуем область MACD
        macd_height = chart_height * 0.2
        macd_top = padding + chart_height - macd_height
        
        # Рисуем фон
        painter.fillRect(int(padding), int(macd_top), int(chart_width), int(macd_height), QColor("#2b2b2b"))
        
        # Рисуем нулевую линию
        painter.setPen(QPen(QColor("#666666"), 1, Qt.DashLine))
        painter.drawLine(int(padding), int(macd_top + macd_height / 2), int(padding + chart_width), int(macd_top + macd_height / 2))
        
        # Рисуем линию MACD
        painter.setPen(QPen(QColor("#2196F3"), 2))
        prev_x = padding
        prev_y = macd_top + macd_height / 2
        for i in range(1, 100):
            x = padding + i * chart_width / 100
            y = macd_top + macd_height / 2 + math.sin(i / 15) * macd_height / 4
            painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x = x
            prev_y = y
        
        # Рисуем сигнальную линию
        painter.setPen(QPen(QColor("#F44336"), 2))
        prev_x = padding
        prev_y = macd_top + macd_height / 2
        for i in range(1, 100):
            x = padding + i * chart_width / 100
            y = macd_top + macd_height / 2 + math.sin(i / 15 + 1) * macd_height / 4
            painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
            prev_x = x
            prev_y = y
        
        # Рисуем гистограмму
        painter.setPen(QPen(QColor("#4CAF50"), 1))
        for i in range(100):
            x = padding + i * chart_width / 100
            height = math.sin(i / 15) * macd_height / 4 - math.sin(i / 15 + 1) * macd_height / 4
            if height > 0:
                painter.setBrush(QBrush(QColor("#4CAF50")))
            else:
                painter.setBrush(QBrush(QColor("#F44336")))
            painter.drawRect(int(x), int(macd_top + macd_height / 2), int(chart_width / 100), int(height))
    
    def _draw_bollinger(self, painter, params, padding, chart_width, chart_height, min_price, price_range):
        """Рисует полосы Боллинджера"""
        period = int(params.get("Период", "20"))
        multiplier = float(params.get("Множитель", "2.0"))
        
        # Рассчитываем SMA
        sma_values = []
        upper_values = []
        lower_values = []
        
        for i in range(len(self.data)):
            if i < period - 1:
                sma_values.append(None)
                upper_values.append(None)
                lower_values.append(None)
                continue
            
            values = [self.data[j]["close"] for j in range(i - period + 1, i + 1)]
            sma = sum(values) / len(values)
            std = math.sqrt(sum((x - sma) ** 2 for x in values) / len(values))
            
            sma_values.append(sma)
            upper_values.append(sma + multiplier * std)
            lower_values.append(sma - multiplier * std)
        
        # Рисуем средние линии
        painter.setPen(QPen(QColor("#2196F3"), 2))
        path_points = []
        for i, sma in enumerate(sma_values):
            if sma is None:
                continue
            
            x = padding + i * chart_width / len(self.data)
            y = padding + chart_height * (1 - (sma - min_price) / price_range)
            
            if not path_points:
                path_points.append((x, y))
            else:
                painter.drawLine(int(path_points[-1][0]), int(path_points[-1][1]), int(x), int(y))
                path_points.append((x, y))
        
        # Рисуем верхнюю линию
        painter.setPen(QPen(QColor("#F44336"), 2))
        path_points = []
        for i, upper in enumerate(upper_values):
            if upper is None:
                continue
            
            x = padding + i * chart_width / len(self.data)
            y = padding + chart_height * (1 - (upper - min_price) / price_range)
            
            if not path_points:
                path_points.append((x, y))
            else:
                painter.drawLine(int(path_points[-1][0]), int(path_points[-1][1]), int(x), int(y))
                path_points.append((x, y))
        
        # Рисуем нижнюю линию
        painter.setPen(QPen(QColor("#4CAF50"), 2))
        path_points = []
        for i, lower in enumerate(lower_values):
            if lower is None:
                continue
            
            x = padding + i * chart_width / len(self.data)
            y = padding + chart_height * (1 - (lower - min_price) / price_range)
            
            if not path_points:
                path_points.append((x, y))
            else:
                painter.drawLine(int(path_points[-1][0]), int(path_points[-1][1]), int(x), int(y))
                path_points.append((x, y))

class PreviewDialog(QDialog):
    """Диалог предварительного просмотра индикатора"""
    
    def __init__(self, blocks, parent=None):
        super().__init__(parent)
        self.blocks = blocks
        self.setWindowTitle("Предварительный просмотр индикатора")
        self.setMinimumSize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Предварительный просмотр индикатора")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Виджет предпросмотра
        self.preview = PreviewWidget()
        layout.addWidget(self.preview)
        
        # Добавляем индикаторы
        for block in self.blocks:
            if block.block_type in ["Скользящая средняя", "RSI", "MACD", "Bollinger Bands"]:
                self.preview.add_indicator(block.block_type, block.params)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)