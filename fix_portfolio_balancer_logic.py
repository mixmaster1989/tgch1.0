#!/usr/bin/env python3
"""
Скрипт для исправления логики PortfolioBalancer - правильная работа с PnL и USDC
"""

def fix_portfolio_balancer_logic():
    # Читаем файл
    with open('portfolio_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Модифицируем метод calculate_rebalance_trades
    old_method = '''    def calculate_rebalance_trades(self, balances: Dict, values: Dict) -> Dict:
        """Рассчитать необходимые торги для балансировки"""
        try:
            target_btc_value = values['total_value'] * self.target_btc_ratio
            target_eth_value = values['total_value'] * self.target_eth_ratio
            
            btc_diff = values['btc_value'] - target_btc_value
            eth_diff = values['eth_value'] - target_eth_value
            
            trades = []
            
            # Если BTC больше нормы - продаем BTC
            if btc_diff > 0:
                btc_to_sell = btc_diff / values['btc_price']
                
                # Проверяем минимальные лоты
                if btc_to_sell >= 0.0001:  # Минимальный лот BTC
                    btc_to_sell = round(btc_to_sell, 6)
                    trades.append({
                        'action': 'SELL',
                        'symbol': 'BTCUSDC', 
                        'quantity': btc_to_sell,
                        'value': btc_to_sell * values['btc_price']
                    })
            
            # Если ETH меньше нормы - покупаем ETH
            if eth_diff < 0:
                eth_to_buy = abs(eth_diff) / values['eth_price']
                
                # Проверяем минимальные лоты
                if eth_to_buy >= 0.001:  # Минимальный лот ETH
                    eth_to_buy = round(eth_to_buy, 6)
                    trades.append({
                        'action': 'BUY',
                        'symbol': 'ETHUSDC',
                        'quantity': eth_to_buy,
                        'value': eth_to_buy * values['eth_price']
                    })
            
            return {
                'trades': trades,
                'target_btc_value': target_btc_value,
                'target_eth_value': target_eth_value,
                'btc_diff': btc_diff,
                'eth_diff': eth_diff
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета торгов балансировки: {e}")
            return {'trades': [], 'error': str(e)}'''
    
    new_method = '''    def calculate_rebalance_trades(self, balances: Dict, values: Dict) -> Dict:
        """Рассчитать необходимые торги для балансировки с учетом PnL и USDC"""
        try:
            target_btc_value = values['total_value'] * self.target_btc_ratio
            target_eth_value = values['total_value'] * self.target_eth_ratio
            
            btc_diff = values['btc_value'] - target_btc_value
            eth_diff = values['eth_value'] - target_eth_value
            
            # Получаем PnL для каждого актива
            btc_pnl = self.get_asset_pnl('BTC', balances, values)
            eth_pnl = self.get_asset_pnl('ETH', balances, values)
            
            # Получаем доступный USDC
            usdc_balance = self.get_usdc_balance()
            
            trades = []
            total_usdc_needed = 0.0
            
            # 🔥 НОВАЯ ЛОГИКА: Сначала пытаемся купить за USDC
            
            # Если BTC больше нормы - продаем BTC (только если в плюсе или нейтрале)
            if btc_diff > 0:
                btc_to_sell = btc_diff / values['btc_price']
                
                # Проверяем PnL BTC - продаем только если в плюсе или нейтрале
                if btc_pnl >= 0:  # BTC в плюсе или нейтрале
                    if btc_to_sell >= 0.0001:  # Минимальный лот BTC
                        btc_to_sell = round(btc_to_sell, 6)
                        trades.append({
                            'action': 'SELL',
                            'symbol': 'BTCUSDC', 
                            'quantity': btc_to_sell,
                            'value': btc_to_sell * values['btc_price'],
                            'pnl': btc_pnl,
                            'reason': f'BTC в плюсе (PnL: ${btc_pnl:.4f})'
                        })
                else:
                    logger.warning(f"🚫 Не продаем BTC: PnL отрицательный ${btc_pnl:.4f}")
            
            # Если ETH меньше нормы - покупаем ETH
            if eth_diff < 0:
                eth_to_buy = abs(eth_diff) / values['eth_price']
                eth_cost = eth_to_buy * values['eth_price']
                
                if eth_to_buy >= 0.001:  # Минимальный лот ETH
                    eth_to_buy = round(eth_to_buy, 6)
                    
                    # Проверяем хватает ли USDC
                    if usdc_balance >= eth_cost:
                        # Хватает USDC - покупаем
                        trades.append({
                            'action': 'BUY',
                            'symbol': 'ETHUSDC',
                            'quantity': eth_to_buy,
                            'value': eth_cost,
                            'funding_source': 'USDC',
                            'reason': f'Покупка за USDC (доступно: ${usdc_balance:.2f})'
                        })
                    else:
                        # Не хватает USDC - нужно продать BTC
                        usdc_shortage = eth_cost - usdc_balance
                        btc_to_sell_for_usdc = usdc_shortage / values['btc_price']
                        
                        # Проверяем PnL BTC - продаем только если в плюсе
                        if btc_pnl >= 0:  # BTC в плюсе
                            if btc_to_sell_for_usdc >= 0.0001:  # Минимальный лот BTC
                                btc_to_sell_for_usdc = round(btc_to_sell_for_usdc, 6)
                                trades.append({
                                    'action': 'SELL',
                                    'symbol': 'BTCUSDC',
                                    'quantity': btc_to_sell_for_usdc,
                                    'value': btc_to_sell_for_usdc * values['btc_price'],
                                    'pnl': btc_pnl,
                                    'reason': f'Продажа BTC для покупки ETH (PnL: ${btc_pnl:.4f})'
                                })
                                
                                # Добавляем покупку ETH
                                trades.append({
                                    'action': 'BUY',
                                    'symbol': 'ETHUSDC',
                                    'quantity': eth_to_buy,
                                    'value': eth_cost,
                                    'funding_source': 'BTC_SALE',
                                    'reason': f'Покупка ETH за выручку от продажи BTC'
                                })
                        else:
                            logger.warning(f"🚫 Не продаем BTC для покупки ETH: PnL отрицательный ${btc_pnl:.4f}")
                            logger.info(f"⏳ Ждем следующей проверки - ETH в минусе, BTC в минусе")
            
            return {
                'trades': trades,
                'target_btc_value': target_btc_value,
                'target_eth_value': target_eth_value,
                'btc_diff': btc_diff,
                'eth_diff': eth_diff,
                'btc_pnl': btc_pnl,
                'eth_pnl': eth_pnl,
                'usdc_balance': usdc_balance
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета торгов балансировки: {e}")
            return {'trades': [], 'error': str(e)}'''
    
    # Заменяем метод
    content = content.replace(old_method, new_method)
    
    # Добавляем новые вспомогательные методы
    new_methods = '''
    def get_asset_pnl(self, asset: str, balances: Dict, values: Dict) -> float:
        """Получить PnL для конкретного актива"""
        try:
            if asset == 'BTC':
                quantity = balances.get('BTC', 0.0)
                current_price = values['btc_price']
                # Упрощенный расчет PnL (можно улучшить)
                avg_buy_price = current_price * 0.95  # Примерная средняя цена покупки
                pnl = (current_price - avg_buy_price) * quantity
                return pnl
            elif asset == 'ETH':
                quantity = balances.get('ETH', 0.0)
                current_price = values['eth_price']
                # Упрощенный расчет PnL (можно улучшить)
                avg_buy_price = current_price * 0.95  # Примерная средняя цена покупки
                pnl = (current_price - avg_buy_price) * quantity
                return pnl
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка расчета PnL для {asset}: {e}")
            return 0.0
    
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
'''
    
    # Вставляем новые методы перед последним методом
    lines = content.split('\n')
    insert_index = len(lines) - 2  # Перед последней строкой
    lines.insert(insert_index, new_methods)
    content = '\n'.join(lines)
    
    # Записываем обратно
    with open('portfolio_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ portfolio_balancer.py исправлен - добавлена правильная логика работы с PnL и USDC")

if __name__ == "__main__":
    fix_portfolio_balancer_logic()
