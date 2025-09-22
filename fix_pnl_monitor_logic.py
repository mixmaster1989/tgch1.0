#!/usr/bin/env python3
"""
Скрипт для исправления логики PnLMonitor - убрать блокировку всей балансировки при общем отрицательном PnL
"""

def fix_pnl_monitor_logic():
    # Читаем файл
    with open('pnl_monitor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Модифицируем метод check_portfolio_balance
    old_method = '''            # Проверяем, можно ли балансировать
            if total_pnl < 0 and not self.portfolio_balancer.allow_negative_pnl_rebalance:
                logger.warning(f"🚫 Балансировка заблокирована: отрицательный PnL ${total_pnl:.4f}")
                self.portfolio_balancer.blocked_rebalances += 1
                
                # Отправляем уведомление о блокировке
                block_message = (
                    "<b>🚫 БАЛАНСИРОВКА ЗАБЛОКИРОВАНА</b>\\n\\n"
                    f"📉 Общий PnL: ${total_pnl:.4f}\\n"
                    f"🛡️ Причина: Защита от убытков\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\\n\\n"
                    "💡 Балансировка будет разрешена при положительном PnL"
                )
                self.send_telegram_message(block_message)
                return'''
    
    new_method = '''            # 🔥 НОВАЯ ЛОГИКА: Не блокируем всю балансировку при общем отрицательном PnL
            # Теперь PortfolioBalancer сам решает что можно продавать/покупать на основе PnL каждого актива
            logger.info(f"💰 Общий PnL портфеля: ${total_pnl:.4f} - передаем управление PortfolioBalancer")
            
            # Отправляем информационное уведомление (не блокирующее)
            if total_pnl < 0:
                info_message = (
                    "<b>ℹ️ БАЛАНСИРОВКА С ОТРИЦАТЕЛЬНЫМ PnL</b>\\n\\n"
                    f"📉 Общий PnL: ${total_pnl:.4f}\\n"
                    f"🛡️ Защита: Продажа только активов в плюсе\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\\n\\n"
                    "💡 PortfolioBalancer проверит PnL каждого актива отдельно"
                )
                self.send_telegram_message(info_message)'''
    
    # Заменяем метод
    content = content.replace(old_method, new_method)
    
    # Записываем обратно
    with open('pnl_monitor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ pnl_monitor.py исправлен - убрана блокировка всей балансировки при общем отрицательном PnL")

if __name__ == "__main__":
    fix_pnl_monitor_logic()
