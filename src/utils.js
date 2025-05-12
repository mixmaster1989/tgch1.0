// Import dependencies
import fs from 'fs/promises';
import path from 'path';
import 'dotenv/config';

// Ensure data directory exists
const DATA_DIR = path.join(process.cwd(), 'data');
await fs.mkdir(DATA_DIR, { recursive: true });

/**
 * Calculate percentage difference between two values
 * @param {number} a First value
 * @param {number} b Second value
 * @returns {number} Percentage difference
 */
export function calculatePercentageDifference(a, b) {
  return ((Math.abs(a - b) / ((a + b) / 2)) * 100).toFixed(2);
}

/**
 * Format date in ISO format
 * @param {Date} date Date object
 * @returns {string} Formatted date string
 */
export function formatDate(date) {
  return date.toISOString().replace(/T/, ' ').replace(/\..+/, '');
}

/**
 * Log message to file
 * @param {string} message Message to log
 */
export async function logToFile(message) {
  const date = new Date();
  const fileName = `${date.toISOString().split('T')[0]}_log.txt`;
  const filePath = path.join(DATA_DIR, fileName);
  
  const logMessage = `[${formatDate(date)}] ${message}\n`;
  
  try {
    await fs.appendFile(filePath, logMessage);
  } catch (error) {
    console.error('Error writing to log file:', error);
  }
}

/**
 * Save history to JSON file
 * @param {Array} data History data to save
 */
export async function saveHistory(data) {
  const date = new Date();
  const fileName = `${date.toISOString().split('T')[0]}_history.json`;
  const filePath = path.join(DATA_DIR, fileName);
  
  try {
    // Read existing history
    let history = [];
    try {
      const fileData = await fs.readFile(filePath, 'utf8');
      history = JSON.parse(fileData) || [];
    } catch (error) {
      // File doesn't exist yet
    }
    
    // Add new data
    history.push(...data);
    
    // Write back to file
    await fs.writeFile(filePath, JSON.stringify(history, null, 2));
  } catch (error) {
    console.error('Error saving history:', error);
    await logToFile(`History save error: ${error.message}`);
  }
}

/**
 * Telegram command handlers
 */
export const commands = {
  status: async (ctx) => {
    try {
      ctx.reply('Bot is running and monitoring funding rate arbitrage opportunities.');
    } catch (error) {
      console.error('Error in status command:', error);
      ctx.reply('Error retrieving status. Please try again later.');
    }
  },
  history: async (ctx) => {
    try {
      const historyFiles = await fs.readdir(DATA_DIR);
      const jsonFiles = historyFiles.filter(f => f.endsWith('_history.json'));
      
      if (jsonFiles.length === 0) {
        ctx.reply('No history data available yet.');
        return;
      }
      
      // Read latest history file
      const latestFile = jsonFiles.sort().reverse()[0];
      const filePath = path.join(DATA_DIR, latestFile);
      const fileData = await fs.readFile(filePath, 'utf8');
      const history = JSON.parse(fileData);
      
      // Format response
      let response = `History from ${latestFile.replace('_history.json', '')}:\n\n`;
      
      history.forEach((entry, index) => {
        response += `${index + 1}. ${entry.pair} - ${entry.fundingDifference}% difference\n`;
      });
      
      ctx.reply(response);
    } catch (error) {
      console.error('Error retrieving history:', error);
      ctx.reply('Error retrieving history data.');
    }
  }
};

// Admin chat ID from environment
export const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID || '';