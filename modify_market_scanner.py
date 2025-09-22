#!/usr/bin/env python3
"""
Скрипт для модификации market_scanner.py - добавление проверки разрешения у балансировщика
"""

def modify_market_scanner():
    # Читаем файл
    with open('market_scanner.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем импорт балансировщика в начало файла
    import_line = "from active_50_50_balancer import Active5050Balancer\n"
    
    # Находим место после импортов
    lines = content.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('from config import'):
            insert_index = i + 1
            break
    
    lines.insert(insert_index, import_line)
    
    # Модифицируем класс MarketScanner
    modified_content = '\n'.join(lines)
    
    # Добавляем инициализацию балансировщика в __init__
    init_pattern = '        self.anti_hype_filter = AntiHypeFilter()'
    replacement = '        self.anti_hype_filter = AntiHypeFilter()\n        self.balancer = Active5050Balancer()'
    modified_content = modified_content.replace(init_pattern, replacement)
    
    # Модифицируем функцию auto_buy_opportunities
    old_auto_buy = '''    async def auto_buy_opportunities(self, scan_results: Dict):
        """Автоматическая покупка возможностей"""
        try:
            buy_opportunities = scan_results.get('buy_opportunities', [])
            if not buy_opportunities:
                logger.info("❌ Нет возможностей для покупки")
                return
            
            # Проверяем баланс USDT
            usdt_balance = self.get_usdt_balance()
            if usdt_balance < 6.0:
                logger.info(f"❌ Недостаточно USDT: ${usdt_balance:.2f}")
                # Отправляем уведомление о недостатке средств
                insufficient_message = (
                    f"💰 <b>НЕДОСТАТОЧНО СРЕДСТВ ДЛЯ ПОКУПКИ</b>\\n\\n"
                    f"📊 Найдено возможностей: {len(buy_opportunities)}\\n"
                    f"💵 Текущий баланс USDT: ${usdt_balance:.2f}\\n"
                    f"⚠️ Минимум для покупки: $6.00\\n\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(insufficient_message)
                return'''
    
    new_auto_buy = '''    async def auto_buy_opportunities(self, scan_results: Dict):
        """Автоматическая покупка возможностей"""
        try:
            buy_opportunities = scan_results.get('buy_opportunities', [])
            if not buy_opportunities:
                logger.info("❌ Нет возможностей для покупки")
                return
            
            # Проверяем баланс USDT
            usdt_balance = self.get_usdt_balance()
            if usdt_balance < 6.0:
                logger.info(f"❌ Недостаточно USDT: ${usdt_balance:.2f}")
                # Отправляем уведомление о недостатке средств
                insufficient_message = (
                    f"💰 <b>НЕДОСТАТОЧНО СРЕДСТВ ДЛЯ ПОКУПКИ</b>\\n\\n"
                    f"📊 Найдено возможностей: {len(buy_opportunities)}\\n"
                    f"💵 Текущий баланс USDT: ${usdt_balance:.2f}\\n"
                    f"⚠️ Минимум для покупки: $6.00\\n\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(insufficient_message)
                return
            
            # Берем лучшую возможность
            best_opportunity = buy_opportunities[0]
            symbol = best_opportunity['symbol']
            score = best_opportunity['score']
            
            # Рассчитываем сумму покупки в процентах от свободного USDT с фоллбэком на минимум
            purchase_amount = usdt_balance * (PURCHASE_PCT_OF_USDT / 100.0)
            if usdt_balance >= PURCHASE_MIN_USDT:
                purchase_amount = max(PURCHASE_MIN_USDT, purchase_amount)
            purchase_amount = min(purchase_amount, PURCHASE_MAX_USDT)
            
            if purchase_amount < PURCHASE_MIN_USDT:
                logger.info("❌ Сумма покупки слишком мала")
                # Отправляем уведомление о малой сумме
                small_amount_message = (
                    f"💰 <b>СУММА ПОКУПКИ СЛИШКОМ МАЛА</b>\\n\\n"
                    f"📊 Найдено возможностей: {len(buy_opportunities)}\\n"
                    f"�� Рассчитанная сумма: ${purchase_amount:.2f}\\n"
                    f"💳 Доступный баланс: ${usdt_balance:.2f}\\n"
                    f"⚠️ Минимум для покупки: ${PURCHASE_MIN_USDT:.2f}\\n\\n"
                    f"💡 <b>РЕШЕНИЕ:</b> Пополните баланс до $6+ для активации автопокупок\\n\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(small_amount_message)
                return
            
            # 🔥 НОВОЕ: ПРОВЕРЯЕМ РАЗРЕШЕНИЕ У БАЛАНСИРОВЩИКА
            logger.info(f"🔍 Запрашиваем разрешение у балансировщика на покупку {symbol}...")
            permission = self.balancer.check_purchase_permission(purchase_amount, "ALTS")
            
            if not permission['allowed']:
                logger.warning(f"🚫 Балансировщик заблокировал покупку: {permission['reason']}")
                # Отправляем уведомление о блокировке
                blocked_message = (
                    f"🚫 <b>ПОКУПКА ЗАБЛОКИРОВАНА БАЛАНСИРОВЩИКОМ</b>\\n\\n"
                    f"📈 <b>{symbol}</b>\\n"
                    f"💰 Сумма: ${purchase_amount:.2f} USDT\\n"
                    f"⭐ Скор: {score}\\n\\n"
                    f"⚖️ <b>ПРИЧИНА БЛОКИРОВКИ:</b>\\n"
                    f"{permission['reason']}\\n\\n"
                    f"📊 <b>ТЕКУЩИЕ ПРОПОРЦИИ:</b>\\n"
                    f"Альты: {permission['current_alts_ratio']*100:.1f}%\\n"
                    f"BTC/ETH: {permission['current_btceth_ratio']*100:.1f}%\\n\\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(blocked_message)
                return
            
            logger.info(f"✅ Балансировщик разрешил покупку: {permission['reason']}")'''
    
    # Заменяем функцию
    modified_content = modified_content.replace(old_auto_buy, new_auto_buy)
    
    # Записываем обратно
    with open('market_scanner.py', 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ market_scanner.py модифицирован - добавлена проверка разрешения у балансировщика")

if __name__ == "__main__":
    modify_market_scanner()
