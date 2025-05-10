// src/logic/smartMoney.js
"use strict";

const { calculateATR } = require('./atr');
const { calculateConfidence } = require('./confidence');

/**
 * Класс для генерации торговых сигналов на основе Smart Money логики
 */
class SmartMoneyAnalyzer {
  /**
   * Создание нового экземпляра SmartMoneyAnalyzer
   * @param {Object} config - Конфигурационные данные
   */
  constructor(config = {}) {
    // Проверка конфигурации
    if (!config.atr || !config.dbscan) {
      throw new Error("Некорректная конфигурация для SmartMoneyAnalyzer");
    }
    
    this.config = config;
    this.atrPeriod = config.atr.period || 14;
    this.signalHistory = [];
  }

  /**
   * Генерация торгового сигнала на основе данных OHLCV
   * @param {string} symbol - Символ пары (например, "BTC_USDT")
   * @param {Array} ohlcvData - Массив данных OHLCV
   * @param {Object} marketData - Дополнительные рыночные данные
   * @returns {Object|null} Торговый сигнал или null, если условия не выполнены
   */
  generateSignal(symbol, ohlcvData, marketData = {}) {
    try {
      // Проверка достаточности данных
      if (!ohlcvData || ohlcvData.length < 10) {
        console.warn(`Недостаточно данных для генерации сигнала для ${symbol}`);
        return null;
      }
      
      // Расчет ATR
      const atr = calculateATR(ohlcvData, this.atrPeriod);
      
      // Расчет уровней входа, тейк-профита и стоп-лосса
      const signalType = this.identifySignalType(ohlcvData, atr, marketData);
      
      // Если сигнал не определен, возвращаем null
      if (!signalType) {
        return null;
      }
      
      // Расчет уровней
      const levels = this.calculateLevels(ohlcvData[ohlcvData.length - 1].close, atr, signalType, this.config.atr);
      
      // Расчет уверенности в сигнале
      const confidence = calculateConfidence(ohlcvData, {
        ...this.config,
        ...marketData
      });
      
      // Если уверенность ниже порога, не генерируем сигнал
      if (confidence < this.config.minConfidence) {
        console.log(`Сигнал для ${symbol} отменен: уверенность ${confidence.toFixed(2)} ниже порога ${this.config.minConfidence.toFixed(2)}`);
        return null;
      }
      
      // Формирование сигнала
      const signal = {
        pair: symbol,
        signalType,
        confidence,
        entry: levels.entry,
        stop: levels.stop,
        tp1: levels.tp1,
        tp2: levels.tp2,
        rrRatio: levels.rrRatio,
        horizon: this.config.signalHorizon || '4ч',
        timestamp: new Date().toISOString()
      };
      
      // Сохранение сигнала в истории
      this.signalHistory.push(signal);
      
      return signal;
    } catch (error) {
      console.error(`Ошибка генерации сигнала для ${symbol}:", error);
      return null;
    }
  }

  /**
   * Определение типа сигнала на основе кластерного анализа
   * @param {Array} ohlcvData - Массив данных OHLCV
   * @param {number} atr - Рассчитанное значение ATR
   * @param {Object} marketData - Дополнительные рыночные данные
   * @returns {string|null} Тип сигнала ('Long' | 'Short' | null)
   */
  identifySignalType(ohlcvData, atr, marketData = {}) {
    if (!ohlcvData || ohlcvData.length < 2) {
      return null;
    }
    
    const latestCandle = ohlcvData[ohlcvData.length - 1];
    const prevCandle = ohlcvData[ohlcvData.length - 2];
    
    // Пример простой логики определения типа сигнала
    const priceChange = (latestCandle.close - prevCandle.close) / prevCandle.close;
    
    // Расчет волатильности
    const volatility = atr / latestCandle.close;
    
    // Логика определения типа сигнала
    // В реальной реализации здесь будет сложный кластерный анализ
    if (priceChange > volatility * 0.5) {
      return 'Long';
    } else if (priceChange < -volatility * 0.5) {
      return 'Short';
    } else {
      return null; // Недостаточно данных для определения сигнала
    }
  }

  /**
   * Расчет уровней входа, тейк-профитов и стоп-лосса
   * @param {number} entryPrice - Цена входа
   * @param {number} atr - Рассчитанное значение ATR
   * @param {string} signalType - Тип сигнала ('Long' | 'Short')
   * @param {Object} atrConfig - Конфигурация ATR (multipliers для TP и SL)
   * @returns {Object} Объект с уровнями входа, тейк-профита и стоп-лосса
   */
  calculateLevels(entryPrice, atr, signalType, atrConfig = {}) {
    // Расчет базовых уровней на основе ATR
    const config = {
      tp1: 1.5,
      tp2: 3.0,
      stopLoss: 1.0,
      ...atrConfig
    };
    
    let tp1 = 0;
    let tp2 = 0;
    let stop = 0;
    
    if (signalType === 'Long') {
      // Для Long позиции
      tp1 = entryPrice * (1 + config.tp1 * atr / entryPrice);
      tp2 = entryPrice * (1 + config.tp2 * atr / entryPrice);
      stop = entryPrice * (1 - config.stopLoss * atr / entryPrice);
    } else if (signalType === 'Short') {
      // Для Short позиции
      tp1 = entryPrice * (1 - config.tp1 * atr / entryPrice);
      tp2 = entryPrice * (1 - config.tp2 * atr / entryPrice);
      stop = entryPrice * (1 + config.stopLoss * atr / entryPrice);
    } else {
      return {
        entry: entryPrice,
        tp1: entryPrice,
        tp2: entryPrice,
        stop: entryPrice,
        rrRatio: 0,
        atr: atr
      };
    }
    
    // Расчет R:R
    const avgProfit = (Math.abs(tp1 - entryPrice) + Math.abs(tp2 - entryPrice)) / 2;
    const avgRisk = Math.abs(entryPrice - stop);
    const rrRatio = avgProfit / avgRisk;
    
    return {
      entry: entryPrice,
      tp1,
      tp2,
      stop,
      atr,
      rrRatio: rrRatio.toFixed(1),
      volatility: (atr / entryPrice).toFixed(3)
    };
  }
}

module.exports = SmartMoneyAnalyzer;