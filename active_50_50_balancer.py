#!/usr/bin/env python3
"""
Активный балансировщик 50/50 Альты vs BTC/ETH
- Сканирует каждые 10 секунд свободные USDC
- Если больше $10 - запускает балансировку
- Покупает альты за USDC если отстают
- Покупает BTC/ETH за USDC если отстают
- ЗАЩИТА: Нельзя оставлять на балансе USDC меньше $10!
- Работает БЫСТРЕЕ чем market_scanner.py
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from decimal import Decimal

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Active5050Balancer:
    """Активный балансировщик 50/50 Альты vs BTC/ETH за USDC"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Настройки мониторинга - ПЕРЕВОД НА USDC!
        self.scan_interval = 60  # Сканирование каждые 60 секунд (1 минута)
        self.min_balance_threshold = 10.0  # Минимальная сумма для балансировки ($10 USDC)
        self.max_balance_threshold = 100.0  # Максимальная сумма для одной операции ($100 USDC)
        
        # ЗАЩИТА БАЛАНСА USDC - КРИТИЧНО!
        self.min_usdc_balance_after_operation = 20.0  # Минимум $20 USDC должно остаться после операции (зарезервировано для скальперов)
        
        # Целевые пропорции
        self.target_alts_ratio = 0.50  # 50% альты
        self.target_btceth_ratio = 0.50  # 50% BTC/ETH
        
        # Минимальное отклонение для балансировки (10%)
        self.min_deviation_threshold = 0.10  # 10% отклонение от целевой пропорции
        
        # Защита от частых операций
        self.last_balance_time = None
        self.min_balance_cooldown = 60  # Минимум 1 минута между операциями
        
        # Статистика
        self.total_balances = 0
        self.total_converted = 0.0
        
        # Флаг работы
        self.is_running = False
        
        # Контроль частоты отчетов (уменьшаем спам в 2 раза)
        self.report_counter = 0
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        if not self.bot_token or not self.chat_id:
            return
            
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
    
    def get_usdc_balance(self) -> float:
        """Получить баланс USDC"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDC':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDC: {e}")
            return 0.0
    
    def get_usdt_balance(self) -> float:
        """Получить баланс USDT (для конвертации в USDC)"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDT: {e}")
            return 0.0
    
    def ensure_usdc_for_trade(self, required_usdc: float) -> bool:
        """Убедиться, что есть USDC для сделки; при недостатке купить за USDT"""
        try:
            buffer = 0.02  # небольшой запас на комиссии
            need = required_usdc + buffer
            usdc_free = self.get_usdc_balance()
            
            if usdc_free >= need:
                return True

            # Покупаем недостающее количество USDC за USDT
            shortfall = max(0.0, need - usdc_free)
            usdt_free = self.get_usdt_balance()
            
            if usdt_free < shortfall:
                logger.warning(f"⚠️ Недостаточно USDT для покупки USDC: нужно ${shortfall:.2f}, есть ${usdt_free:.2f}")
                return False

            qty = round(shortfall, 2)
            if qty < 1.0:
                qty = 1.0  # минимальный разумный шаг

            # Покупаем USDC за USDT через рыночный ордер
            order = self.mex_api.place_order(
                symbol='USDCUSDT', 
                side='BUY', 
                quantity=qty
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Куплен USDC за USDT: ${qty:.2f}")
                try:
                    self.send_telegram_message(f"💱 Куплен USDC за USDT на ${qty:.2f} для балансировки")
                except Exception:
                    pass
                return True
            else:
                logger.error(f"❌ Не удалось купить USDC: {order}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка ensure_usdc_for_trade: {e}")
            return False
    
    def can_make_operation(self, operation_amount: float) -> Tuple[bool, str]:
        """
        Проверить, можно ли сделать операцию на указанную сумму
        ЗАЩИТА: Нельзя оставлять на балансе USDC меньше $10!
        """
        try:
            current_usdc = self.get_usdc_balance()
            
            # Проверяем основную защиту баланса
            if current_usdc < self.min_usdc_balance_after_operation + operation_amount:
                return False, f"Недостаточно USDC: нужно ${operation_amount:.2f}, но должно остаться минимум ${self.min_usdc_balance_after_operation:.2f}"
            
            # Проверяем, что после операции останется достаточно USDC
            remaining_after_operation = current_usdc - operation_amount
            if remaining_after_operation < self.min_usdc_balance_after_operation:
                return False, f"После операции останется ${remaining_after_operation:.2f} USDC, что меньше минимума ${self.min_usdc_balance_after_operation:.2f}"
            
            # Проверяем кулдаун между операциями
            if (self.last_balance_time and 
                time.time() - self.last_balance_time < self.min_balance_cooldown):
                remaining_cooldown = self.min_balance_cooldown - (time.time() - self.last_balance_time)
                return False, f"Кулдаун между операциями: осталось {remaining_cooldown:.0f} сек"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки возможности операции: {e}")
            return False, f"Ошибка проверки: {e}"
    
    def calculate_safe_operation_amount(self, available_usdc: float) -> float:
        """
        Рассчитать безопасную сумму для операции
        Гарантирует, что после операции останется минимум $10 USDC
        """
        try:
            # Максимальная сумма, которую можно потратить
            max_safe_amount = available_usdc - self.min_usdc_balance_after_operation
            
            if max_safe_amount <= 0:
                return 0.0
            
            # Ограничиваем максимальной суммой операции
            safe_amount = min(max_safe_amount, self.max_balance_threshold)
            
            # Округляем до 2 знаков после запятой
            return round(safe_amount, 2)
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета безопасной суммы операции: {e}")
            return 0.0
    
    def get_portfolio_values(self) -> Dict:
        """Рассчитать стоимость портфеля альты vs BTC/ETH"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return {'alts_value': 0.0, 'btceth_value': 0.0, 'total_value': 0.0}
            
            alts_value = 0.0
            btceth_value = 0.0
            
            # Получаем цены
            btc_price = self.mex_api.get_ticker_price('BTCUSDC')
            eth_price = self.mex_api.get_ticker_price('ETHUSDC')
            usdc_usdt_price = self.mex_api.get_ticker_price('USDCUSDT')
            
            btc_price_value = float(btc_price['price']) if btc_price else 0.0
            eth_price_value = float(eth_price['price']) if eth_price else 0.0
            usdc_usdt_value = float(usdc_usdt_price['price']) if usdc_usdt_price else 1.0
            
            for balance in account_info['balances']:
                asset = balance['asset']
                total_amount = float(balance['free']) + float(balance['locked'])
                
                if total_amount <= 0:
                    continue
                
                # BTC/ETH считаем в USDC
                if asset == 'BTC':
                    btceth_value += total_amount * btc_price_value
                elif asset == 'ETH':
                    btceth_value += total_amount * eth_price_value
                # Альты (все остальное кроме стейблкоинов) считаем в USDT
                elif asset not in ['USDT', 'USDC']:
                    # Получаем цену в USDT
                    symbol = f"{asset}USDT"
                    try:
                        price_info = self.mex_api.get_ticker_price(symbol)
                        if price_info and 'price' in price_info:
                            price = float(price_info['price'])
                            alts_value += total_amount * price
                    except:
                        # Если не можем получить цену, пропускаем
                        continue
            
            # Конвертируем BTC/ETH в USDT для сравнения
            btceth_value_usdt = btceth_value * usdc_usdt_value
            total_value = alts_value + btceth_value_usdt
            
            return {
                'alts_value': alts_value,
                'btceth_value': btceth_value,
                'btceth_value_usdt': btceth_value_usdt,
                'total_value': total_value,
                'usdc_usdt_rate': usdc_usdt_value
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета стоимости портфеля: {e}")
            return {'alts_value': 0.0, 'btceth_value': 0.0, 'total_value': 0.0}
    
    def calculate_balance_needed(self) -> Optional[Dict]:
        """Рассчитать необходимую балансировку за USDC"""
        try:
            usdc_balance = self.get_usdc_balance()
            
            if usdc_balance < self.min_balance_threshold:
                return None
            
            # Получаем актуальные данные портфеля
            portfolio = self.get_portfolio_values()
            
            if portfolio['total_value'] <= 0:
                return None
            
            # Рассчитываем текущие пропорции
            alts_ratio = portfolio['alts_value'] / portfolio['total_value']
            btceth_ratio = portfolio['btceth_value_usdt'] / portfolio['total_value']
            
            # Целевые значения
            target_alts_value = portfolio['total_value'] * self.target_alts_ratio
            target_btceth_value = portfolio['total_value'] * self.target_btceth_ratio
            
            # Отклонения
            alts_deviation = portfolio['alts_value'] - target_alts_value
            btceth_deviation = portfolio['btceth_value_usdt'] - target_btceth_value
            
            # Рассчитываем безопасную сумму для операции
            safe_operation_amount = self.calculate_safe_operation_amount(usdc_balance)
            
            if safe_operation_amount < 5.0:  # Минимум $5 для операции
                return None
            
            # Проверяем минимальное отклонение (10%)
            alts_deviation_percent = abs(alts_ratio - self.target_alts_ratio) / self.target_alts_ratio
            btceth_deviation_percent = abs(btceth_ratio - self.target_btceth_ratio) / self.target_btceth_ratio
            
            # Балансируем только если отклонение больше 10%
            if alts_deviation_percent < self.min_deviation_threshold and btceth_deviation_percent < self.min_deviation_threshold:
                logger.info(f"📊 Отклонение недостаточно для балансировки: Альты {alts_deviation_percent*100:.1f}%, BTC/ETH {btceth_deviation_percent*100:.1f}% < {self.min_deviation_threshold*100}%")
                return None
            
            # Определяем что нужно делать
            if alts_deviation > 0 and btceth_deviation < 0:
                # Альтов больше, BTC/ETH меньше - покупаем BTC/ETH за USDC
                amount_to_spend = min(safe_operation_amount, abs(btceth_deviation) * 0.5)
                if amount_to_spend >= 5.0:  # Минимум $5
                    return {
                        'action': 'BUY_BTCETH_USDC',
                        'amount': amount_to_spend,
                        'reason': f'Альты {alts_ratio*100:.1f}% > 50%, BTC/ETH {btceth_ratio*100:.1f}% < 50% (отклонение {alts_deviation_percent*100:.1f}%)'
                    }
            
            elif btceth_deviation > 0 and alts_deviation < 0:
                # BTC/ETH больше, альтов меньше - покупаем альты за USDC
                amount_to_spend = min(safe_operation_amount, abs(alts_deviation) * 0.5)
                if amount_to_spend >= 5.0:  # Минимум $5
                    return {
                        'action': 'BUY_ALTS_USDC',
                        'amount': amount_to_spend,
                        'reason': f'BTC/ETH {btceth_ratio*100:.1f}% > 50%, Альты {alts_ratio*100:.1f}% < 50% (отклонение {btceth_deviation_percent*100:.1f}%)'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета балансировки: {e}")
            return None
    
    def check_purchase_permission(self, purchase_amount: float, purchase_type: str = "ALTS") -> Dict:
        """Проверить разрешение на покупку альтов у балансировщика"""
        try:
            # Получаем текущие пропорции портфеля
            portfolio = self.get_portfolio_values()
            
            if portfolio['total_value'] <= 0:
                return {
                    'allowed': False,
                    'reason': 'Портфель пуст или недоступен',
                    'current_alts_ratio': 0.0,
                    'current_btceth_ratio': 0.0
                }
            
            # Рассчитываем текущие пропорции
            alts_ratio = portfolio['alts_value'] / portfolio['total_value']
            btceth_ratio = portfolio['btceth_value_usdt'] / portfolio['total_value']
            
            # Проверяем отклонение от целевых пропорций
            alts_deviation_percent = abs(alts_ratio - self.target_alts_ratio) / self.target_alts_ratio
            btceth_deviation_percent = abs(btceth_ratio - self.target_btceth_ratio) / self.target_btceth_ratio
            
            # Если отклонение меньше 10% - разрешаем покупку
            if alts_deviation_percent < self.min_deviation_threshold and btceth_deviation_percent < self.min_deviation_threshold:
                return {
                    'allowed': True,
                    'reason': f'Пропорции сбалансированы (Альты: {alts_ratio*100:.1f}%, BTC/ETH: {btceth_ratio*100:.1f}%)',
                    'current_alts_ratio': alts_ratio,
                    'current_btceth_ratio': btceth_ratio
                }
            
            # Если альтов больше 50% - блокируем покупку альтов
            if alts_ratio > self.target_alts_ratio and purchase_type == "ALTS":
                return {
                    'allowed': False,
                    'reason': f'Альтов уже {alts_ratio*100:.1f}% > 50% (отклонение {alts_deviation_percent*100:.1f}%)',
                    'current_alts_ratio': alts_ratio,
                    'current_btceth_ratio': btceth_ratio
                }
            
            # Если BTC/ETH больше 50% - разрешаем покупку альтов
            if btceth_ratio > self.target_btceth_ratio and purchase_type == "ALTS":
                return {
                    'allowed': True,
                    'reason': f'BTC/ETH {btceth_ratio*100:.1f}% > 50%, можно покупать альты',
                    'current_alts_ratio': alts_ratio,
                    'current_btceth_ratio': btceth_ratio
                }
            
            # По умолчанию разрешаем
            return {
                'allowed': True,
                'reason': f'Пропорции в норме (Альты: {alts_ratio*100:.1f}%, BTC/ETH: {btceth_ratio*100:.1f}%)',
                'current_alts_ratio': alts_ratio,
                'current_btceth_ratio': btceth_ratio
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки разрешения: {e}")
            return {
                'allowed': False,
                'reason': f'Ошибка проверки: {e}',
                'current_alts_ratio': 0.0,
                'current_btceth_ratio': 0.0
            }
    
    async def execute_balance_operation(self, balance_plan: Dict) -> bool:
        """Выполнить операцию балансировки за USDC"""
        try:
            action = balance_plan['action']
            amount = balance_plan['amount']
            reason = balance_plan['reason']
            
            logger.info(f"⚖️ Выполняем балансировку: {action} на ${amount:.2f} USDC")
            logger.info(f"📊 Причина: {reason}")
            
            # Проверяем возможность операции с ЗАЩИТОЙ БАЛАНСА
            can_operate, reason_block = self.can_make_operation(amount)
            
            if not can_operate:
                logger.warning(f"⚠️ Операция заблокирована: {reason_block}")
                return False
            
            if action == 'BUY_BTCETH_USDC':
                # Покупаем BTC/ETH за USDC
                success = await self.buy_btceth_with_usdc(amount)
            elif action == 'BUY_ALTS_USDC':
                # Покупаем альты за USDC
                success = await self.buy_alts_with_usdc(amount)
            else:
                logger.error(f"❌ Неизвестное действие: {action}")
                return False
            
            if success:
                self.last_balance_time = time.time()
                self.total_balances += 1
                self.total_converted += amount
                
                logger.info(f"✅ Балансировка выполнена успешно!")
                logger.info(f"📊 Статистика: {self.total_balances} операций, потрачено ${self.total_converted:.2f} USDC")
                
                # Отправляем уведомление
                message = self.format_balance_report(balance_plan, True)
                self.send_telegram_message(message)
                
                return True
            else:
                logger.error(f"❌ Ошибка выполнения балансировки")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения балансировки: {e}")
            return False
    
    async def buy_btceth_with_usdc(self, amount: float) -> bool:
        """Купить BTC/ETH за USDC"""
        try:
            # Распределяем между BTC и ETH
            btc_amount = amount * 0.6  # 60% на BTC
            eth_amount = amount * 0.4  # 40% на ETH
            
            success_count = 0
            
            # Покупаем BTC
            if btc_amount >= 5.0:
                btc_order = self.mex_api.place_order(
                    symbol='BTCUSDC',
                    side='BUY',
                    quantity=btc_amount
                )
                if btc_order and 'orderId' in btc_order:
                    logger.info(f"✅ Куплен BTC на ${btc_amount:.2f} USDC")
                    success_count += 1
                else:
                    logger.error(f"❌ Ошибка покупки BTC")
            
            # Покупаем ETH
            if eth_amount >= 5.0:
                eth_order = self.mex_api.place_order(
                    symbol='ETHUSDC',
                    side='BUY',
                    quantity=eth_amount
                )
                if eth_order and 'orderId' in eth_order:
                    logger.info(f"✅ Куплен ETH на ${eth_amount:.2f} USDC")
                    success_count += 1
                else:
                    logger.error(f"❌ Ошибка покупки ETH")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка покупки BTC/ETH: {e}")
            return False
    
    async def buy_alts_with_usdc(self, amount: float) -> bool:
        """Купить альты за USDC"""
        try:
            # Список популярных альтов для покупки
            alt_symbols = ['ADAUSDC', 'DOTUSDC', 'LINKUSDC', 'MATICUSDC', 'AVAXUSDC']
            
            # Распределяем сумму между альтами
            amount_per_alt = amount / len(alt_symbols)
            
            if amount_per_alt < 5.0:
                # Если сумма на каждый альт слишком мала, покупаем только первый
                alt_symbols = alt_symbols[:1]
                amount_per_alt = amount
            
            success_count = 0
            
            for symbol in alt_symbols:
                try:
                    order = self.mex_api.place_order(
                        symbol=symbol,
                        side='BUY',
                        quantity=amount_per_alt
                    )
                    
                    if order and 'orderId' in order:
                        logger.info(f"✅ Куплен {symbol} на ${amount_per_alt:.2f} USDC")
                        success_count += 1
                    else:
                        logger.error(f"❌ Ошибка покупки {symbol}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка покупки {symbol}: {e}")
                    continue
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка покупки альтов: {e}")
            return False
    
    def format_balance_report(self, balance_plan: Dict, success: bool) -> str:
        """Форматировать отчет о балансировке"""
        try:
            action = balance_plan['action']
            amount = balance_plan['amount']
            reason = balance_plan['reason']
            
            if success:
                message = "<b>✅ БАЛАНСИРОВКА ВЫПОЛНЕНА</b>\n"
            else:
                message = "<b>❌ ОШИБКА БАЛАНСИРОВКИ</b>\n"
            
            message += "=" * 40 + "\n\n"
            message += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            message += f"⚖️ Действие: {action}\n"
            message += f"💰 Сумма: ${amount:.2f} USDC\n"
            message += f"📊 Причина: {reason}\n\n"
            
            if success:
                message += f"📈 Статистика: {self.total_balances} операций\n"
                message += f"💸 Всего потрачено: ${self.total_converted:.2f} USDC\n"
                message += f"🛡️ Защита баланса: минимум $10 USDC\n"
            else:
                message += "⚠️ Операция не выполнена\n"
            
            message += "\n" + "=" * 40 + "\n"
            message += "<b>⚖️ АКТИВНАЯ БАЛАНСИРОВКА</b>"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования отчета: {e}")
            return f"❌ Ошибка отчета: {e}"
    
    async def balance_cycle(self):
        """Один цикл балансировки"""
        try:
            # Проверяем кулдаун
            if (self.last_balance_time and 
                time.time() - self.last_balance_time < self.min_balance_cooldown):
                return
            
            # Получаем баланс USDC (основная валюта для операций)
            usdc_balance = self.get_usdc_balance()
            
            if usdc_balance < self.min_balance_threshold:
                return
            
            # Получаем стоимость портфеля
            portfolio = self.get_portfolio_values()
            
            if portfolio['total_value'] <= 0:
                return
            
            # Рассчитываем необходимую балансировку
            balance_plan = self.calculate_balance_needed()
            
            if not balance_plan:
                return
            
            logger.info(f"🎯 Запуск активной балансировки: {balance_plan['action']} ${balance_plan['amount']:.2f}")
            
            # Выполняем конвертацию
            success = await self.execute_balance_operation(balance_plan)
            
            if success:
                # Отправляем отчет (каждые 20 секунд вместо 10)
                self.report_counter += 1
                if self.report_counter % 2 == 0:  # Отправляем каждый второй отчет
                    report = self.format_balance_report(balance_plan, True)
                    self.send_telegram_message(report)
                else:
                    logger.info("📊 Отчет балансировки пропущен (уменьшение спама)")
            else:
                # Отправляем отчет об ошибке (всегда)
                report = self.format_balance_report(balance_plan, False)
                self.send_telegram_message(report)
            
        except Exception as e:
            logger.error(f"❌ Ошибка цикла балансировки: {e}")
    
    async def start_monitoring(self):
        """Запустить мониторинг балансировки"""
        logger.info("🚀 Запуск активного балансировщика 50/50 Альты vs BTC/ETH за USDC")
        logger.info(f"📊 Настройки:")
        logger.info(f"   Минимальный баланс: ${self.min_balance_threshold} USDC")
        logger.info(f"   Максимальная операция: ${self.max_balance_threshold} USDC")
        logger.info(f"   ЗАЩИТА: Минимум ${self.min_usdc_balance_after_operation} USDC должно остаться после операции")
        logger.info(f"   Интервал сканирования: {self.scan_interval} сек (1 минута)")
        logger.info(f"   Кулдаун между операциями: {self.min_balance_cooldown} сек")
        logger.info(f"   Целевые пропорции: Альты {self.target_alts_ratio*100}% | BTC/ETH {self.target_btceth_ratio*100}%")
        logger.info(f"   Минимальное отклонение для балансировки: {self.min_deviation_threshold*100}%")
        
        # Отправляем уведомление о запуске
        startup_message = (
            "<b>⚖️ АКТИВНЫЙ БАЛАНСИРОВЩИК 50/50 ЗАПУЩЕН</b>\n\n"
            f"📊 Настройки:\n"
            f"💰 Минимальный баланс: ${self.min_balance_threshold} USDC\n"
            f"💸 Максимальная операция: ${self.max_balance_threshold} USDC\n"
            f"🛡️ ЗАЩИТА: Минимум ${self.min_usdc_balance_after_operation} USDC после операции\n"
            f"⏰ Сканирование каждые {self.scan_interval} сек (1 минута)\n"
            f"📈 Целевые пропорции: Альты {self.target_alts_ratio*100}% | BTC/ETH {self.target_btceth_ratio*100}%\n"
            f"🎯 Минимальное отклонение: {self.min_deviation_threshold*100}%\n\n"
            "🔄 Мониторинг активен...\n"
            "💱 Все операции выполняются за USDC (рыночные ордера без комиссий)"
        )
        self.send_telegram_message(startup_message)
        
        self.is_running = True
        
        while self.is_running:
            try:
                await self.balance_cycle()
                await asyncio.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Мониторинг остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле балансировки: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке
        
        self.is_running = False
        logger.info("🛑 Мониторинг балансировки остановлен")
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        logger.info("🛑 Остановка активного балансировщика 50/50")
        self.is_running = False
    
    def get_status(self) -> Dict:
        """Получить статус балансировщика"""
        return {
            'is_running': self.is_running,
            'total_balances': self.total_balances,
            'total_converted': self.total_converted,
            'last_balance_time': self.last_balance_time,
            'scan_interval': self.scan_interval,
            'min_balance_threshold': self.min_balance_threshold
        }

# Функция для запуска в отдельном потоке
def run_active_balancer():
    """Запустить активный балансировщик в отдельном потоке"""
    balancer = Active5050Balancer()
    asyncio.run(balancer.start_monitoring())

if __name__ == "__main__":
    # Тестовый запуск
    balancer = Active5050Balancer()
    asyncio.run(balancer.start_monitoring())
