// Import dependencies
import { Bot } from 'grammy';
import { commands, ADMIN_CHAT_ID } from './utils.js';
import { startSimulation } from './simulation.js';
import 'dotenv/config';

// Create bot instance
const bot = new Bot(process.env.BOT_TOKEN);

// Set admin chat ID
process.env.ADMIN_CHAT_ID = ADMIN_CHAT_ID;

// Register commands
bot.command('status', commands.status);
bot.command('history', commands.history);

// Start bot and simulation
bot.start();
startSimulation();

// Notify admin that bot is started
bot.api.sendMessage(process.env.ADMIN_CHAT_ID, '🚀 Bot started successfully!');

export default bot;