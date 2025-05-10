// Копирование из предыдущего файла
// src/bot/telegram.js
"use strict";

const TelegramBot = require('node-telegram-bot-api');
const { formatSignal } = require('./formatSignal');

/**
 * Инициализация и настройка Telegram-бота
 * @param {string} token - Токен Telegram-бота
 * @param {Object} config - Конфигурационные данные
 * @returns {Object} Объект с ботом и функцией отправки сигналов
 */
function initTelegramBot(token, config) {
  // Проверка обязательных параметров
  if (!token) {
    throw new Error("Необходимо указать токен Telegram-бота");
  }
  
  // Создание экземпляра бота
  const bot = new TelegramBot(token, { polling: true });
  
  // Обработка команды /start
  bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    const welcomeMessage = `
Добро пожаловать в Smart Money Signal Bot!

Я генерирую торговые сигналы на основе Smart Money логики и кластерного анализа.

Доступные команды:
/start - Показать это приветствие
/help - Получить помощь
/subscribe - Подписаться на сигналы
/unsubscribe - Отписаться от сигналов
/status - Проверить статус подписки

Сигналы генерируются на основе:
• Кластерного анализа (DBSCAN)
• Волатильности (ATR)
• Уверенности (веса из конфигурации)

Текущая конфигурация:
• DBSCAN: eps=${config.dbscan.eps}, minPoints=${config.dbscan.minPoints}
• ATR: период=${config.atr.period}, tp1=${config.atr.tp1}, tp2=${config.atr.tp2}, stopLoss=${config.atr.stopLoss}
    `;
  
  bot.sendMessage(chatId, welcomeMessage);
}

  // Обработка команды /help
  bot.onText(/\/help/, (msg) => {
    const chatId = msg.chat.id;
    const helpMessage = `
Помощь по командам:
/start - Приветственное сообщение
/help - Это справочное сообщение
/subscribe - Подписаться на сигналы
/unsubscribe - Отписаться от сигналов
/status - Проверить статус подписки

Сигналы генерируются на основе кластерного анализа, волатильности и уверенности
• Уверенность: ${config.confidenceWeights.volume * 100}% объем, ${config.confidenceWeights.rsi * 100}% RSI, ${config.confidenceWeights.density * 100}% плотность
• Горизонт прогноза: ${config.signalHorizon || '4ч'}
• Уровни рассчитываются на основе ATR с множителями:
  TP1: ${config.atr.tp1}x ATR
  TP2: ${config.atr.tp2}x ATR
  Stop: ${config.atr.stopLoss}x ATR
    `;
  
  bot.sendMessage(chatId, helpMessage);
}

  // Обработка команды /subscribe
  bot.onText(/\/subscribe/, (msg) => {
    const chatId = msg.chat.id;
    // Здесь должна быть реализована логика подписки
    bot.sendMessage(chatId, "Вы успешно подписаны на сигналы!");
  });

  // Обработка команды /unsubscribe
  bot.onText(/\/unsubscribe/, (msg) => {
    const chatId = msg.chat.id;
    // Здесь должна быть реализована логика отписки
    bot.sendMessage(chatId, "Вы успешно отписаны от сигналов.");
  });

  // Обработка команды /status
  bot.onText(/\/status/, (msg) => {
    const chatId = msg.chat.id;
    // Здесь должна быть реализована логика проверки статуса
    bot.sendMessage(chatId, "Вы подписаны на сигналы.");
  });

  // Функция для отправки сигнала
  const sendSignal = (signal) => {
    try {
      // Форматирование сигнала
      const { text, options } = formatSignal(signal);
      // Отправка сигнала всем подписчикам
      // Здесь должна быть реализована логика получения списка подписчиков
      bot.sendMessage(
        config.telegram.chatId || 'default_chat_id',
        text,
        options
      );
    } catch (error) {
      console.error("Ошибка при отправке сигнала:", error);
    }
  };

  return {
    bot,
    sendSignal
  };
}

module.exports = { initTelegramBot };