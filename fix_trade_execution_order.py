#!/usr/bin/env python3
"""
Скрипт для исправления порядка выполнения торгов - сначала все SELL, потом все BUY
"""

def fix_trade_execution_order():
    # Читаем файл
    with open('portfolio_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Модифицируем логику выполнения торгов
    old_execution = '''            # Выполняем торги
            results = {
                'success': True,
                'timestamp': datetime.now(),
                'before': {
                    'btc_ratio': values['btc_ratio'],
                    'eth_ratio': values['eth_ratio'],
                    'total_value': values['total_value']
                },
                'trades': [],
                'plan': rebalance_plan
            }
            
            for trade in rebalance_plan['trades']:
                trade_result = self.execute_rebalance_trade(
                    trade['action'],
                    trade['symbol'],
                    trade['quantity']
                )
                
                trade['result'] = trade_result
                results['trades'].append(trade)
                
                if not trade_result['success']:
                    logger.error(f"Ошибка выполнения торга: {trade_result['error']}")'''
    
    new_execution = '''            # 🔥 НОВАЯ ЛОГИКА: Выполняем торги в правильном порядке
            results = {
                'success': True,
                'timestamp': datetime.now(),
                'before': {
                    'btc_ratio': values['btc_ratio'],
                    'eth_ratio': values['eth_ratio'],
                    'total_value': values['total_value']
                },
                'trades': [],
                'plan': rebalance_plan
            }
            
            # Разделяем торги на SELL и BUY
            sell_trades = [t for t in rebalance_plan['trades'] if t['action'] == 'SELL']
            buy_trades = [t for t in rebalance_plan['trades'] if t['action'] == 'BUY']
            
            logger.info(f"📊 План торгов: {len(sell_trades)} продаж, {len(buy_trades)} покупок")
            
            # 🔥 ШАГ 1: Выполняем все SELL операции
            for trade in sell_trades:
                logger.info(f"🔄 Выполняем продажу: {trade['symbol']} {trade['quantity']:.6f}")
                trade_result = self.execute_rebalance_trade(
                    trade['action'],
                    trade['symbol'],
                    trade['quantity']
                )
                
                trade['result'] = trade_result
                results['trades'].append(trade)
                
                if not trade_result['success']:
                    logger.error(f"❌ Ошибка продажи: {trade_result['error']}")
                    # Продолжаем выполнение других торгов
                else:
                    logger.info(f"✅ Продажа выполнена: {trade['symbol']}")
            
            # 🔥 ШАГ 2: Ждем поступления USDC (если были продажи)
            if sell_trades:
                logger.info("⏳ Ожидаем поступления USDC от продаж...")
                import time
                time.sleep(3)  # Ждем 3 секунды для поступления USDC
                
                # Проверяем новый баланс USDC
                new_usdc_balance = self.get_usdc_balance()
                logger.info(f"💰 Новый баланс USDC: ${new_usdc_balance:.2f}")
            
            # 🔥 ШАГ 3: Выполняем все BUY операции
            for trade in buy_trades:
                logger.info(f"🔄 Выполняем покупку: {trade['symbol']} {trade['quantity']:.6f}")
                
                # Проверяем баланс USDC перед покупкой
                usdc_balance = self.get_usdc_balance()
                required_usdc = trade['quantity'] * trade.get('price', 0)
                
                if usdc_balance < required_usdc:
                    logger.warning(f"⚠️ Недостаточно USDC для покупки {trade['symbol']}: нужно ${required_usdc:.2f}, есть ${usdc_balance:.2f}")
                    trade_result = {'success': False, 'error': f'Недостаточно USDC: нужно ${required_usdc:.2f}, есть ${usdc_balance:.2f}'}
                else:
                    trade_result = self.execute_rebalance_trade(
                        trade['action'],
                        trade['symbol'],
                        trade['quantity']
                    )
                
                trade['result'] = trade_result
                results['trades'].append(trade)
                
                if not trade_result['success']:
                    logger.error(f"❌ Ошибка покупки: {trade_result['error']}")
                else:
                    logger.info(f"✅ Покупка выполнена: {trade['symbol']}")'''
    
    # Заменяем логику выполнения
    content = content.replace(old_execution, new_execution)
    
    # Записываем обратно
    with open('portfolio_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ portfolio_balancer.py исправлен - добавлен правильный порядок выполнения торгов")

if __name__ == "__main__":
    fix_trade_execution_order()
