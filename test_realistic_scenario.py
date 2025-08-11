#!/usr/bin/env python3
"""
Реалистичный сценарий проблемы PnL монитора
Показывает, как старый метод приводил к продаже ETH дешевле покупки
"""

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealisticPnLScenario:
    """Реалистичный сценарий проблемы PnL"""
    
    def __init__(self):
        self.profit_threshold = 0.40  # Порог прибыли $0.40
        
        # Реалистичная история ордеров ETH (как в логах)
        self.eth_order_history = [
            # Покупки в разное время по разным ценам
            {'side': 'BUY', 'quantity': 0.05, 'price': 4200.0, 'time': 1000, 'note': 'Первая покупка'},
            {'side': 'BUY', 'quantity': 0.03, 'price': 4210.0, 'time': 2000, 'note': 'Вторая покупка'},
            {'side': 'BUY', 'quantity': 0.02, 'price': 4220.0, 'time': 3000, 'note': 'Третья покупка'},
            {'side': 'BUY', 'quantity': 0.04, 'price': 4230.0, 'time': 4000, 'note': 'Четвертая покупка'},
            {'side': 'BUY', 'quantity': 0.01, 'price': 4240.0, 'time': 5000, 'note': 'Пятая покупка'},
            
            # Продажи по более высоким ценам (прибыльные)
            {'side': 'SELL', 'quantity': 0.08, 'price': 4250.0, 'time': 6000, 'note': 'Первая продажа'},
            {'side': 'SELL', 'quantity': 0.05, 'price': 4240.0, 'time': 7000, 'note': 'Вторая продажа'},
            {'side': 'SELL', 'quantity': 0.02, 'price': 4230.0, 'time': 8000, 'note': 'Третья продажа'},
            
            # Дополнительная покупка (остаток)
            {'side': 'BUY', 'quantity': 0.00242, 'price': 4200.0, 'time': 9000, 'note': 'Остаток'},
        ]
        
        # Текущий баланс ETH
        self.current_eth_balance = 0.00242
        
    def show_order_history(self):
        """Показать историю ордеров"""
        logger.info("📋 ИСТОРИЯ ОРДЕРОВ ETH:")
        logger.info("=" * 80)
        
        total_bought = 0
        total_sold = 0
        total_buy_cost = 0
        total_sell_revenue = 0
        
        for i, order in enumerate(self.eth_order_history, 1):
            side_emoji = "🟢" if order['side'] == 'BUY' else "🔴"
            side_text = "ПОКУПКА" if order['side'] == 'BUY' else "ПРОДАЖА"
            
            if order['side'] == 'BUY':
                total_bought += order['quantity']
                total_buy_cost += order['quantity'] * order['price']
            else:
                total_sold += order['quantity']
                total_sell_revenue += order['quantity'] * order['price']
            
            logger.info(
                f"{i:2d}. {side_emoji} {side_text}: {order['quantity']:.6f} ETH @ ${order['price']:.2f} "
                f"(${order['quantity'] * order['price']:.2f}) - {order['note']}"
            )
        
        logger.info("=" * 80)
        logger.info(f"📊 ИТОГО ПОКУПОК: {total_bought:.6f} ETH на ${total_buy_cost:.2f}")
        logger.info(f"📊 ИТОГО ПРОДАЖ: {total_sold:.6f} ETH на ${total_sell_revenue:.2f}")
        logger.info(f"📊 ОСТАТОК: {total_bought - total_sold:.6f} ETH")
        logger.info(f"📊 ТЕКУЩИЙ БАЛАНС: {self.current_eth_balance:.6f} ETH")
        
        # Рассчитываем реальную прибыль от продаж
        if total_sold > 0:
            avg_buy_price = total_buy_cost / total_bought
            avg_sell_price = total_sell_revenue / total_sold
            realized_profit = (avg_sell_price - avg_buy_price) * total_sold
            
            logger.info(f"💰 Средняя цена покупки: ${avg_buy_price:.4f}")
            logger.info(f"💰 Средняя цена продажи: ${avg_sell_price:.4f}")
            logger.info(f"📈 Реализованная прибыль: ${realized_profit:.4f}")
        
        logger.info("=" * 80)
    
    def demonstrate_old_method_problem(self):
        """Демонстрация проблемы старого метода"""
        logger.info("❌ ДЕМОНСТРАЦИЯ ПРОБЛЕМЫ СТАРОГО МЕТОДА:")
        logger.info("=" * 80)
        
        # Старый метод: учитывает ВСЕ покупки
        buy_orders = [order for order in self.eth_order_history if order['side'] == 'BUY']
        total_buy_cost = sum(order['quantity'] * order['price'] for order in buy_orders)
        total_buy_quantity = sum(order['quantity'] for order in buy_orders)
        old_avg_buy_price = total_buy_cost / total_buy_quantity
        
        logger.info(f"🔴 СТАРЫЙ МЕТОД (неправильный):")
        logger.info(f"   - Учитывает ВСЕ покупки: {total_buy_quantity:.6f} ETH")
        logger.info(f"   - Общая стоимость: ${total_buy_cost:.2f}")
        logger.info(f"   - Средняя цена покупки: ${old_avg_buy_price:.4f}")
        
        # Показываем проблему на разных ценах
        test_prices = [4200, 4250, 4300]
        
        for price in test_prices:
            current_value = self.current_eth_balance * price
            cost_basis = self.current_eth_balance * old_avg_buy_price
            pnl = current_value - cost_basis
            
            logger.info(f"   📊 При цене ${price}: PnL = ${pnl:.4f}")
            
            if pnl > self.profit_threshold:
                logger.info(f"   ⚠️  ЛОЖНЫЙ СИГНАЛ! Продажа при убытке!")
        
        logger.info("=" * 80)
    
    def demonstrate_new_method_solution(self):
        """Демонстрация решения новым методом"""
        logger.info("✅ ДЕМОНСТРАЦИЯ РЕШЕНИЯ НОВЫМ МЕТОДОМ:")
        logger.info("=" * 80)
        
        # Новый метод: учитывает только оставшиеся монеты
        buy_orders = [order for order in self.eth_order_history if order['side'] == 'BUY']
        sell_orders = [order for order in self.eth_order_history if order['side'] == 'SELL']
        
        total_bought = sum(order['quantity'] for order in buy_orders)
        total_sold = sum(order['quantity'] for order in sell_orders)
        remaining_quantity = total_bought - total_sold
        
        # Рассчитываем среднюю цену покупки для оставшихся монет
        total_buy_cost = sum(order['quantity'] * order['price'] for order in buy_orders)
        new_avg_buy_price = total_buy_cost / total_bought
        
        logger.info(f"🟢 НОВЫЙ МЕТОД (правильный FIFO):")
        logger.info(f"   - Общее количество покупок: {total_bought:.6f} ETH")
        logger.info(f"   - Общее количество продаж: {total_sold:.6f} ETH")
        logger.info(f"   - Оставшиеся монеты: {remaining_quantity:.6f} ETH")
        logger.info(f"   - Средняя цена покупки: ${new_avg_buy_price:.4f}")
        
        # Показываем правильный расчет на разных ценах
        test_prices = [4200, 4250, 4300]
        
        for price in test_prices:
            current_value = self.current_eth_balance * price
            cost_basis = self.current_eth_balance * new_avg_buy_price
            pnl = current_value - cost_basis
            
            logger.info(f"   📊 При цене ${price}: PnL = ${pnl:.4f}")
            
            if pnl > self.profit_threshold:
                logger.info(f"   ✅ ПРАВИЛЬНЫЙ СИГНАЛ! Продажа при прибыли!")
            else:
                logger.info(f"   📈 PnL ниже порога, продажа не требуется")
        
        logger.info("=" * 80)
    
    def show_critical_issue(self):
        """Показать критическую проблему старого метода"""
        logger.info("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА СТАРОГО МЕТОДА:")
        logger.info("=" * 80)
        
        # Показываем, как старый метод мог продать ETH дешевле покупки
        buy_orders = [order for order in self.eth_order_history if order['side'] == 'BUY']
        total_buy_cost = sum(order['quantity'] * order['price'] for order in buy_orders)
        total_buy_quantity = sum(order['quantity'] for order in buy_orders)
        old_avg_buy_price = total_buy_cost / total_buy_quantity
        
        logger.info(f"🔴 СТАРЫЙ МЕТОД:")
        logger.info(f"   - Средняя цена покупки: ${old_avg_buy_price:.4f}")
        logger.info(f"   - Текущий баланс: {self.current_eth_balance:.6f} ETH")
        
        # Показываем, при какой цене старый метод давал бы ложный сигнал
        false_signal_price = old_avg_buy_price + (self.profit_threshold / self.current_eth_balance)
        
        logger.info(f"   - Ложный сигнал на продажу при цене: ${false_signal_price:.4f}")
        logger.info(f"   - Это означает продажу по цене ВЫШЕ средней покупки")
        
        # Показываем реальную ситуацию
        logger.info(f"\n📊 РЕАЛЬНАЯ СИТУАЦИЯ:")
        logger.info(f"   - Большая часть ETH уже продана по прибыльным ценам")
        logger.info(f"   - Остался только небольшой остаток: {self.current_eth_balance:.6f} ETH")
        logger.info(f"   - Этот остаток должен оцениваться по его реальной себестоимости")
        
        logger.info("=" * 80)

def main():
    """Главная функция"""
    logger.info("🚨 АНАЛИЗ КРИТИЧЕСКОЙ ПРОБЛЕМЫ PnL МОНИТОРА")
    logger.info("=" * 80)
    
    scenario = RealisticPnLScenario()
    
    # Показываем историю ордеров
    scenario.show_order_history()
    
    # Демонстрируем проблему старого метода
    scenario.demonstrate_old_method_problem()
    
    # Демонстрируем решение новым методом
    scenario.demonstrate_new_method_solution()
    
    # Показываем критическую проблему
    scenario.show_critical_issue()
    
    logger.info("=" * 80)
    logger.info("💡 ВЫВОД:")
    logger.info("   Старый метод мог приводить к продаже ETH по ценам")
    logger.info("   ниже реальной себестоимости, что приводило к убыткам!")
    logger.info("   Новый FIFO метод решает эту проблему.")

if __name__ == "__main__":
    main() 