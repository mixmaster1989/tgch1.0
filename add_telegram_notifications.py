#!/usr/bin/env python3
"""
Скрипт для добавления уведомлений в Telegram для закупщиков альтов
"""

def add_telegram_notifications():
    # Читаем market_scanner.py
    with open('market_scanner.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем уведомление о запросе разрешения
    old_permission_check = '''            # 🔥 НОВОЕ: ПРОВЕРЯЕМ РАЗРЕШЕНИЕ У БАЛАНСИРОВЩИКА
            logger.info(f"🔍 Запрашиваем разрешение у балансировщика на покупку {symbol}...")
            permission = self.balancer.check_purchase_permission(purchase_amount, "ALTS")'''
    
    new_permission_check = '''            # 🔥 НОВОЕ: ПРОВЕРЯЕМ РАЗРЕШЕНИЕ У БАЛАНСИРОВЩИКА
            logger.info(f"🔍 Запрашиваем разрешение у балансировщика на покупку {symbol}...")
            
            # Отправляем уведомление о запросе разрешения
            request_message = (
                f"🔍 <b>ЗАПРОС РАЗРЕШЕНИЯ НА ПОКУПКУ АЛЬТА</b>\\n\\n"
                f"📈 <b>{symbol}</b>\\n"
                f"💰 Сумма: ${purchase_amount:.2f} USDT\\n"
                f"⭐ Скор: {score}\\n"
                f"📊 RSI: {best_opportunity['rsi']:.1f}\\n\\n"
                f"⚖️ <b>Ожидаем ответ от балансировщика...</b>\\n\\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_telegram_message(request_message)
            
            permission = self.balancer.check_purchase_permission(purchase_amount, "ALTS")'''
    
    content = content.replace(old_permission_check, new_permission_check)
    
    # Записываем обратно
    with open('market_scanner.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ market_scanner.py обновлен - добавлены уведомления о запросе разрешения")
    
    # Теперь модифицируем alt_monitor.py
    with open('alt_monitor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем уведомление о запросе разрешения в alt_monitor
    old_alt_permission_check = '''                # 🔥 НОВОЕ: ПРОВЕРЯЕМ РАЗРЕШЕНИЕ У БАЛАНСИРОВЩИКА
                logger.info(f"🔍 Запрашиваем разрешение у балансировщика на покупку {alt}...")
                permission = self.balancer.check_purchase_permission(spend_amount, "ALTS")'''
    
    new_alt_permission_check = '''                # 🔥 НОВОЕ: ПРОВЕРЯЕМ РАЗРЕШЕНИЕ У БАЛАНСИРОВЩИКА
                logger.info(f"🔍 Запрашиваем разрешение у балансировщика на покупку {alt}...")
                
                # Отправляем уведомление о запросе разрешения
                request_message = (
                    f"🔍 <b>ЗАПРОС РАЗРЕШЕНИЯ НА ПОКУПКУ АЛЬТА</b>\\n\\n"
                    f"💱 <b>{alt}</b>\\n"
                    f"💵 Сумма: ${spend_amount:.2f}\\n"
                    f"🛡️ Анти-хайп: {alt_filter['reason']} ×{alt_filter['multiplier']}\\n\\n"
                    f"⚖️ <b>Ожидаем ответ от балансировщика...</b>\\n\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                PnLMonitor().send_telegram_message(request_message)
                
                permission = self.balancer.check_purchase_permission(spend_amount, "ALTS")'''
    
    content = content.replace(old_alt_permission_check, new_alt_permission_check)
    
    # Записываем обратно
    with open('alt_monitor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ alt_monitor.py обновлен - добавлены уведомления о запросе разрешения")

if __name__ == "__main__":
    add_telegram_notifications()
