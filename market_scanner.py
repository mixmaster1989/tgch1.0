#!/usr/bin/env python3
"""
Фоновый сканер рынка
Анализирует рынок каждые 5 минут и отправляет результаты в Telegram
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from mex_api import MexAPI
from technical_indicators import TechnicalIndicators
from anti_hype_filter import AntiHypeFilter
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, EXCLUDED_SYMBOLS, PURCHASE_PCT_OF_USDT, PURCHASE_MIN_USDT, PURCHASE_MAX_USDT

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketScanner:
    """Фоновый сканер рынка"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.tech_indicators = TechnicalIndicators()
        self.anti_hype_filter = AntiHypeFilter()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Настройки
        self.scan_interval = 600  # 10 минут (увеличено в 2 раза для отчетов)
        self.max_pairs = 200  # Максимум пар для анализа (увеличено с 20 до 200)
        
        # Торговые пары для анализа (будет заполнено динамически)
        self.trading_pairs = []
        
        # Статистика
        self.scan_count = 0
        self.last_scan_time = None
        
        # Контроль частоты отчетов (уменьшаем спам в 2 раза)
        self.report_counter = 0
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None

    def _build_reasoning(self, opp: Dict) -> Dict[str, str]:
        """Построить развернутые причины и краткосрочный прогноз по возможности покупки."""
        reasons_verbose = []
        rsi = opp.get('rsi', 50)
        macd = opp.get('macd_signal', 'NEUTRAL')
        vol = opp.get('volume_ratio', 1.0)
        bb = opp.get('bb_position', 0.5)
        filt = opp.get('filter_result', {}) or {}
        filt_reason = filt.get('reason')

        if rsi < 30:
            reasons_verbose.append("RSI < 30 — перепроданность, ожидаем технический отскок")
        elif rsi < 45:
            reasons_verbose.append("RSI в нижней зоне — преимущество покупателей при развороте")
        if bb < 0.2:
            reasons_verbose.append("Цена у нижней границы Bollinger — вероятен отскок к средней")
        if vol > 1.5:
            reasons_verbose.append("Объемы выше нормы — повышенная вероятность импульса")
        elif vol > 1.2:
            reasons_verbose.append("Объемы нормализуются — ликвидность достаточна для входа")
        if macd == 'BUY':
            reasons_verbose.append("MACD подает сигнал BUY — подтверждение смены импульса")
        elif macd == 'SELL':
            reasons_verbose.append("MACD SELL — вход только как контртренд с малым риском")
        if filt_reason:
            reasons_verbose.append(f"Анти‑хайп фильтр: {filt_reason}")

        # Простой краткосрочный прогноз
        bullish_signals = sum([
            rsi < 35,
            bb < 0.3,
            macd == 'BUY',
            vol > 1.2
        ])
        if bullish_signals >= 3:
            forecast = "Ожидаю отскок 1–3% в ближайшие 2–6 часов при сохранении объема"
        elif bullish_signals == 2:
            forecast = "Вероятен тех. откат 0.5–2% и возврат к средней полосе"
        elif macd == 'SELL' or rsi > 70 or bb > 0.8:
            forecast = "Риски продолжения снижения/боковика, возможна доборная точка ниже"
        else:
            forecast = "Боковик с уклоном к средним значениям; контроль риска обязателен"

        return {
            'why': "\n   • " + "\n   • ".join(reasons_verbose) if reasons_verbose else "\n   • Техническая конфигурация соответствует правилам входа",
            'forecast': forecast
        }
    
    def get_usdt_balance(self) -> float:
        """Получить баланс USDT"""
        try:
            account_info = self.mex_api.get_account_info()
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDT: {e}")
            return 0.0
    
    def get_top_trading_pairs(self, limit: int = 200) -> List[str]:
        """Получить топ торговых пар по объему торгов"""
        try:
            logger.info(f"🔍 Получение топ {limit} торговых пар...")
            
            # Получаем 24h статистику по всем парам
            tickers = self.mex_api.get_24hr_ticker()
            if not isinstance(tickers, list):
                logger.error("Ошибка получения тикеров")
                return self.get_fallback_pairs()
            
            # Фильтруем только USDT пары с достаточным объемом
            usdt_pairs = []
            for ticker in tickers:
                if (ticker['symbol'].endswith('USDT') and 
                    float(ticker.get('quoteVolume', 0)) > 10000):  # Минимум $10k объема
                    usdt_pairs.append({
                        'symbol': ticker['symbol'],
                        'volume': float(ticker.get('quoteVolume', 0)),
                        'price': float(ticker.get('lastPrice', 0))
                    })
            
            # Сортируем по объему торгов
            usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
            
            # Берем топ пар
            top_pairs = [pair['symbol'] for pair in usdt_pairs[:limit]]
            
            # Исключаем символы из глобального списка EXCLUDED_SYMBOLS
            if EXCLUDED_SYMBOLS:
                excluded_set = set(EXCLUDED_SYMBOLS)
                top_pairs = [s for s in top_pairs if s not in excluded_set]
            
            logger.info(f"✅ Получено {len(top_pairs)} торговых пар")
            logger.info(f"📊 Топ-5 по объему: {top_pairs[:5]}")
            
            return top_pairs
            
        except Exception as e:
            logger.error(f"Ошибка получения торговых пар: {e}")
            return self.get_fallback_pairs()
    
    def get_fallback_pairs(self) -> List[str]:
        """Резервный список торговых пар"""
        return [
            # Исключены BTCUSDT и ETHUSDT
            'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT',
            'ATOMUSDT', 'LTCUSDT', 'XRPUSDT', 'BCHUSDT', 'ETCUSDT',
            'FILUSDT', 'NEARUSDT', 'ALGOUSDT', 'VETUSDT', 'ICPUSDT'
        ]
    
    def update_trading_pairs(self):
        """Обновить список торговых пар"""
        try:
            self.trading_pairs = self.get_top_trading_pairs(self.max_pairs)
            # Дополнительная страховка: исключаем символы из EXCLUDED_SYMBOLS, если вдруг попали
            if EXCLUDED_SYMBOLS:
                excluded_set = set(EXCLUDED_SYMBOLS)
                self.trading_pairs = [s for s in self.trading_pairs if s not in excluded_set]
            logger.info(f"🔄 Список торговых пар обновлен: {len(self.trading_pairs)} пар")
        except Exception as e:
            logger.error(f"Ошибка обновления торговых пар: {e}")
            self.trading_pairs = self.get_fallback_pairs()
    
    def analyze_pair(self, symbol: str) -> Optional[Dict]:
        """Анализ одной торговой пары"""
        try:
            # Получаем свечи (используем поддерживаемый интервал) с локальными ретраями
            klines = None
            for _ in range(3):
                klines = self.mex_api.get_klines(symbol, '15m', 24)
                if klines and len(klines) >= 20:
                    break
                time.sleep(0.4)
            if not klines or len(klines) < 20:
                return None
            
            # Получаем текущую цену (локальные ретраи)
            ticker = None
            for _ in range(3):
                ticker = self.mex_api.get_ticker_price(symbol)
                if ticker and 'price' in ticker:
                    break
                time.sleep(0.3)
            if not ticker or 'price' not in ticker:
                return None
            
            current_price = float(ticker['price'])
            
            # Рассчитываем технические индикаторы
            indicators = self.tech_indicators.calculate_all_indicators(klines, symbol)
            if not indicators:
                return None
            
            # Проверяем анти-хайп фильтр
            filter_result = self.anti_hype_filter.check_buy_permission(symbol)
            
            # Рассчитываем скор
            score = 0
            reasons = []
            
            # RSI анализ
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                score += 3
                reasons.append("перепродано")
            elif rsi < 45:
                score += 2
                reasons.append("низкий_rsi")
            elif rsi > 70:
                score -= 1
                reasons.append("перекуплено")
            
            # Объем анализ
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                score += 2
                reasons.append("высокий_объем")
            elif volume_ratio > 1.2:
                score += 1
                reasons.append("нормальный_объем")
            
            # MACD анализ
            macd_signal = indicators.get('macd_signal', 'NEUTRAL')
            if macd_signal == 'BUY':
                score += 2
                reasons.append("macd_buy")
            elif macd_signal == 'SELL':
                score -= 1
                reasons.append("macd_sell")
            
            # Bollinger Bands анализ
            bb_position = indicators.get('bb_position', 0.5)
            if bb_position < 0.2:
                score += 2
                reasons.append("bb_нижняя")
            elif bb_position > 0.8:
                score -= 1
                reasons.append("bb_верхняя")
            
            # Анти-хайп фильтр
            if not filter_result['allowed']:
                score = -10  # Блокируем покупку
                reasons.append(f"блокирован_{filter_result['reason']}")
            
            # Рассчитываем уверенность
            confidence = max(0.1, min(0.9, (score + 5) / 10))
            
            return {
                'symbol': symbol,
                'price': current_price,
                'score': score,
                'confidence': confidence,
                'reasons': reasons,
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'macd_signal': macd_signal,
                'bb_position': bb_position,
                'filter_result': filter_result,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return None
    
    def scan_market(self) -> Dict:
        """Сканирование всего рынка с параллельной обработкой"""
        try:
            logger.debug("🔍 Начинаю сканирование рынка...")
            
            # Обновляем список торговых пар перед сканированием
            self.update_trading_pairs()
            
            scan_results = {
                'timestamp': datetime.now(),
                'total_pairs': len(self.trading_pairs),
                'analyzed_pairs': 0,
                'buy_opportunities': [],
                'neutral_pairs': [],
                'blocked_pairs': [],
                'errors': []
            }
            
            # Параллельная обработка с ограничением потоков
            max_workers = min(10, len(self.trading_pairs))  # Максимум 10 потоков
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Запускаем анализ всех пар параллельно
                future_to_symbol = {
                    executor.submit(self.analyze_pair, symbol): symbol 
                    for symbol in self.trading_pairs
                }
                
                # Собираем результаты по мере завершения
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        analysis = future.result()
                        if analysis:
                            scan_results['analyzed_pairs'] += 1
                            
                            if analysis['score'] > 2:
                                scan_results['buy_opportunities'].append(analysis)
                            elif analysis['score'] < -5:
                                scan_results['blocked_pairs'].append(analysis)
                            else:
                                scan_results['neutral_pairs'].append(analysis)
                        else:
                            scan_results['errors'].append(symbol)
                            
                    except Exception as e:
                        logger.error(f"Ошибка анализа {symbol}: {e}")
                        scan_results['errors'].append(symbol)
            
            # Сортируем результаты
            scan_results['buy_opportunities'].sort(key=lambda x: x['score'], reverse=True)
            scan_results['neutral_pairs'].sort(key=lambda x: x['score'], reverse=True)
            
            logger.debug(f"✅ Сканирование завершено: {scan_results['analyzed_pairs']} пар проанализировано")
            return scan_results
            
        except Exception as e:
            logger.error(f"Ошибка сканирования рынка: {e}")
            return None
    
    def format_scan_report(self, scan_results: Dict) -> str:
        """Форматирование отчета о сканировании"""
        try:
            usdt_balance = self.get_usdt_balance()
            
            report = f"📊 <b>СКАН РЫНКА #{self.scan_count}</b>\n"
            report += f"⏰ {scan_results['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}\n"
            report += f"💰 Баланс USDT: ${usdt_balance:.2f}\n\n"
            
            # Статистика
            report += f"📈 <b>СТАТИСТИКА:</b>\n"
            report += f"🔍 Проанализировано: {scan_results['analyzed_pairs']}/{scan_results['total_pairs']}\n"
            report += f"✅ Возможности покупки: {len(scan_results['buy_opportunities'])}\n"
            report += f"⚠️ Нейтральные: {len(scan_results['neutral_pairs'])}\n"
            report += f"🚫 Заблокированные: {len(scan_results['blocked_pairs'])}\n"
            report += f"❌ Ошибки: {len(scan_results['errors'])}\n\n"
            
            # Лучшие возможности
            if scan_results['buy_opportunities']:
                report += f"🎯 <b>ЛУЧШИЕ ВОЗМОЖНОСТИ:</b>\n"
                for i, opp in enumerate(scan_results['buy_opportunities'][:5], 1):
                    report += f"{i}. <b>{opp['symbol']}</b> ${opp['price']:.4f}\n"
                    report += f"   ⭐ Скор: {opp['score']} | RSI: {opp['rsi']:.1f}\n"
                    report += f"   🔍 {', '.join(opp['reasons'][:3])}\n\n"
            
            # Нейтральные пары (топ-3)
            if scan_results['neutral_pairs']:
                report += f"⚖️ <b>НЕЙТРАЛЬНЫЕ (топ-3):</b>\n"
                for i, pair in enumerate(scan_results['neutral_pairs'][:3], 1):
                    report += f"{i}. {pair['symbol']} (скор: {pair['score']}, RSI: {pair['rsi']:.1f})\n"
                report += "\n"
            
            # Заблокированные пары (топ-3)
            if scan_results['blocked_pairs']:
                report += f"🚫 <b>ЗАБЛОКИРОВАННЫЕ (топ-3):</b>\n"
                for i, pair in enumerate(scan_results['blocked_pairs'][:3], 1):
                    report += f"{i}. {pair['symbol']} - {pair['filter_result']['reason']}\n"
                report += "\n"
            
            # Рекомендации
            if usdt_balance >= 10.0:
                if scan_results['buy_opportunities']:
                    report += f"💡 <b>РЕКОМЕНДАЦИЯ:</b> Есть возможности для покупки!\n"
                else:
                    report += f"💡 <b>РЕКОМЕНДАЦИЯ:</b> Ждем лучших возможностей\n"
            else:
                report += f"💡 <b>РЕКОМЕНДАЦИЯ:</b> Недостаточно USDT (нужно $10+)\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка форматирования отчета: {e}")
            return f"❌ Ошибка создания отчета: {e}"
    
    async def scan_cycle(self):
        """Цикл сканирования"""
        try:
            self.scan_count += 1
            self.last_scan_time = datetime.now()
            
            logger.debug(f"🔄 Сканирование #{self.scan_count}...")
            
            # Проверяем баланс USDT в начале каждого цикла
            try:
                usdt_balance = self.get_usdt_balance()
            except Exception:
                usdt_balance = 0.0
            
            # Если баланс недостаточный - пропускаем сканирование, но НЕ останавливаем цикл
            if usdt_balance < 6.0:
                logger.info(f"⏭️ Пропуск сканирования: USDT=${usdt_balance:.2f} < $6.00 (экономия API лимитов)")
                # Пропускаем сканирование, но продолжаем цикл
                pass
            else:
                # Сканируем рынок только при достаточном балансе
                scan_results = self.scan_market()
                
                if scan_results:
                    # Форматируем отчет
                    report = self.format_scan_report(scan_results)
                    
                    # Отправляем в Telegram (каждые 10 минут вместо 5)
                    self.report_counter += 1
                    if self.report_counter % 2 == 0:  # Отправляем каждый второй отчет
                        self.send_telegram_message(report)
                        logger.info(f"📊 Отчет #{self.scan_count} отправлен в Telegram")
                    else:
                        logger.info(f"📊 Отчет #{self.scan_count} пропущен (уменьшение спама)")
                    
                    # АВТОМАТИЧЕСКАЯ ПОКУПКА
                    await self.auto_buy_opportunities(scan_results)
                else:
                    logger.error("❌ Ошибка сканирования рынка")
                
        except Exception as e:
            logger.error(f"Ошибка цикла сканирования: {e}")
    
    async def auto_buy_opportunities(self, scan_results: Dict):
        """Автоматическая покупка возможностей"""
        try:
            buy_opportunities = scan_results.get('buy_opportunities', [])
            if not buy_opportunities:
                logger.info("❌ Нет возможностей для покупки")
                return
            
            # Проверяем баланс USDT
            usdt_balance = self.get_usdt_balance()
            if usdt_balance < 6.0:
                logger.info(f"❌ Недостаточно USDT: ${usdt_balance:.2f}")
                # Отправляем уведомление о недостатке средств
                insufficient_message = (
                    f"💰 <b>НЕДОСТАТОЧНО СРЕДСТВ ДЛЯ ПОКУПКИ</b>\n\n"
                    f"📊 Найдено возможностей: {len(buy_opportunities)}\n"
                    f"💵 Текущий баланс USDT: ${usdt_balance:.2f}\n"
                    f"⚠️ Минимум для покупки: $6.00\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(insufficient_message)
                return
            
            # Берем лучшую возможность
            best_opportunity = buy_opportunities[0]
            symbol = best_opportunity['symbol']
            score = best_opportunity['score']
            
            # Рассчитываем сумму покупки в процентах от свободного USDT с фоллбэком на минимум
            purchase_amount = usdt_balance * (PURCHASE_PCT_OF_USDT / 100.0)
            if usdt_balance >= PURCHASE_MIN_USDT:
                purchase_amount = max(PURCHASE_MIN_USDT, purchase_amount)
            purchase_amount = min(purchase_amount, PURCHASE_MAX_USDT)
            
            if purchase_amount < PURCHASE_MIN_USDT:
                logger.info("❌ Сумма покупки слишком мала")
                # Отправляем уведомление о малой сумме
                small_amount_message = (
                    f"💰 <b>СУММА ПОКУПКИ СЛИШКОМ МАЛА</b>\n\n"
                    f"📊 Найдено возможностей: {len(buy_opportunities)}\n"
                    f"💵 Рассчитанная сумма: ${purchase_amount:.2f}\n"
                    f"💳 Доступный баланс: ${usdt_balance:.2f}\n"
                    f"⚠️ Минимум для покупки: ${PURCHASE_MIN_USDT:.2f}\n\n"
                    f"💡 <b>РЕШЕНИЕ:</b> Пополните баланс до $6+ для активации автопокупок\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(small_amount_message)
                return
            
            logger.info(f"🎯 Автоматическая покупка {symbol} на ${purchase_amount:.2f}")
            
            # Отправляем уведомление о начале покупки
            start_purchase_message = (
                f"🛒 <b>НАЧИНАЕМ ПОКУПКУ</b>\n\n"
                f"📈 <b>{symbol}</b>\n"
                f"💰 Сумма: ${purchase_amount:.2f} USDT\n"
                f"⭐ Скор: {score}\n"
                f"📊 RSI: {best_opportunity['rsi']:.1f}\n"
                f"🔍 Причины: {', '.join(best_opportunity['reasons'][:3])}\n\n"
                f"⏳ Выполняем покупку..."
            )
            self.send_telegram_message(start_purchase_message)
            
            # Выполняем покупку
            result = await self.execute_purchase(symbol, purchase_amount, best_opportunity)
            
            if result['success']:
                logger.info(f"✅ Автопокупка выполнена: {symbol}")
                # Успешная покупка уже отправляется в execute_purchase
            else:
                logger.error(f"❌ Ошибка автопокупки: {result['error']}")
                # Отправляем уведомление об ошибке
                error_message = (
                    f"❌ <b>ОШИБКА ПОКУПКИ</b>\n\n"
                    f"📈 <b>{symbol}</b>\n"
                    f"💰 Сумма: ${purchase_amount:.2f} USDT\n"
                    f"⭐ Скор: {score}\n"
                    f"📊 RSI: {best_opportunity['rsi']:.1f}\n\n"
                    f"🚫 <b>ОШИБКА:</b>\n"
                    f"{result['error']}\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(error_message)
                
        except Exception as e:
            logger.error(f"Ошибка автопокупки: {e}")
            # Отправляем уведомление о критической ошибке
            critical_error_message = (
                f"💥 <b>КРИТИЧЕСКАЯ ОШИБКА АВТОПОКУПКИ</b>\n\n"
                f"🚫 <b>ОШИБКА:</b>\n"
                f"{str(e)}\n\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_telegram_message(critical_error_message)
    
    async def execute_purchase(self, symbol: str, usdt_amount: float, opportunity: Dict) -> Dict:
        """Выполнить покупку с ретраями"""
        try:
            logger.info(f"🛒 Покупка {symbol} на ${usdt_amount:.2f} USDT...")
            
            # Отправляем уведомление о начале покупки с ретраями
            retry_message = (
                f"🔄 <b>ПОКУПКА С РЕТРАЯМИ</b>\n\n"
                f"📈 <b>{symbol}</b>\n"
                f"💰 Сумма: ${usdt_amount:.2f} USDT\n"
                f"⏳ Попытка 1/3..."
            )
            self.send_telegram_message(retry_message)
            
            # Получаем текущую цену
            ticker = self.mex_api.get_ticker_price(symbol)
            if not ticker or 'price' not in ticker:
                error_msg = 'Не удалось получить цену'
                self.send_telegram_message(f"❌ <b>ОШИБКА:</b> {error_msg}")
                return {'success': False, 'error': error_msg}
            
            current_price = float(ticker['price'])
            raw_quantity = usdt_amount / current_price
            
            # Список методов округления для ретраев
            rounding_methods = [
                {'name': 'Правила биржи', 'method': 'rules'},
                {'name': '3 знака', 'method': '3_digits'},
                {'name': '4 знака', 'method': '4_digits'},
                {'name': '5 знаков', 'method': '5_digits'},
                {'name': '6 знаков', 'method': '6_digits'},
                {'name': '2 знака', 'method': '2_digits'}
            ]
            
            # Пробуем каждый метод округления
            for attempt, method_info in enumerate(rounding_methods, 1):
                try:
                    method_name = method_info['name']
                    method = method_info['method']
                    
                    # Рассчитываем количество разными способами
                    if method == 'rules':
                        # Метод 1: Правила биржи
                        try:
                            from mexc_advanced_api import MexAdvancedAPI
                            advanced_api = MexAdvancedAPI()
                            symbol_rules = advanced_api.get_symbol_rules(symbol)
                            
                            if symbol_rules:
                                # Используем precision из правил
                                quantity_precision = symbol_rules.get('quantityPrecision', 8)
                                step_size = symbol_rules.get('stepSize', 1e-08)
                                min_qty = symbol_rules.get('minQty', 0)
                                
                                # Округляем до правильной точности
                                quantity = round(raw_quantity, quantity_precision)
                                
                                # Если есть минимальное количество и мы меньше его
                                if min_qty > 0 and quantity < min_qty:
                                    quantity = min_qty
                                    
                                # Округляем до шага
                                if step_size > 0:
                                    quantity = round(quantity / step_size) * step_size
                            else:
                                quantity = round(raw_quantity, 3)
                        except:
                            quantity = round(raw_quantity, 3)
                            
                    elif method == '3_digits':
                        quantity = round(raw_quantity, 3)
                    elif method == '4_digits':
                        quantity = round(raw_quantity, 4)
                    elif method == '5_digits':
                        quantity = round(raw_quantity, 5)
                    elif method == '6_digits':
                        quantity = round(raw_quantity, 6)
                    elif method == '2_digits':
                        quantity = round(raw_quantity, 2)
                    
                    if quantity <= 0:
                        continue
                    
                    # Не слать в Telegram уведомления о попытках; логируем только в файл
                    # (ранее здесь отправлялось уведомление о попытке)
                    
                    # Размещаем рыночный ордер
                    order = self.mex_api.place_order(
                        symbol=symbol,
                        side='BUY',
                        quantity=quantity,
                        price=None  # Рыночный ордер
                    )
                    
                    if 'orderId' in order:
                        # Успех!
                        explain = self._build_reasoning(opportunity)
                        success_message = (
                            f"✅ <b>ПОКУПКА УСПЕШНА!</b>\n\n"
                            f"📈 <b>{symbol}</b>\n"
                            f"💰 Сумма: ${usdt_amount:.2f} USDT\n"
                            f"📊 Метод: {method_name}\n"
                            f"📈 Количество: {quantity}\n"
                            f"💵 Цена: ${current_price:.6f}\n"
                            f"🆔 Ордер: <code>{order['orderId']}</code>\n\n"
                            f"🎯 <b>АНАЛИЗ:</b>\n"
                            f"⭐ Скор: {opportunity['score']}\n"
                            f"📊 RSI: {opportunity['rsi']:.1f}\n"
                            f"🔍 Причины:{explain['why']}\n\n"
                            f"🧭 <b>ПРОГНОЗ (2–6 ч):</b> {explain['forecast']}\n\n"
                            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                        )
                        self.send_telegram_message(success_message)
                        
                        return {
                            'success': True,
                            'order_id': order['orderId'],
                            'symbol': symbol,
                            'quantity': quantity,
                            'price': current_price,
                            'amount': usdt_amount,
                            'method': method_name,
                            'attempt': attempt
                        }
                    else:
                        # Ошибка ордера (ретрай будет сделан) — не логируем на уровне error
                        # Лог финальной ошибки будет выше по стеку
                        pass
                        
                except Exception as e:
                    # Исключение в попытке (будет ретрай) — не логируем на уровне error
                    # Лог финальной ошибки будет выше по стеку
                    pass
            
            # Все попытки исчерпаны — не отправляем в Telegram, только возвращаем ошибку
            return {'success': False, 'error': 'Все попытки покупки исчерпаны'}
                
        except Exception as e:
            error_msg = f"Критическая ошибка покупки {symbol}: {e}"
            logger.error(error_msg)
            
            # Отправляем уведомление о критической ошибке
            critical_message = (
                f"💥 <b>КРИТИЧЕСКАЯ ОШИБКА ПОКУПКИ</b>\n\n"
                f"📈 <b>{symbol}</b>\n"
                f"💰 Сумма: ${usdt_amount:.2f} USDT\n\n"
                f"🚫 <b>ОШИБКА:</b>\n"
                f"{str(e)}\n\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_telegram_message(critical_message)
            
            return {'success': False, 'error': error_msg}
    
    async def start_scanning(self):
        """Запуск фонового сканирования"""
        logger.info("🚀 Запуск фонового сканера рынка...")
        logger.info(f"⏰ Интервал сканирования: {self.scan_interval} сек")
        logger.info(f"📊 Анализируем пары: {len(self.trading_pairs)}")
        
        # Отправляем уведомление о запуске
        startup_message = (
            f"🤖 <b>ФОНОВЫЙ СКАНЕР РЫНКА ЗАПУЩЕН</b>\n\n"
            f"⏰ Интервал: {self.scan_interval} сек (5 минут)\n"
            f"📊 Пар для анализа: {len(self.trading_pairs)}\n"
            f"📱 Отчеты в Telegram каждые 5 минут\n\n"
            f"🔄 Сканирование активно..."
        )
        self.send_telegram_message(startup_message)
        
        while True:
            try:
                await self.scan_cycle()
                await asyncio.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Сканер остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Критическая ошибка: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке

async def main():
    """Главная функция"""
    scanner = MarketScanner()
    await scanner.start_scanning()

if __name__ == "__main__":
    asyncio.run(main()) 
 