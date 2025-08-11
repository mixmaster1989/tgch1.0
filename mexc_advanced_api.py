#!/usr/bin/env python3
"""
Расширенный MEX API для получения критичных данных
- Правила торговли (минимальные лоты, точность)
- История сделок пользователя
- Комиссии за торговлю
"""

import hashlib
import hmac
import time
import requests
import json
from typing import Dict, List, Optional
from config import MEX_API_KEY, MEX_SECRET_KEY, MEX_SPOT_URL

class MexAdvancedAPI:
    """Расширенный API для получения критичных торговых данных"""
    
    def __init__(self):
        self.api_key = MEX_API_KEY
        self.secret_key = MEX_SECRET_KEY
        self.base_url = MEX_SPOT_URL
        
    def _generate_signature(self, query_string: str) -> str:
        """Генерация подписи для приватных эндпоинтов"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, signed: bool = False) -> Dict:
        """Получение заголовков для запросов"""
        headers = {
            'Content-Type': 'application/json',
        }
        if signed:
            headers['X-MEXC-APIKEY'] = self.api_key
        return headers
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict:
        """
        Получить информацию о торговых парах
        Критично для: минимальные лоты, точность цен, правила торговли
        """
        try:
            url = f"{self.base_url}/api/v3/exchangeInfo"
            params = {}
            if symbol:
                params['symbol'] = symbol
                
            response = requests.get(url, params=params, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Ошибка получения exchange info: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Ошибка API exchange info: {e}")
            return {}
    
    def get_symbol_rules(self, symbol: str) -> Dict:
        """
        Получить правила торговли для конкретной пары
        Возвращает: минимальный лот, точность цены, статус торговли
        """
        try:
            exchange_info = self.get_exchange_info(symbol)
            
            symbols = exchange_info.get('symbols') or exchange_info.get('data') or []
            if not symbols:
                return {}
            
            symbol_info = None
            for s in symbols:
                if s.get('symbol') == symbol:
                    symbol_info = s
                    break
            if not symbol_info:
                return {}
            
            # Безопасно извлекаем фильтры по именам
            filters = symbol_info.get('filters', []) or []
            by_type = {}
            for f in filters:
                ft = f.get('filterType') or f.get('filter_type') or f.get('type')
                if ft:
                    by_type[ft] = f
            
            lot = by_type.get('LOT_SIZE', {})
            pricef = by_type.get('PRICE_FILTER', {})
            min_notional_f = by_type.get('MIN_NOTIONAL') or by_type.get('NOTIONAL') or {}
            
            def as_float(d: Dict, key: str, default: float = 0.0) -> float:
                try:
                    return float(d.get(key, default))
                except Exception:
                    return default
            
            min_qty = as_float(lot, 'minQty', as_float(lot, 'min_qty', 0.0))
            step_size = as_float(lot, 'stepSize', as_float(lot, 'step_size', 0.0))
            min_price = as_float(pricef, 'minPrice', as_float(pricef, 'min_price', 0.0))
            tick_size = as_float(pricef, 'tickSize', as_float(pricef, 'tick_size', 0.0))
            min_notional = as_float(min_notional_f, 'minNotional', as_float(min_notional_f, 'min_notional', 5.0))
            
            # Точности, если есть
            price_precision = symbol_info.get('pricePrecision') or symbol_info.get('price_precision') or 8
            quantity_precision = symbol_info.get('quantityPrecision') or symbol_info.get('quantity_precision') or 8
            
            return {
                'symbol': symbol,
                'status': symbol_info.get('status', 'UNKNOWN'),
                'baseAsset': symbol_info.get('baseAsset', ''),
                'quoteAsset': symbol_info.get('quoteAsset', ''),
                'minQty': min_qty,
                'maxQty': as_float(lot, 'maxQty', as_float(lot, 'max_qty', 0.0)),
                'stepSize': step_size or (10 ** -int(quantity_precision)),
                'minPrice': min_price,
                'maxPrice': as_float(pricef, 'maxPrice', as_float(pricef, 'max_price', 0.0)),
                'tickSize': tick_size or (10 ** -int(price_precision)),
                'minNotional': min_notional if min_notional > 0 else 5.0,
                'pricePrecision': int(price_precision),
                'quantityPrecision': int(quantity_precision)
            }
            
        except Exception as e:
            print(f"Ошибка получения правил для {symbol}: {e}")
            return {}
    
    def get_my_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Получить историю сделок пользователя
        Критично для: анализ торговли, расчет P&L, оптимизация стратегий
        """
        try:
            timestamp = int(time.time() * 1000)
            query_string = f'symbol={symbol}&timestamp={timestamp}'
            
            if limit:
                query_string += f'&limit={limit}'
            
            signature = self._generate_signature(query_string)
            url = f"{self.base_url}/api/v3/myTrades?{query_string}&signature={signature}"
            
            response = requests.get(url, headers=self._get_headers(True))
            
            if response.status_code == 200:
                trades = response.json()
                # Обрабатываем данные
                processed_trades = []
                for trade in trades:
                    processed_trades.append({
                        'id': trade.get('id'),
                        'symbol': trade.get('symbol'),
                        'orderId': trade.get('orderId'),
                        'price': float(trade.get('price', 0)),
                        'qty': float(trade.get('qty', 0)),
                        'quoteQty': float(trade.get('quoteQty', 0)),
                        'commission': float(trade.get('commission', 0)),
                        'commissionAsset': trade.get('commissionAsset'),
                        'time': trade.get('time'),
                        'isBuyer': trade.get('isBuyer', False),
                        'isMaker': trade.get('isMaker', False),
                        'isBestMatch': trade.get('isBestMatch', False)
                    })
                return processed_trades
            else:
                print(f"Ошибка получения истории сделок: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Ошибка API my trades: {e}")
            return []
    
    def get_trade_fee(self, symbol: Optional[str] = None) -> Dict:
        """
        Получить комиссии за торговлю
        Критично для: точный расчет прибыли, оптимизация размера ордеров
        """
        try:
            timestamp = int(time.time() * 1000)
            query_string = f'timestamp={timestamp}'
            
            if symbol:
                query_string += f'&symbol={symbol}'
            
            signature = self._generate_signature(query_string)
            url = f"{self.base_url}/api/v3/account/tradeFee?{query_string}&signature={signature}"
            
            response = requests.get(url, headers=self._get_headers(True))
            
            if response.status_code == 200:
                fee_data = response.json()
                return fee_data
            else:
                print(f"Ошибка получения комиссий: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Ошибка API trade fee: {e}")
            return {}
    
    def get_symbol_fee(self, symbol: str) -> Dict:
        """
        Получить комиссии для конкретной пары
        """
        try:
            fee_data = self.get_trade_fee(symbol)
            
            if 'tradeFee' in fee_data:
                for fee in fee_data['tradeFee']:
                    if fee.get('symbol') == symbol:
                        return {
                            'symbol': symbol,
                            'makerCommissionRate': float(fee.get('makerCommissionRate', 0)),
                            'takerCommissionRate': float(fee.get('takerCommissionRate', 0))
                        }
            
            # Возвращаем дефолтные комиссии если не найдены
            return {
                'symbol': symbol,
                'makerCommissionRate': 0.001,  # 0.1%
                'takerCommissionRate': 0.001   # 0.1%
            }
            
        except Exception as e:
            print(f"Ошибка получения комиссий для {symbol}: {e}")
            return {
                'symbol': symbol,
                'makerCommissionRate': 0.001,
                'takerCommissionRate': 0.001
            }
    
    def calculate_min_order_size(self, symbol: str, current_price: float) -> Dict:
        """
        Рассчитать минимальный размер ордера для пары
        """
        try:
            rules = self.get_symbol_rules(symbol)
            fees = self.get_symbol_fee(symbol)
            
            if not rules:
                return {
                    'min_qty': 0.001,
                    'min_notional': 5.0,
                    'min_order_usdt': 5.0
                }
            
            min_qty = rules.get('minQty', 0.001)
            min_notional = rules.get('minNotional', 5.0)
            
            # Минимальный размер в USDT
            min_order_usdt = max(min_notional, min_qty * current_price)
            
            return {
                'min_qty': min_qty,
                'min_notional': min_notional,
                'min_order_usdt': min_order_usdt,
                'price_precision': rules.get('pricePrecision', 8),
                'quantity_precision': rules.get('quantityPrecision', 8),
                'maker_fee': fees.get('makerCommissionRate', 0.001),
                'taker_fee': fees.get('takerCommissionRate', 0.001)
            }
            
        except Exception as e:
            print(f"Ошибка расчета минимального размера для {symbol}: {e}")
            return {
                'min_qty': 0.001,
                'min_notional': 5.0,
                'min_order_usdt': 5.0
            }
    
    def get_trading_summary(self, symbol: str) -> Dict:
        """
        Получить сводку по торговле для пары
        """
        try:
            trades = self.get_my_trades(symbol, limit=100)
            rules = self.get_symbol_rules(symbol)
            fees = self.get_symbol_fee(symbol)
            
            # Анализируем сделки
            total_buy_volume = 0
            total_sell_volume = 0
            total_buy_cost = 0
            total_sell_revenue = 0
            total_commission = 0
            
            for trade in trades:
                if trade['isBuyer']:
                    total_buy_volume += trade['qty']
                    total_buy_cost += trade['quoteQty']
                else:
                    total_sell_volume += trade['qty']
                    total_sell_revenue += trade['quoteQty']
                
                total_commission += trade['commission']
            
            # Рассчитываем P&L
            current_position = total_buy_volume - total_sell_volume
            realized_pnl = total_sell_revenue - (total_sell_volume * (total_buy_cost / total_buy_volume if total_buy_volume > 0 else 0))
            
            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'total_buy_volume': total_buy_volume,
                'total_sell_volume': total_sell_volume,
                'current_position': current_position,
                'total_commission': total_commission,
                'realized_pnl': realized_pnl,
                'avg_buy_price': total_buy_cost / total_buy_volume if total_buy_volume > 0 else 0,
                'avg_sell_price': total_sell_revenue / total_sell_volume if total_sell_volume > 0 else 0,
                'trading_rules': rules,
                'fees': fees
            }
            
        except Exception as e:
            print(f"Ошибка получения сводки для {symbol}: {e}")
            return {}
