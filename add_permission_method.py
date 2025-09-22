#!/usr/bin/env python3
"""
Скрипт для добавления метода проверки разрешения в балансировщик
"""

def add_permission_method():
    # Читаем файл
    with open('active_50_50_balancer.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Находим место для вставки (после строки 337)
    insert_index = 338
    
    # Новый метод
    new_method = """    def check_purchase_permission(self, purchase_amount: float, purchase_type: str = "ALTS") -> Dict:
        \"\"\"Проверить разрешение на покупку альтов у балансировщика\"\"\"
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
            }
    
"""
    
    # Вставляем новый метод
    lines.insert(insert_index, new_method)
    
    # Записываем обратно
    with open('active_50_50_balancer.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Метод check_purchase_permission добавлен в active_50_50_balancer.py")

if __name__ == "__main__":
    add_permission_method()
