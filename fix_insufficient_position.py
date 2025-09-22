#!/usr/bin/env python3
"""
Скрипт для исправления ошибки "Insufficient position" - добавление ожидания исполнения ордеров
"""

def fix_insufficient_position():
    # Читаем файл
    with open('portfolio_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Модифицируем метод execute_rebalance_trade
    old_method = '''    def execute_rebalance_trade(self, action: str, symbol: str, quantity: float) -> Dict:
        """Выполнить торговую операцию для балансировки"""
        try:
            logger.info(f"🔄 Балансировка: {action} {quantity:.6f} {symbol}")
            
            # Получаем оптимальную цену
            side = 'SELL' if action == 'SELL' else 'BUY'
            limit_price = self.calculate_limit_price(symbol, side)
            
            if not limit_price:
                return {'success': False, 'error': f'Не удалось рассчитать цену для {symbol}'}
            
            # Получаем данные стакана для логирования
            orderbook = self.get_orderbook_data(symbol)
            
            logger.info(f"📊 Стакан {symbol}:")
            logger.info(f"   Лучшая покупка: ${orderbook['best_bid']:.4f}")
            logger.info(f"   Лучшая продажа: ${orderbook['best_ask']:.4f}")
            logger.info(f"   Спред: {orderbook['spread_percent']:.4f}%")
            logger.info(f"   Наша цена: ${limit_price:.4f}")
            
            # Создаем лимитный ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=limit_price
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Ордер балансировки размещен: {order}")
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': limit_price,
                    'order': order
                }
            else:
                logger.error(f"❌ Ошибка размещения ордера балансировки: {order}")
                return {'success': False, 'error': f'API ошибка: {order}'}
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения балансировки {symbol}: {e}")
            return {'success': False, 'error': str(e)}'''
    
    new_method = '''    def execute_rebalance_trade(self, action: str, symbol: str, quantity: float) -> Dict:
        """Выполнить торговую операцию для балансировки"""
        try:
            logger.info(f"🔄 Балансировка: {action} {quantity:.6f} {symbol}")
            
            # Получаем оптимальную цену
            side = 'SELL' if action == 'SELL' else 'BUY'
            limit_price = self.calculate_limit_price(symbol, side)
            
            if not limit_price:
                return {'success': False, 'error': f'Не удалось рассчитать цену для {symbol}'}
            
            # Получаем данные стакана для логирования
            orderbook = self.get_orderbook_data(symbol)
            
            logger.info(f"📊 Стакан {symbol}:")
            logger.info(f"   Лучшая покупка: ${orderbook['best_bid']:.4f}")
            logger.info(f"   Лучшая продажа: ${orderbook['best_ask']:.4f}")
            logger.info(f"   Спред: {orderbook['spread_percent']:.4f}%")
            logger.info(f"   Наша цена: ${limit_price:.4f}")
            
            # 🔥 НОВОЕ: Проверяем баланс перед покупкой
            if action == 'BUY':
                usdc_balance = self.get_usdc_balance()
                required_usdc = quantity * limit_price
                
                logger.info(f"💰 Проверка баланса перед покупкой:")
                logger.info(f"   Доступно USDC: ${usdc_balance:.2f}")
                logger.info(f"   Требуется USDC: ${required_usdc:.2f}")
                
                if usdc_balance < required_usdc:
                    logger.warning(f"⚠️ Недостаточно USDC для покупки: нужно ${required_usdc:.2f}, есть ${usdc_balance:.2f}")
                    return {'success': False, 'error': f'Недостаточно USDC: нужно ${required_usdc:.2f}, есть ${usdc_balance:.2f}'}
            
            # Создаем лимитный ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=limit_price
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Ордер балансировки размещен: {order}")
                
                # 🔥 НОВОЕ: Ждем исполнения ордера (только для SELL)
                if action == 'SELL':
                    logger.info(f"⏳ Ожидаем исполнения ордера {order['orderId']}...")
                    import time
                    time.sleep(2)  # Ждем 2 секунды для исполнения
                    
                    # Проверяем статус ордера
                    try:
                        order_status = self.mex_api.get_order_status(symbol, order['orderId'])
                        if order_status and order_status.get('status') == 'FILLED':
                            logger.info(f"✅ Ордер {order['orderId']} исполнен")
                        else:
                            logger.warning(f"⚠️ Ордер {order['orderId']} еще не исполнен: {order_status}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось проверить статус ордера: {e}")
                
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': limit_price,
                    'order': order
                }
            else:
                logger.error(f"❌ Ошибка размещения ордера балансировки: {order}")
                return {'success': False, 'error': f'API ошибка: {order}'}
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения балансировки {symbol}: {e}")
            return {'success': False, 'error': str(e)}'''
    
    # Заменяем метод
    content = content.replace(old_method, new_method)
    
    # Записываем обратно
    with open('portfolio_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ portfolio_balancer.py исправлен - добавлена проверка баланса и ожидание исполнения ордеров")

if __name__ == "__main__":
    fix_insufficient_position()
