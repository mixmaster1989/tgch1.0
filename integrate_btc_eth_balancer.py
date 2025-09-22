#!/usr/bin/env python3
"""
Скрипт для интеграции с BTC-ETH балансировщиком после покупки BTC/ETH
"""

def integrate_btc_eth_balancer():
    # Читаем active_50_50_balancer.py
    with open('active_50_50_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем импорт PortfolioBalancer
    import_line = "from portfolio_balancer import PortfolioBalancer\n"
    
    # Находим место после импортов
    lines = content.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('from config import'):
            insert_index = i + 1
            break
    
    lines.insert(insert_index, import_line)
    content = '\n'.join(lines)
    
    # Добавляем инициализацию BTC-ETH балансировщика в __init__
    init_pattern = '        self.report_counter = 0'
    replacement = '        self.report_counter = 0\n        self.btc_eth_balancer = PortfolioBalancer()'
    content = content.replace(init_pattern, replacement)
    
    # Модифицируем метод buy_btceth_with_usdc для запуска BTC-ETH балансировки
    old_end_method = '''            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка покупки BTC/ETH: {e}")
            return False'''
    
    new_end_method = '''            # 🔥 НОВОЕ: Запускаем BTC-ETH балансировщик после покупки
            if success_count > 0:
                logger.info("🔄 Запускаем BTC-ETH балансировщик для выравнивания пропорций...")
                try:
                    btc_eth_result = self.btc_eth_balancer.execute_portfolio_rebalance_sync()
                    if btc_eth_result.get('success'):
                        logger.info("✅ BTC-ETH балансировка выполнена успешно")
                        # Отправляем уведомление о BTC-ETH балансировке
                        btc_eth_message = (
                            f"⚖️ <b>BTC-ETH БАЛАНСИРОВКА ВЫПОЛНЕНА</b>\\n\\n"
                            f"📊 Результат: {btc_eth_result.get('message', 'Успешно')}\\n"
                            f"💰 Потрачено: ${btc_eth_result.get('total_spent', 0):.2f}\\n"
                            f"🔄 Операций: {btc_eth_result.get('trades_executed', 0)}\\n\\n"
                            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                        )
                        self.send_telegram_message(btc_eth_message)
                    else:
                        logger.warning(f"⚠️ BTC-ETH балансировка не выполнена: {btc_eth_result.get('message', 'Неизвестная ошибка')}")
                except Exception as e:
                    logger.error(f"❌ Ошибка BTC-ETH балансировки: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка покупки BTC/ETH: {e}")
            return False'''
    
    content = content.replace(old_end_method, new_end_method)
    
    # Записываем обратно
    with open('active_50_50_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ active_50_50_balancer.py обновлен - добавлена интеграция с BTC-ETH балансировщиком")

if __name__ == "__main__":
    integrate_btc_eth_balancer()
