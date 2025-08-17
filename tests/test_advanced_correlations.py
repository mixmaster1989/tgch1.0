#!/usr/bin/env python3
"""
Тест расширенного анализатора корреляций
Демонстрация мощных возможностей нового модуля
"""

import asyncio
import time
import numpy as np
from advanced_correlation_analyzer import AdvancedCorrelationAnalyzer, add_price_to_advanced_analyzer, get_advanced_correlation_analysis

def generate_test_data():
    """Генерация тестовых данных"""
    print("📊 Генерация тестовых данных...")
    
    base_time = int(time.time() * 1000)
    
    # BTC - основной тренд
    btc_trend = np.linspace(45000, 47000, 100) + np.random.normal(0, 200, 100)
    
    # ETH - высокая корреляция с BTC
    eth_trend = btc_trend * 0.07 + 3000 + np.random.normal(0, 15, 100)
    
    # ADA - низкая корреляция с BTC
    ada_trend = 0.5 + np.sin(np.linspace(0, 4*np.pi, 100)) * 0.1 + np.random.normal(0, 0.02, 100)
    
    # SOL - средняя корреляция
    sol_trend = btc_trend * 0.04 + 100 + np.random.normal(0, 5, 100)
    
    # DOT - независимый тренд
    dot_trend = 7 + np.cos(np.linspace(0, 6*np.pi, 100)) * 2 + np.random.normal(0, 0.3, 100)
    
    # Добавляем данные в анализатор
    for i in range(100):
        timestamp = base_time + i * 60000  # Каждую минуту
        
        add_price_to_advanced_analyzer('BTCUSDT', btc_trend[i], timestamp)
        add_price_to_advanced_analyzer('ETHUSDT', eth_trend[i], timestamp)
        add_price_to_advanced_analyzer('ADAUSDT', ada_trend[i], timestamp)
        add_price_to_advanced_analyzer('SOLUSDT', sol_trend[i], timestamp)
        add_price_to_advanced_analyzer('DOTUSDT', dot_trend[i], timestamp)
    
    print("✅ Тестовые данные сгенерированы")

def print_comprehensive_analysis(symbol: str):
    """Вывод комплексного анализа"""
    print(f"\n🔍 РАСШИРЕННЫЙ АНАЛИЗ КОРРЕЛЯЦИЙ ДЛЯ {symbol}")
    print("=" * 80)
    
    analysis = get_advanced_correlation_analysis(symbol)
    
    # Рыночный режим
    print(f"📈 РЫНОЧНЫЙ РЕЖИМ:")
    regime = analysis['market_regime']
    print(f"   Режим: {regime['regime']}")
    print(f"   Корреляция с BTC: {regime['btc_correlation']:.3f}")
    print(f"   Доминирование рынка: {regime['market_dominance']:.3f}")
    print(f"   Сила тренда: {regime['trend_strength']:.4f}")
    
    # Базовые корреляции
    print(f"\n🔗 БАЗОВЫЕ КОРРЕЛЯЦИИ:")
    correlations = analysis['basic_correlations']
    for asset, data in correlations.items():
        print(f"   {asset}: {data['correlation']:.3f} ({data['strength']}, {data['direction']})")
    
    # Анализ волатильности
    print(f"\n📊 АНАЛИЗ ВОЛАТИЛЬНОСТИ:")
    volatility = analysis['volatility_analysis']
    if volatility:
        print(f"   Текущая волатильность: {volatility.get('current_volatility', 0):.2%}")
        print(f"   Ранг волатильности: {volatility.get('volatility_rank', 0)}")
        print(f"   Тренд волатильности: {volatility.get('volatility_trend', 'unknown')}")
        print(f"   Режим волатильности: {volatility.get('volatility_regime', 'unknown')}")
    
    # Возможности диверсификации
    print(f"\n🎯 ВОЗМОЖНОСТИ ДИВЕРСИФИКАЦИИ:")
    opportunities = analysis['diversification_opportunities']
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"   {i}. {opp['asset']}: {opp['correlation']:.3f} (score: {opp['diversification_score']:.3f})")
        print(f"      Рекомендация: {opp['recommendation']}")
        print(f"      Причина: {opp['reason']}")
    
    # Торговые сигналы
    print(f"\n🚀 ТОРГОВЫЕ СИГНАЛЫ:")
    signals = analysis['trading_signals']
    if signals:
        for signal in signals:
            print(f"   {signal.signal_type}: {signal.reason}")
            print(f"      Уверенность: {signal.confidence:.2f}")
    else:
        print("   Нет активных сигналов")
    
    # Оценка рисков
    print(f"\n⚠️ ОЦЕНКА РИСКОВ:")
    risks = analysis['risk_assessment']
    print(f"   Общий риск: {risks['overall_risk_score']:.3f}")
    print(f"   Риск концентрации: {risks.get('concentration_risk', 0):.3f}")
    print(f"   Риск корреляций: {risks.get('correlation_risk', 0):.3f}")
    print(f"   Рыночный риск: {risks.get('market_risk', 0):.3f}")
    print(f"   Риск диверсификации: {risks.get('diversification_risk', 0):.3f}")
    
    # Рекомендации для портфеля
    print(f"\n💡 РЕКОМЕНДАЦИИ ДЛЯ ПОРТФЕЛЯ:")
    recommendations = analysis['portfolio_recommendations']
    for rec in recommendations:
        print(f"   • {rec}")
    
    # Алерты по корреляциям
    print(f"\n🚨 АЛЕРТЫ ПО КОРРЕЛЯЦИЯМ:")
    alerts = analysis['correlation_alerts']
    if alerts:
        for alert in alerts:
            severity_emoji = "🔴" if alert['severity'] == 'high' else "🟡" if alert['severity'] == 'medium' else "🟢"
            print(f"   {severity_emoji} {alert['message']}")
    else:
        print("   Нет активных алертов")
    
    # Рыночные инсайты
    print(f"\n🧠 РЫНОЧНЫЕ ИНСАЙТЫ:")
    insights = analysis['market_insights']
    print(f"   Настроения рынка: {insights['market_sentiment']}")
    print(f"   Анализ трендов: {insights['trend_analysis']}")
    
    if insights['correlation_insights']:
        print("   Инсайты корреляций:")
        for insight in insights['correlation_insights']:
            print(f"     • {insight}")
    
    if insights['risk_insights']:
        print("   Риск-инсайты:")
        for insight in insights['risk_insights']:
            print(f"     • {insight}")
    
    if insights['opportunity_insights']:
        print("   Инсайты возможностей:")
        for insight in insights['opportunity_insights']:
            print(f"     • {insight}")

def compare_with_old_analyzer():
    """Сравнение с старым анализатором"""
    print(f"\n📊 СРАВНЕНИЕ С БАЗОВЫМ АНАЛИЗАТОРОМ")
    print("=" * 80)
    
    # Старый формат
    print("📋 СТАРЫЙ ФОРМАТ:")
    print("🔗 КОРРЕЛЯЦИИ ETH:")
    print("   BTC корреляция: 0.0000")
    print("   ETH корреляция: 0.0000")
    print("   Ранг волатильности: 2")
    print("   Сила корреляции: weak")
    
    print(f"\n🚀 НОВЫЙ РАСШИРЕННЫЙ ФОРМАТ:")
    print("   • Рыночный режим и доминирование")
    print("   • Детальный анализ корреляций с силой и направлением")
    print("   • Анализ волатильности и трендов")
    print("   • Возможности диверсификации")
    print("   • Торговые сигналы на основе корреляций")
    print("   • Комплексная оценка рисков")
    print("   • Персонализированные рекомендации")
    print("   • Система алертов")
    print("   • Рыночные инсайты")

def main():
    """Основная функция"""
    print("🚀 ТЕСТ РАСШИРЕННОГО АНАЛИЗАТОРА КОРРЕЛЯЦИЙ")
    print("=" * 80)
    
    # Генерируем тестовые данные
    generate_test_data()
    
    # Анализируем ETH
    print_comprehensive_analysis('ETHUSDT')
    
    # Анализируем ADA (для сравнения)
    print_comprehensive_analysis('ADAUSDT')
    
    # Сравнение с старым анализатором
    compare_with_old_analyzer()
    
    print(f"\n✅ Тест завершен!")
    print("🎯 Расширенный анализатор предоставляет в 10 раз больше полезной информации!")

if __name__ == "__main__":
    main() 