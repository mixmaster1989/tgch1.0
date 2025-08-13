#!/usr/bin/env python3
"""
Автоматический торговый цикл
Выполняет покупки по найденным возможностям из скана рынка
"""

import asyncio
import time
import logging
from datetime import datetime
from trading_engine import TradingEngine
from market_analyzer import MarketAnalyzer
from mex_api import MexAPI

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_trading.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutoTradingCycle:
    """Автоматический торговый цикл"""
    
    def __init__(self, simulation_mode=True):
        self.trading_engine = TradingEngine(simulation_mode=simulation_mode)
        self.market_analyzer = MarketAnalyzer()
        self.mex_api = MexAPI()
        self.cycle_interval = 300  # 5 минут между циклами
        self.is_running = False
        
    def get_market_scan_report(self) -> dict:
        """Получить отчет скана рынка"""
        try:
            # Получаем рекомендации
            recommendations = self.market_analyzer.get_trading_recommendations()
            
            # Получаем баланс
            balance = self.trading_engine.get_usdt_balance()
            
            # Анализируем рекомендации
            buy_opportunities = [r for r in recommendations if r['action'] == 'BUY']
            neutral_opportunities = [r for r in recommendations if r['action'] == 'HOLD']
            blocked_opportunities = [r for r in recommendations if r['action'] == 'SELL']
            
            # Формируем отчет
            report = {
                'timestamp': datetime.now(),
                'balance_usdt': balance,
                'total_analyzed': len(recommendations),
                'buy_opportunities': len(buy_opportunities),
                'neutral_opportunities': len(neutral_opportunities),
                'blocked_opportunities': len(blocked_opportunities),
                'errors': 0,
                'best_opportunities': buy_opportunities[:4],  # Топ-4
                'neutral_top3': neutral_opportunities[:3],   # Топ-3 нейтральных
                'recommendations': recommendations
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета скана: {e}")
            return {
                'timestamp': datetime.now(),
                'balance_usdt': 0,
                'total_analyzed': 0,
                'buy_opportunities': 0,
                'neutral_opportunities': 0,
                'blocked_opportunities': 0,
                'errors': 1,
                'best_opportunities': [],
                'neutral_top3': [],
                'recommendations': []
            }
    
    def format_scan_report(self, report: dict) -> str:
        """Форматировать отчет скана рынка"""
        timestamp = report['timestamp'].strftime('%d.%m.%Y %H:%M:%S')
        
        message = f"📊 СКАН РЫНКА #{int(time.time()) % 1000}\n"
        message += f"⏰ {timestamp}\n"
        message += f"💰 Баланс USDT: ${report['balance_usdt']:.2f}\n\n"
        
        message += f"📈 СТАТИСТИКА:\n"
        message += f"🔍 Проанализировано: {report['total_analyzed']}/20\n"
        message += f"✅ Возможности покупки: {report['buy_opportunities']}\n"
        message += f"⚠️ Нейтральные: {report['neutral_opportunities']}\n"
        message += f"🚫 Заблокированные: {report['blocked_opportunities']}\n"
        message += f"❌ Ошибки: {report['errors']}\n\n"
        
        if report['best_opportunities']:
            message += "🎯 ЛУЧШИЕ ВОЗМОЖНОСТИ:\n"
            for i, opp in enumerate(report['best_opportunities'], 1):
                message += f"{i}. {opp['symbol']} ${opp['price']:.4f}\n"
                message += f"   ⭐ Скор: {opp['score']} | RSI: {opp.get('rsi', 50.0):.1f}\n"
                if 'reasons' in opp and opp['reasons']:
                    message += f"   🔍 {', '.join(opp['reasons'])}\n"
                message += "\n"
        
        if report['neutral_top3']:
            message += "⚖️ НЕЙТРАЛЬНЫЕ (топ-3):\n"
            for i, opp in enumerate(report['neutral_top3'], 1):
                message += f"{i}. {opp['symbol']} (скор: {opp['score']}, RSI: {opp.get('rsi', 50.0):.1f})\n"
            message += "\n"
        
        # Рекомендация
        if report['buy_opportunities'] > 0:
            message += "💡 РЕКОМЕНДАЦИЯ: Есть возможности для покупки! должен докупать по найденным возможностям\n"
        else:
            message += "💡 РЕКОМЕНДАЦИЯ: Возможностей для покупки не найдено\n"
        
        return message
    
    def execute_buy_opportunities(self, report: dict) -> list:
        """Выполнить покупки по найденным возможностям"""
        results = []
        
        if not report['buy_opportunities']:
            logger.info("Нет возможностей для покупки")
            return results
        
        logger.info(f"Найдено {len(report['buy_opportunities'])} возможностей для покупки")
        
        # Выполняем торговый цикл
        try:
            trading_results = self.trading_engine.run_trading_cycle()
            
            if trading_results['buy_orders']:
                logger.info(f"Выполнено {len(trading_results['buy_orders'])} покупок")
                results.extend(trading_results['buy_orders'])
            else:
                logger.info("Покупки не выполнены")
                
        except Exception as e:
            logger.error(f"Ошибка выполнения торгового цикла: {e}")
        
        return results
    
    async def run_cycle(self):
        """Запустить один торговый цикл"""
        try:
            logger.info("🔄 Запуск торгового цикла...")
            
            # Получаем отчет скана рынка
            report = self.get_market_scan_report()
            
            # Форматируем отчет
            scan_message = self.format_scan_report(report)
            logger.info("📊 Отчет скана рынка:")
            print(scan_message)
            
            # Выполняем покупки по возможностям
            if report['buy_opportunities'] > 0:
                logger.info("🚀 Выполнение покупок по найденным возможностям...")
                buy_results = self.execute_buy_opportunities(report)
                
                if buy_results:
                    logger.info(f"✅ Выполнено {len(buy_results)} покупок")
                    for result in buy_results:
                        if result['result']['success']:
                            logger.info(f"   ✅ {result['symbol']}: {result['result']['quantity']} по ${result['result']['price']:.6f}")
                        else:
                            logger.info(f"   ❌ {result['symbol']}: {result['result']['error']}")
                else:
                    logger.info("❌ Покупки не выполнены")
            else:
                logger.info("⏸️ Нет возможностей для покупки")
            
            logger.info("✅ Торговый цикл завершен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка торгового цикла: {e}")
    
    async def start_auto_trading(self):
        """Запустить автоматическую торговлю"""
        self.is_running = True
        logger.info("🚀 Запуск автоматической торговли...")
        
        while self.is_running:
            try:
                await self.run_cycle()
                
                # Ждем до следующего цикла
                logger.info(f"⏰ Ожидание {self.cycle_interval} секунд до следующего цикла...")
                await asyncio.sleep(self.cycle_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Остановка автоматической торговли...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле торговли: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке
    
    def stop_auto_trading(self):
        """Остановить автоматическую торговлю"""
        self.is_running = False
        logger.info("🛑 Автоматическая торговля остановлена")

def main():
    """Главная функция"""
    print("🚀 АВТОМАТИЧЕСКАЯ ТОРГОВЛЯ ПО СКАНУ РЫНКА")
    print("=" * 60)
    
    # Создаем торговый цикл в режиме симуляции
    auto_trader = AutoTradingCycle(simulation_mode=True)
    
    try:
        # Запускаем автоматическую торговлю
        asyncio.run(auto_trader.start_auto_trading())
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка пользователем")
        auto_trader.stop_auto_trading()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()