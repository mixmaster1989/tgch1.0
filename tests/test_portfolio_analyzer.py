#!/usr/bin/env python3
"""
Тест анализатора портфеля MEXCAITRADE
"""

import asyncio
from portfolio_analyzer import PortfolioAnalyzer

def test_portfolio_analyzer():
    """Тест анализатора портфеля"""
    print("🧪 ТЕСТ АНАЛИЗАТОРА ПОРТФЕЛЯ")
    print("=" * 50)
    
    try:
        # Создаем анализатор
        analyzer = PortfolioAnalyzer()
        print("✅ Анализатор создан")
        
        # Получаем полную информацию об аккаунте
        print("📊 Получение данных аккаунта...")
        account_data = analyzer.get_account_full_info()
        
        if account_data:
            print("✅ Данные аккаунта получены")
            
            # Проверяем структуру данных
            account_info = account_data.get('account_info', {})
            portfolio_pnl = account_data.get('portfolio_pnl', {})
            open_orders = account_data.get('open_orders', [])
            
            print(f"📋 Балансов: {len(account_info.get('balances', []))}")
            print(f"📈 Позиций: {portfolio_pnl.get('total_positions', 0)}")
            print(f"📋 Открытых ордеров: {len(open_orders)}")
            
            # Форматируем отчет
            print("📝 Форматирование отчета...")
            report = analyzer.format_portfolio_report(account_data)
            
            if report and len(report) > 100:
                print("✅ Отчет сформирован")
                print(f"📄 Длина отчета: {len(report)} символов")
                
                # Показываем первые 500 символов
                print("\n📋 ПРЕВЬЮ ОТЧЕТА:")
                print("-" * 50)
                print(report[:500] + "..." if len(report) > 500 else report)
                print("-" * 50)
                
                # Спрашиваем пользователя о отправке
                response = input("\n❓ Отправить отчет в Telegram? (y/n): ")
                if response.lower() == 'y':
                    print("📤 Отправка отчета...")
                    success = analyzer.send_portfolio_report()
                    if success:
                        print("✅ Отчет отправлен!")
                    else:
                        print("❌ Ошибка отправки")
                else:
                    print("⏭️ Отчет не отправлен")
            else:
                print("❌ Ошибка форматирования отчета")
        else:
            print("❌ Не удалось получить данные аккаунта")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_analyzer() 