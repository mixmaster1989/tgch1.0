// src/index.js
// Точка входа для модулей src
exports.SmartMoneyAnalyzer = require('./logic/smartMoney').SmartMoneyAnalyzer;
exports.calculateATR = require('./logic/atr').calculateATR;
exports.MEXCWebSocket = require('./data/ws-mexc');
exports.formatSignal = require('./bot/formatSignal').formatSignal;