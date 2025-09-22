#!/usr/bin/env python3
"""
Скрипт для полного исправления PortfolioBalancer - замена всего метода calculate_rebalance_trades
"""

def fix_portfolio_balancer_complete():
    # Читаем файл
    with open('portfolio_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим и заменяем весь метод calculate_rebalance_trades
    start_marker = "    def calculate_rebalance_trades(self, balances: Dict, values: Dict) -> Dict:"
    end_marker = "    async def execute_portfolio_rebalance(self) -> Dict:"
    
    # Разбиваем на строки
    lines = content.split('\n')
    
    # Находим начало и конец метода
    start_index = -1
    end_index = -1
    
    for i, line in enumerate(lines):
        if start_marker in line:
            start_index = i
        elif end_marker in line and start_index != -1:
            end_index = i
            break
    
    if start_index == -1 or end_index == -1:
        print("❌ Не удалось найти метод calculate_rebalance_trades")
        return
    
    # Новый метод
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
    new_lines = lines[:start_index] + new_method.split('\n') + lines[end_index:]
    
    # Записываем обратно
    with open('portfolio_balancer.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ portfolio_balancer.py исправлен - полностью заменен метод calculate_rebalance_trades")

if __name__ == "__main__":
    fix_portfolio_balancer_complete()
