// Import dependencies
import schedule from 'node-schedule';
import { findArbitrageOpportunities } from './arbitrage.js';
import { getFundingRates } from './funding.js';
import bot from './bot.js';
import { logToFile, saveHistory, formatDate } from './utils.js';

// Trading cycle configuration
const CYCLE_DURATION = 8 * 60 * 60 * 1000; // 8 hours in milliseconds
const CHECK_INTERVAL = 10 * 60 * 1000; // 10 minutes

let currentPositions = [];

/**
 * Start the trading simulation cycle
 */
export function startSimulation() {
  // Initial check
  checkOpportunities();
  
  // Schedule periodic checks every 10 minutes
  schedule.scheduleJob('*/10 * * * *', checkOpportunities);
  
  // Schedule cycle completion notification every 8 hours
  schedule.scheduleJob('0 */8 * * *', handleCycleCompletion);
}

/**
 * Check for new arbitrage opportunities
 */
async function checkOpportunities() {
  try {
    // Get current funding rates
    const fundingData = await getFundingRates(['Kraken', 'MEXC'], ['BTC/USDT', 'ETH/USDT']);
    
    // Find arbitrage opportunities
    const opportunities = findArbitrageOpportunities(fundingData);
    
    // Handle new opportunities
    if (opportunities.length > 0) {
      // Log and notify about new opportunities
      opportunities.forEach(opportunity => {
        const message = formatOpportunityMessage(opportunity);
        
        logToFile(`New opportunity: ${JSON.stringify(opportunity)}`);
        bot.api.sendMessage(process.env.ADMIN_CHAT_ID, message);
      });
      
      // Open positions
      openPositions(opportunities);
    }
  } catch (error) {
    console.error('Error in simulation check:', error);
    logToFile(`Simulation error: ${error.message}`);
  }
}

/**
 * Open positions for arbitrage opportunities
 * @param {Array} opportunities - List of arbitrage opportunities
 */
function openPositions(opportunities) {
  currentPositions = opportunities.map(opportunity => ({
    ...opportunity,
    entryTime: Date.now(),
    entryFundingRate1: opportunity.fundingRate1,
    entryFundingRate2: opportunity.fundingRate2,
    entryPrice1: opportunity.price1,
    entryPrice2: opportunity.price2
  }));
  
  // Save to history
  saveHistory(currentPositions);
}

/**
 * Handle cycle completion every 8 hours
 */
function handleCycleCompletion() {
  // Calculate and close virtual positions
  const closedPositions = currentPositions.map(position => {
    // In real implementation would get updated values
    const exitFundingRate1 = position.fundingRate1;
    const exitFundingRate2 = position.fundingRate2;
    const exitPrice1 = position.price1;
    const exitPrice2 = position.price2;
    
    // Calculate profit/loss
    const fundingProfit = (exitFundingRate1 - exitFundingRate2) * 3; // 8-hour rate extrapolated to 24 hours
    const priceChange = ((exitPrice2 - exitPrice1) / exitPrice1) * 100;
    const netProfit = fundingProfit - Math.abs(priceChange);
    
    return {
      ...position,
      exitTime: Date.now(),
      exitFundingRate1,
      exitFundingRate2,
      exitPrice1,
      exitPrice2,
      fundingProfit: fundingProfit.toFixed(4),
      priceChange: priceChange.toFixed(2),
      netProfit: netProfit.toFixed(4)
    };
  });
  
  // Calculate results
  const results = calculateResults(closedPositions);
  
  // Log and notify
  logToFile(`Cycle completed: ${JSON.stringify(results)}`);
  bot.api.sendMessage(process.env.ADMIN_CHAT_ID, formatResultsMessage(results));
  
  // Reset positions
  currentPositions = [];
}

/**
 * Format opportunity message for Telegram
 * @param {Object} opportunity - Arbitrage opportunity data
 * @returns {string} Formatted message
 */
function formatOpportunityMessage(opportunity) {
  return `🔔 New arbitrage opportunity detected at ${formatDate(new Date())}:

` +
    `🔹 Pair: ${opportunity.pair}
` +
    `📊 Exchange 1: ${opportunity.exchange1} (${opportunity.fundingRate1}%)
` +
    `📉 Exchange 2: ${opportunity.exchange2} (${opportunity.fundingRate2}%)
` +
    `💰 Price Difference: ${opportunity.priceDifference}%
` +
    `📈 Funding Rate Difference: ${opportunity.fundingDifference}%

` +
    `✅ Suggested Action:
` +
    `- Long position on ${opportunity.exchange1}
` +
    `- Short position on ${opportunity.exchange2}

` +
    `⏱️ Position will be closed automatically in 8 hours.`;
}

/**
 * Format cycle results message for Telegram
 * @param {Object} results - Cycle results data
 * @returns {string} Formatted message
 */
function formatResultsMessage(results) {
  return `✅ Trading cycle completed at ${formatDate(new Date())}:

` +
    `📊 Summary:
` +
    `🔢 Total Opportunities: ${results.total}
` +
    `📈 Profitable: ${results.profitable}
` +
    `📉 Unprofitable: ${results.unprofitable}
` +
    `💸 Total Net Profit: ${results.totalProfit}%

` +
    `⚠️ Positions closed virtually. Manual balance adjustment needed.`;
}

/**
 * Calculate cycle results
 * @param {Array} positions - Closed positions
 * @returns {Object} Results summary
 */
function calculateResults(positions) {
  return {
    total: positions.length,
    profitable: positions.filter(p => parseFloat(p.netProfit) > 0).length,
    unprofitable: positions.filter(p => parseFloat(p.netProfit) <= 0).length,
    totalProfit: positions.reduce((sum, p) => sum + parseFloat(p.netProfit), 0).toFixed(2)
  };
}