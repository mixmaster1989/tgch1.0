// src/index.js
// Точка входа для модулей src
exports.SmartMoneyAnalyzer = require('./logic/smartMoney').SmartMoneyAnalyzer;
exports.calculateATR = require('./logic/atr').calculateATR;
exports.MEXCWebSocket = require('./data/ws-mexc');
exports.formatSignal = require('./bot/formatSignal').formatSignal;

// Импорт библиотек
const { initTelegramBot } = require('./bot/telegram');
const MEXCWebSocket = require('./data/ws-mexc');
const { SmartMoneyAnalyzer } = require('./logic/smartMoney');
const fs = require('fs');
const path = require('path');

// Загрузка конфигурации
const configPath = path.join(__dirname, '..', 'config', 'thresholds.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Загрузка переменных окружения
require('dotenv').config();

// Инициализация Telegram-бота
const telegramToken = process.env.TELEGRAM_BOT_TOKEN;
const { bot, sendSignal } = initTelegramBot(telegramToken, config);

// Инициализация WebSocket клиента MEXC
const mexcClient = new MEXCWebSocket();

// Инициализация анализатора Smart Money
const analyzer = new SmartMoneyAnalyzer(config);

// Подписка на новые свечи
mexcClient.on('onNewCandle', (symbol, candle) => {
  console.log(`Получена новая свеча для ${symbol}:`, candle);
  
  // Получение исторических данных
  const ohlcvData = mexcClient.getOHLCV(symbol);
  
  // Генерация сигнала
  const signal = analyzer.generateSignal(symbol, ohlcvData, {
    ...config,
    ...{ symbol }
  });
  
  // Отправка сигнала если он существует
  if (signal) {
    console.log(`Сгенерирован сигнал для ${symbol}:`, signal);
    sendSignal(signal);
  }
});

// Обработка ошибок
bot.on('error', (error) => {
  console.error('Ошибка Telegram-бота:', error);
});

mexcClient.on('error', (error) => {
  console.error('Ошибка MEXC WebSocket:', error);
});

console.log('Smart Money Signal Bot запущен');