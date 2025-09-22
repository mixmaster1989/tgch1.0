#!/usr/bin/env python3
"""
Скрипт для исправления балансировщика - добавление конвертации USDT → USDC
"""

def fix_balancer_usdc_conversion():
    # Читаем файл
    with open('active_50_50_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Модифицируем метод buy_btceth_with_usdc
    old_method = '''    async def buy_btceth_with_usdc(self, amount: float) -> bool:
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
            return False'''
    
    new_method = '''    async def buy_btceth_with_usdc(self, amount: float) -> bool:
        """Купить BTC/ETH за USDC"""
        try:
            # 🔥 НОВОЕ: Обеспечиваем USDC для покупки
            logger.info(f"🔄 Проверяем наличие USDC для покупки BTC/ETH на ${amount:.2f}")
            
            if not self.ensure_usdc_for_trade(amount):
                logger.error(f"❌ Не удалось обеспечить USDC для покупки BTC/ETH")
                # Отправляем уведомление об ошибке
                error_message = (
                    f"❌ <b>ОШИБКА КОНВЕРТАЦИИ USDT → USDC</b>\\n\\n"
                    f"💰 Требуется: ${amount:.2f} USDC\\n"
                    f"🔄 Действие: Конвертация USDT → USDC\\n"
                    f"📊 Цель: Покупка BTC/ETH для балансировки\\n\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(error_message)
                return False
            
            # Отправляем уведомление об успешной конвертации
            success_message = (
                f"✅ <b>USDC ПОДГОТОВЛЕН ДЛЯ ПОКУПКИ BTC/ETH</b>\\n\\n"
                f"💰 Сумма: ${amount:.2f} USDC\\n"
                f"🔄 Действие: USDT → USDC (выполнено)\\n"
                f"📊 Цель: Покупка BTC/ETH для балансировки\\n\\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_telegram_message(success_message)
            
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
            return False'''
    
    # Заменяем метод
    content = content.replace(old_method, new_method)
    
    # Записываем обратно
    with open('active_50_50_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ active_50_50_balancer.py исправлен - добавлена конвертация USDT → USDC")

if __name__ == "__main__":
    fix_balancer_usdc_conversion()
