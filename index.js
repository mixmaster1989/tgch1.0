"use strict";

// Загрузка зависимостей
const path = require('path');
const fs = require('fs');
const dotenv = require('dotenv');

// Загрузка конфигурации
const thresholds = require('./config/thresholds.json');

// Импорт компонентов
const { initTelegramBot } = require('./src/bot/telegram');
const MEXCWebSocket = require('./src/data/ws-mexc');
const { SmartMoneyAnalyzer } = require('./src/logic/smartMoney');
const { calculateConfidence } = require('./src/logic/confidence');

// Загрузка переменных окружения
dotenv.config();

// Проверка наличия необходимых переменных окружения
if (!process.env.TELEGRAM_BOT_TOKEN) {
  console.error("TELEGRAM_BOT_TOKEN не найден в .env");
  process.exit(1);
}

if (!process.env.MEXC_API_KEY || !process.env.MEXC_SECRET_KEY) {
  console.warn("MEXC API ключи не найдены в .env");
  console.warn("Продолжение работы возможно, но некоторые функции могут быть ограничены");
}

// Инициализация основных компонентов
try {
  // Инициализация Telegram-бота
  const { bot, sendSignal } = initTelegramBot(process.env.TELEGRAM_BOT_TOKEN, {
    ...thresholds,
    telegram: {
      chatId: process.env.TELEGRAM_CHAT_ID || 'default_chat_id'
    }
  });
  
  // Инициализация MEXC WebSocket клиента
  const mexcWs = new MEXCWebSocket();
  
  // Инициализация анализатора Smart Money
  const smartMoneyAnalyzer = new SmartMoneyAnalyzer(thresholds);
  
  // Обработка новых свечей от MEXC
  mexcWs.on('onNewCandle', (symbol, candle) => {
    console.log(`Новая свеча для ${symbol}:`, candle);
    
    // Получение последних данных OHLCV
    const ohlcvData = mexcWs.getOHLCV(symbol);
    
    // Генерация сигнала
    try {
      const signal = smartMoneyAnalyzer.generateSignal(symbol, ohlcvData, {
        // Здесь могут быть дополнительные рыночные данные
        marketData: {}
      });
      
      if (signal) {
        console.log("Сгенерирован сигнал:", signal);
        sendSignal(signal);
      }
    } catch (error) {
      console.error(`Ошибка генерации сигнала для ${symbol}:`, error);
    }
  });
  
  console.log("Бот успешно запущен и готов к работе!");
  console.log("Подписка на пары:", mexcWs.pairs);
  
  // Обработка завершения работы
  process.on('SIGINT', () => {
    console.log('\nБот останавливается...');
    mexcWs.ws.close();
    bot.stopPolling();
    process.exit(0);
  });
} catch (error) {
  console.error("Ошибка инициализации бота:", error);
  process.exit(1);
}