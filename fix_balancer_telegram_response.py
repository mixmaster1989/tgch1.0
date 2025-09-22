#!/usr/bin/env python3
"""
Скрипт для исправления балансировщика - добавление уведомлений в Telegram при ответе на запрос разрешения
"""

def fix_balancer_telegram_response():
    # Читаем файл
    with open('active_50_50_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Модифицируем метод check_purchase_permission
    old_method = '''    def check_purchase_permission(self, purchase_amount: float, purchase_type: str = "ALTS") -> Dict:
        """Проверить разрешение на покупку альтов у балансировщика"""
        try:
            # Получаем текущие пропорции портфеля
            portfolio = self.get_portfolio_values()
            
            if portfolio['total_value'] <= 0:
                return {
                    'allowed': False,
                    'reason': 'Портфель пуст или недоступен',
                    'current_alts_ratio': 0.0,
                    'current_btceth_ratio': 0.0
                }
            
            # Рассчитываем текущие пропорции
            alts_ratio = portfolio['alts_value'] / portfolio['total_value']
            btceth_ratio = portfolio['btceth_value_usdt'] / portfolio['total_value']
            
            # Проверяем отклонение от целевых пропорций
            alts_deviation_percent = abs(alts_ratio - self.target_alts_ratio) / self.target_alts_ratio
            btceth_deviation_percent = abs(btceth_ratio - self.target_btceth_ratio) / self.target_btceth_ratio
            
            # Если отклонение меньше 10% - разрешаем покупку
            if alts_deviation_percent < self.min_deviation_threshold and btceth_deviation_percent < self.min_deviation_threshold:
                return {
                    'allowed': True,
                    'reason': f'Пропорции сбалансированы (Альты: {alts_ratio*100:.1f}%, BTC/ETH: {btceth_ratio*100:.1f}%)',
                    'current_alts_ratio': alts_ratio,
                    'current_btceth_ratio': btceth_ratio
                }
            
            # Если альтов больше 50% - блокируем покупку альтов
            if alts_ratio > self.target_alts_ratio and purchase_type == "ALTS":
                return {
                    'allowed': False,
                    'reason': f'Альтов уже {alts_ratio*100:.1f}% > 50% (отклонение {alts_deviation_percent*100:.1f}%)',
                    'current_alts_ratio': alts_ratio,
                    'current_btceth_ratio': btceth_ratio
                }
            
            # Если BTC/ETH больше 50% - разрешаем покупку альтов
            if btceth_ratio > self.target_btceth_ratio and purchase_type == "ALTS":
                return {
                    'allowed': True,
                    'reason': f'BTC/ETH {btceth_ratio*100:.1f}% > 50%, можно покупать альты',
                    'current_alts_ratio': alts_ratio,
                    'current_btceth_ratio': btceth_ratio
                }
            
            # По умолчанию разрешаем
            return {
                'allowed': True,
                'reason': f'Пропорции в норме (Альты: {alts_ratio*100:.1f}%, BTC/ETH: {btceth_ratio*100:.1f}%)',
                'current_alts_ratio': alts_ratio,
                'current_btceth_ratio': btceth_ratio
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки разрешения: {e}")
            return {
                'allowed': False,
                'reason': f'Ошибка проверки: {e}',
                'current_alts_ratio': 0.0,
                'current_btceth_ratio': 0.0
            }'''
    
    new_method = '''    def check_purchase_permission(self, purchase_amount: float, purchase_type: str = "ALTS") -> Dict:
        """Проверить разрешение на покупку альтов у балансировщика"""
        try:
            # Получаем текущие пропорции портфеля
            portfolio = self.get_portfolio_values()
            
            if portfolio['total_value'] <= 0:
                result = {
                    'allowed': False,
                    'reason': 'Портфель пуст или недоступен',
                    'current_alts_ratio': 0.0,
                    'current_btceth_ratio': 0.0
                }
            else:
                # Рассчитываем текущие пропорции
                alts_ratio = portfolio['alts_value'] / portfolio['total_value']
                btceth_ratio = portfolio['btceth_value_usdt'] / portfolio['total_value']
                
                # Проверяем отклонение от целевых пропорций
                alts_deviation_percent = abs(alts_ratio - self.target_alts_ratio) / self.target_alts_ratio
                btceth_deviation_percent = abs(btceth_ratio - self.target_btceth_ratio) / self.target_btceth_ratio
                
                # Если отклонение меньше 10% - разрешаем покупку
                if alts_deviation_percent < self.min_deviation_threshold and btceth_deviation_percent < self.min_deviation_threshold:
                    result = {
                        'allowed': True,
                        'reason': f'Пропорции сбалансированы (Альты: {alts_ratio*100:.1f}%, BTC/ETH: {btceth_ratio*100:.1f}%)',
                        'current_alts_ratio': alts_ratio,
                        'current_btceth_ratio': btceth_ratio
                    }
                
                # Если альтов больше 50% - блокируем покупку альтов
                elif alts_ratio > self.target_alts_ratio and purchase_type == "ALTS":
                    result = {
                        'allowed': False,
                        'reason': f'Альтов уже {alts_ratio*100:.1f}% > 50% (отклонение {alts_deviation_percent*100:.1f}%)',
                        'current_alts_ratio': alts_ratio,
                        'current_btceth_ratio': btceth_ratio
                    }
                
                # Если BTC/ETH больше 50% - разрешаем покупку альтов
                elif btceth_ratio > self.target_btceth_ratio and purchase_type == "ALTS":
                    result = {
                        'allowed': True,
                        'reason': f'BTC/ETH {btceth_ratio*100:.1f}% > 50%, можно покупать альты',
                        'current_alts_ratio': alts_ratio,
                        'current_btceth_ratio': btceth_ratio
                    }
                
                # По умолчанию разрешаем
                else:
                    result = {
                        'allowed': True,
                        'reason': f'Пропорции в норме (Альты: {alts_ratio*100:.1f}%, BTC/ETH: {btceth_ratio*100:.1f}%)',
                        'current_alts_ratio': alts_ratio,
                        'current_btceth_ratio': btceth_ratio
                    }
            
            # 🔥 НОВОЕ: Отправляем ответ в Telegram
            status_icon = "✅" if result['allowed'] else "🚫"
            status_text = "РАЗРЕШЕНО" if result['allowed'] else "ЗАБЛОКИРОВАНО"
            
            response_message = (
                f"{status_icon} <b>ОТВЕТ БАЛАНСИРОВЩИКА: {status_text}</b>\\n\\n"
                f"💰 Сумма запроса: ${purchase_amount:.2f}\\n"
                f"📊 Тип: {purchase_type}\\n\\n"
                f"📈 <b>ТЕКУЩИЕ ПРОПОРЦИИ:</b>\\n"
                f"Альты: {result['current_alts_ratio']*100:.1f}%\\n"
                f"BTC/ETH: {result['current_btceth_ratio']*100:.1f}%\\n\\n"
                f"📝 <b>ПРИЧИНА:</b>\\n"
                f"{result['reason']}\\n\\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            try:
                self.send_telegram_message(response_message)
                logger.info(f"📱 Ответ балансировщика отправлен в Telegram: {status_text}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки ответа в Telegram: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки разрешения: {e}")
            error_result = {
                'allowed': False,
                'reason': f'Ошибка проверки: {e}',
                'current_alts_ratio': 0.0,
                'current_btceth_ratio': 0.0
            }
            
            # Отправляем уведомление об ошибке
            error_message = (
                f"❌ <b>ОШИБКА БАЛАНСИРОВЩИКА</b>\\n\\n"
                f"💰 Сумма запроса: ${purchase_amount:.2f}\\n"
                f"📊 Тип: {purchase_type}\\n\\n"
                f"🚫 <b>ОШИБКА:</b>\\n"
                f"{e}\\n\\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            try:
                self.send_telegram_message(error_message)
            except Exception:
                pass
            
            return error_result'''
    
    # Заменяем метод
    content = content.replace(old_method, new_method)
    
    # Записываем обратно
    with open('active_50_50_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ active_50_50_balancer.py исправлен - добавлены уведомления в Telegram при ответе на запрос разрешения")

if __name__ == "__main__":
    fix_balancer_telegram_response()
