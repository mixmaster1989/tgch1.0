import logging
import asyncio
import json
import os
from datetime import datetime
from .config import crypto_config
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import io

# Настройка логирования
logger = logging.getLogger(__name__)

class SignalDispatcher:
    """
    Диспетчер сигналов для отправки уведомлений в Telegram
    """
    def __init__(self, bot=None):
        """
        Инициализация диспетчера сигналов
        
        Args:
            bot: Экземпляр бота Telegram
        """
        self.bot = bot
        self.config = crypto_config
        self.signals_enabled = self.config.get('signals', {}).get('enabled', True)
        self.channel_id = self.config.get('signals', {}).get('channel_id')
        self.include_charts = self.config.get('signals', {}).get('include_charts', True)
        
        # Кэш для отправленных сигналов
        self.sent_signals = {}
        self.cooldown = self.config.get('signals', {}).get('notification_cooldown', 3600)
        
        # Создаем директорию для хранения графиков
        self.charts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'charts')
        os.makedirs(self.charts_dir, exist_ok=True)
    
    def set_bot(self, bot):
        """
        Устанавливает экземпляр бота Telegram
        
        Args:
            bot: Экземпляр бота Telegram
        """
        self.bot = bot
    
    async def dispatch_signals(self, analysis_results):
        """
        Отправляет сигналы на основе результатов анализа
        
        Args:
            analysis_results (dict): Результаты анализа
            
        Returns:
            int: Количество отправленных сигналов
        """
        if not self.signals_enabled or not self.channel_id or not self.bot:
            logger.warning("Отправка сигналов отключена или не настроена")
            return 0
        
        sent_count = 0
        
        for pair, results in analysis_results.items():
            signals = results.get("signals", [])
            
            if not signals:
                continue
            
            # Группируем сигналы по типу
            grouped_signals = {}
            for signal in signals:
                signal_type = signal.get("type")
                if signal_type not in grouped_signals:
                    grouped_signals[signal_type] = []
                grouped_signals[signal_type].append(signal)
            
            # Обрабатываем каждый тип сигнала
            for signal_type, type_signals in grouped_signals.items():
                # Определяем общее направление сигналов
                long_count = sum(1 for s in type_signals if s.get("direction") == "long")
                short_count = sum(1 for s in type_signals if s.get("direction") == "short")
                
                direction = "long" if long_count > short_count else "short"
                
                # Формируем ключ для проверки кулдауна
                cooldown_key = f"{pair}_{signal_type}_{direction}"
                
                # Проверяем, не было ли недавно отправлено такое же уведомление
                current_time = datetime.now().timestamp()
                last_sent_time = self.sent_signals.get(cooldown_key, 0)
                
                if current_time - last_sent_time < self.cooldown:
                    logger.info(f"Сигнал {cooldown_key} находится в кулдауне, пропускаем")
                    continue
                
                # Формируем сообщение
                message = self._format_signal_message(pair, results["price"], signal_type, type_signals, direction)
                
                # Отправляем сообщение
                try:
                    if self.include_charts:
                        # Генерируем график
                        chart_path = await self._generate_chart(pair, direction)
                        
                        if chart_path:
                            # Отправляем сообщение с изображением
                            with open(chart_path, 'rb') as photo:
                                await self.bot.send_photo(
                                    chat_id=self.channel_id,
                                    photo=photo,
                                    caption=message
                                )
                        else:
                            # Если не удалось создать график, отправляем только текст
                            await self.bot.send_message(
                                chat_id=self.channel_id,
                                text=message
                            )
                    else:
                        # Отправляем только текстовое сообщение
                        await self.bot.send_message(
                            chat_id=self.channel_id,
                            text=message
                        )
                    
                    # Обновляем время последней отправки
                    self.sent_signals[cooldown_key] = current_time
                    sent_count += 1
                    
                    logger.info(f"Отправлен сигнал {cooldown_key}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сигнала {cooldown_key}: {e}")
        
        return sent_count
    
    def _format_signal_message(self, pair, price, signal_type, signals, direction):
        """
        Форматирует сообщение с сигналом
        
        Args:
            pair (str): Торговая пара
            price (float): Текущая цена
            signal_type (str): Тип сигнала
            signals (list): Список сигналов
            direction (str): Направление (long/short)
            
        Returns:
            str: Отформатированное сообщение
        """
        # Эмодзи для направления
        direction_emoji = "🟢" if direction == "long" else "🔴"
        
        # Заголовок сообщения
        header = f"{direction_emoji} **{pair}** - {direction.upper()} SIGNAL\n\n"
        
        # Текущая цена
        price_text = f"💰 Current Price: ${price:.2f}\n\n"
        
        # Тип сигнала
        signal_type_text = ""
        if signal_type == "volume_spike":
            signal_type_text = "📊 Volume Spike Detected"
        elif signal_type == "open_interest_change":
            signal_type_text = "📈 Open Interest Change"
        elif signal_type == "funding_rate":
            signal_type_text = "💸 Funding Rate Signal"
        elif signal_type == "whale_transaction":
            signal_type_text = "🐋 Whale Transaction"
        elif signal_type == "liquidity_zone":
            signal_type_text = "💧 Liquidity Zone"
        else:
            signal_type_text = f"📊 {signal_type.replace('_', ' ').title()}"
        
        # Детали сигнала
        details = ""
        
        if signal_type == "volume_spike":
            # Берем сигнал с наибольшим соотношением объема
            strongest_signal = max(signals, key=lambda s: s.get("ratio", 0))
            volume = strongest_signal.get("volume", 0)
            avg_volume = strongest_signal.get("avg_volume", 0)
            ratio = strongest_signal.get("ratio", 0)
            timeframe = strongest_signal.get("timeframe", "")
            
            details = (
                f"Timeframe: {timeframe}\n"
                f"Volume: ${volume:,.0f}\n"
                f"Avg Volume: ${avg_volume:,.0f}\n"
                f"Ratio: {ratio:.2f}x"
            )
        
        elif signal_type == "open_interest_change":
            # Берем сигнал с наибольшим изменением
            strongest_signal = max(signals, key=lambda s: abs(s.get("change_percent", 0)))
            current_oi = strongest_signal.get("current_oi", 0)
            previous_oi = strongest_signal.get("previous_oi", 0)
            change_percent = strongest_signal.get("change_percent", 0)
            
            details = (
                f"Current OI: {current_oi:,.0f}\n"
                f"Previous OI: {previous_oi:,.0f}\n"
                f"Change: {change_percent:+.2f}%"
            )
        
        elif signal_type == "funding_rate":
            # Берем сигнал с наибольшей ставкой
            strongest_signal = max(signals, key=lambda s: abs(s.get("funding_rate", 0)))
            funding_rate = strongest_signal.get("funding_rate", 0)
            
            details = f"Funding Rate: {funding_rate:+.4f}%"
        
        elif signal_type == "whale_transaction":
            # Суммируем объемы транзакций
            total_amount = sum(s.get("amount", 0) for s in signals)
            total_amount_usd = sum(s.get("amount_usd", 0) for s in signals)
            tx_count = len(signals)
            
            details = (
                f"Transactions: {tx_count}\n"
                f"Total Amount: {total_amount:.4f} {pair.replace('USDT', '')}\n"
                f"Total USD: ${total_amount_usd:,.2f}"
            )
        
        elif signal_type == "liquidity_zone":
            # Берем сигнал с наибольшим объемом
            strongest_signal = max(signals, key=lambda s: s.get("volume", 0))
            price_level = strongest_signal.get("price_level", 0)
            volume = strongest_signal.get("volume", 0)
            distance_percent = strongest_signal.get("distance_percent", 0)
            
            details = (
                f"Price Level: ${price_level:.2f}\n"
                f"Volume: ${volume:,.0f}\n"
                f"Distance: {distance_percent:.2f}% from current price"
            )
        
        # Формируем полное сообщение
        message = f"{header}{price_text}{signal_type_text}\n\n{details}\n\n"
        
        # Добавляем рекомендацию
        if direction == "long":
            message += "🔼 Potential upward movement expected"
        else:
            message += "🔽 Potential downward movement expected"
        
        # Добавляем дисклеймер
        message += "\n\n⚠️ This is not financial advice. Trade at your own risk."
        
        return message
    
    async def _generate_chart(self, pair, direction):
        """
        Генерирует график для сигнала
        
        Args:
            pair (str): Торговая пара
            direction (str): Направление (long/short)
            
        Returns:
            str: Путь к сгенерированному графику
        """
        try:
            # Получаем данные для графика
            from .data_sources import BinanceDataSource
            binance = BinanceDataSource()
            await binance.initialize()
            
            # Получаем свечи для 1-дневного графика
            klines = await binance.get_klines(pair, "1d", limit=30)
            
            if not klines:
                logger.error(f"Не удалось получить данные для графика {pair}")
                await binance.close()
                return None
            
            # Подготавливаем данные для графика
            dates = [datetime.fromtimestamp(k["open_time"]/1000) for k in klines]
            opens = [k["open"] for k in klines]
            highs = [k["high"] for k in klines]
            lows = [k["low"] for k in klines]
            closes = [k["close"] for k in klines]
            volumes = [k["volume"] for k in klines]
            
            # Создаем график
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})
            
            # Настраиваем цвета
            up_color = 'green'
            down_color = 'red'
            
            # Рисуем свечи
            for i in range(len(dates)):
                # Определяем цвет свечи
                if closes[i] >= opens[i]:
                    color = up_color
                    body_bottom = opens[i]
                    body_top = closes[i]
                else:
                    color = down_color
                    body_bottom = closes[i]
                    body_top = opens[i]
                
                # Рисуем тело свечи
                ax1.add_patch(plt.Rectangle((i-0.4, body_bottom), 0.8, body_top-body_bottom, fill=True, color=color))
                
                # Рисуем верхний и нижний фитили
                ax1.plot([i, i], [body_top, highs[i]], color=color, linewidth=1)
                ax1.plot([i, i], [body_bottom, lows[i]], color=color, linewidth=1)
            
            # Добавляем объемы
            for i in range(len(dates)):
                if closes[i] >= opens[i]:
                    ax2.bar(i, volumes[i], color=up_color, alpha=0.7, width=0.8)
                else:
                    ax2.bar(i, volumes[i], color=down_color, alpha=0.7, width=0.8)
            
            # Настраиваем оси
            ax1.set_xticks(range(0, len(dates), 5))
            ax1.set_xticklabels([d.strftime('%Y-%m-%d') for d in dates[::5]], rotation=45)
            ax1.grid(True, alpha=0.3)
            ax1.set_title(f"{pair} - {direction.upper()} Signal", fontsize=14)
            
            ax2.set_xticks(range(0, len(dates), 5))
            ax2.set_xticklabels([d.strftime('%Y-%m-%d') for d in dates[::5]], rotation=45)
            ax2.grid(True, alpha=0.3)
            ax2.set_ylabel('Volume')
            
            # Добавляем скользящие средние
            ma20 = np.convolve(closes, np.ones(20)/20, mode='valid')
            ma50 = np.convolve(closes, np.ones(50)/50, mode='valid')
            
            if len(ma20) > 0:
                ax1.plot(range(19, len(closes)), ma20, color='blue', linewidth=1.5, label='MA20')
            
            if len(ma50) > 0:
                ax1.plot(range(49, len(closes)), ma50, color='orange', linewidth=1.5, label='MA50')
            
            ax1.legend()
            
            # Добавляем текущую цену
            current_price = closes[-1]
            ax1.axhline(y=current_price, color='black', linestyle='--', alpha=0.7)
            ax1.text(len(dates)-1, current_price, f" ${current_price:.2f}", va='center')
            
            # Настраиваем внешний вид
            plt.tight_layout()
            
            # Сохраняем график
            chart_filename = f"{pair}_{direction}_{int(datetime.now().timestamp())}.png"
            chart_path = os.path.join(self.charts_dir, chart_filename)
            plt.savefig(chart_path)
            plt.close(fig)
            
            await binance.close()
            
            return chart_path
        except Exception as e:
            logger.error(f"Ошибка при генерации графика: {e}")
            return None