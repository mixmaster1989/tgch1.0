#!/usr/bin/env python3
"""
Скрипт для модификации alt_monitor.py - добавление проверки разрешения у балансировщика
"""

def modify_alt_monitor():
    # Читаем файл
    with open('alt_monitor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем импорт балансировщика в начало файла
    import_line = "from active_50_50_balancer import Active5050Balancer\n"
    
    # Находим место после импортов
    lines = content.split('\n')
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('from post_sale_balancer import PostSaleBalancer'):
            insert_index = i + 1
            break
    
    lines.insert(insert_index, import_line)
    
    # Модифицируем класс AltsMonitor
    modified_content = '\n'.join(lines)
    
    # Добавляем инициализацию балансировщика в __init__
    init_pattern = '        self.anti_hype_filter = AntiHypeFilter()'
    replacement = '        self.anti_hype_filter = AntiHypeFilter()\n        self.balancer = Active5050Balancer()'
    modified_content = modified_content.replace(init_pattern, replacement)
    
    # Модифицируем функцию run_once - добавляем проверку разрешения перед покупкой
    old_buy_section = '''        # BUY phase с анти-хайп фильтром
        balances = self._get_balances()
        usdt = balances.get('USDT', {}).get('free', 0.0)
        if usdt > 0.0:
            # 1% от депозита
            deposit_usd = self._get_total_deposit_usd()
            base_amount = deposit_usd * 0.01 if deposit_usd > 0 else 0.0
            # выбираем первый доступный альт из списка
            for alt in TOP5_ALTS:
                if alt in balances:  # уже держим; пропускаем
                    continue
                sym = f"{alt}USDT"
                if not self.adv.get_symbol_rules(sym):
                    continue
                # Проверяем анти-хайп фильтр для альта
                alt_filter = self.anti_hype_filter.check_buy_permission(sym)
                if not alt_filter['allowed']:
                    logger.warning(f"🚫 {alt} покупка заблокирована: {alt_filter['reason']}")
                    continue
                # Применяем множитель фильтра
                planned_amount = base_amount * alt_filter['multiplier']
                # Покупаем минимум лот если 1% меньше
                min_lot = self._get_min_lot_usdt(sym)
                spend_amount = max(planned_amount, min_lot)
                # Кэп по свободному USDT
                spend_amount = min(spend_amount, usdt)
                if spend_amount < min_lot or spend_amount <= 0:
                    logger.info(f"❌ Недостаточно USDT для минимального лота {alt}: нужно ${min_lot:.2f}, есть ${usdt:.2f}")
                    break
                logger.info(f"Buying {alt} for ${spend_amount:.2f} (1% депозита ×{alt_filter['multiplier']})")
                res = self._place_limit_buy_with_retries(sym, spend_amount, max_retries=3)
                logger.info(f"BUY result: {res}")
                if res and 'orderId' in res:
                    buy_message = (
                        f"<b>🛍️ ПОКУПКА АЛЬТКОИНА</b>\\n\\n"
                        f"💱 Актив: {alt}\\n"
                        f"💵 Сумма: ${spend_amount:.2f}\\n"
                        f"🛡️ Фильтр: {alt_filter['reason']} ×{alt_filter['multiplier']}\\n"
                        f"🆔 Ордер: <code>{res['orderId']}</code>\\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    PnLMonitor().send_telegram_message(buy_message)
                # совершаем только одну покупку за цикл
                break'''
    
    new_buy_section = '''        # BUY phase с анти-хайп фильтром И проверкой балансировщика
        balances = self._get_balances()
        usdt = balances.get('USDT', {}).get('free', 0.0)
        if usdt > 0.0:
            # 1% от депозита
            deposit_usd = self._get_total_deposit_usd()
            base_amount = deposit_usd * 0.01 if deposit_usd > 0 else 0.0
            # выбираем первый доступный альт из списка
            for alt in TOP5_ALTS:
                if alt in balances:  # уже держим; пропускаем
                    continue
                sym = f"{alt}USDT"
                if not self.adv.get_symbol_rules(sym):
                    continue
                # Проверяем анти-хайп фильтр для альта
                alt_filter = self.anti_hype_filter.check_buy_permission(sym)
                if not alt_filter['allowed']:
                    logger.warning(f"🚫 {alt} покупка заблокирована анти-хайп фильтром: {alt_filter['reason']}")
                    continue
                # Применяем множитель фильтра
                planned_amount = base_amount * alt_filter['multiplier']
                # Покупаем минимум лот если 1% меньше
                min_lot = self._get_min_lot_usdt(sym)
                spend_amount = max(planned_amount, min_lot)
                # Кэп по свободному USDT
                spend_amount = min(spend_amount, usdt)
                if spend_amount < min_lot or spend_amount <= 0:
                    logger.info(f"❌ Недостаточно USDT для минимального лота {alt}: нужно ${min_lot:.2f}, есть ${usdt:.2f}")
                    break
                
                # 🔥 НОВОЕ: ПРОВЕРЯЕМ РАЗРЕШЕНИЕ У БАЛАНСИРОВЩИКА
                logger.info(f"🔍 Запрашиваем разрешение у балансировщика на покупку {alt}...")
                permission = self.balancer.check_purchase_permission(spend_amount, "ALTS")
                
                if not permission['allowed']:
                    logger.warning(f"🚫 Балансировщик заблокировал покупку {alt}: {permission['reason']}")
                    # Отправляем уведомление о блокировке
                    blocked_message = (
                        f"🚫 <b>ПОКУПКА {alt} ЗАБЛОКИРОВАНА БАЛАНСИРОВЩИКОМ</b>\\n\\n"
                        f"💵 Сумма: ${spend_amount:.2f}\\n"
                        f"🛡️ Анти-хайп: {alt_filter['reason']} ×{alt_filter['multiplier']}\\n\\n"
                        f"⚖️ <b>ПРИЧИНА БЛОКИРОВКИ:</b>\\n"
                        f"{permission['reason']}\\n\\n"
                        f"📊 <b>ТЕКУЩИЕ ПРОПОРЦИИ:</b>\\n"
                        f"Альты: {permission['current_alts_ratio']*100:.1f}%\\n"
                        f"BTC/ETH: {permission['current_btceth_ratio']*100:.1f}%\\n\\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    PnLMonitor().send_telegram_message(blocked_message)
                    continue
                
                logger.info(f"✅ Балансировщик разрешил покупку {alt}: {permission['reason']}")
                
                logger.info(f"Buying {alt} for ${spend_amount:.2f} (1% депозита ×{alt_filter['multiplier']})")
                res = self._place_limit_buy_with_retries(sym, spend_amount, max_retries=3)
                logger.info(f"BUY result: {res}")
                if res and 'orderId' in res:
                    buy_message = (
                        f"<b>🛍️ ПОКУПКА АЛЬТКОИНА</b>\\n\\n"
                        f"💱 Актив: {alt}\\n"
                        f"💵 Сумма: ${spend_amount:.2f}\\n"
                        f"🛡️ Фильтр: {alt_filter['reason']} ×{alt_filter['multiplier']}\\n"
                        f"⚖️ Балансировщик: {permission['reason']}\\n"
                        f"🆔 Ордер: <code>{res['orderId']}</code>\\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    PnLMonitor().send_telegram_message(buy_message)
                # совершаем только одну покупку за цикл
                break'''
    
    # Заменяем секцию покупки
    modified_content = modified_content.replace(old_buy_section, new_buy_section)
    
    # Записываем обратно
    with open('alt_monitor.py', 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ alt_monitor.py модифицирован - добавлена проверка разрешения у балансировщика")

if __name__ == "__main__":
    modify_alt_monitor()
