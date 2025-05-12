// Import dependencies
import { calculatePercentageDifference } from './utils.js';

/**
 * Find arbitrage opportunities based on funding rate differences
 * @param {Object} fundingData - Funding rate data from exchanges
 * @returns {Array} List of arbitrage opportunities
 */
export function findArbitrageOpportunities(fundingData) {
  try {
    const opportunities = [];
    const exchanges = Object.keys(fundingData.data);
    const pairs = Object.keys(fundingData.data[exchanges[0]]);
    
    // Compare all exchange pairs
    for (let i = 0; i < exchanges.length; i++) {
      for (let j = i + 1; j < exchanges.length; j++) {
        const exchange1 = exchanges[i];
        const exchange2 = exchanges[j];
        
        // Check each trading pair
        pairs.forEach(pair => {
          const data1 = fundingData.data[exchange1][pair];
          const data2 = fundingData.data[exchange2][pair];
          
          if (!data1 || !data2) return;
          
          // Calculate differences
          const priceDifference = calculatePercentageDifference(data1.price, data2.price);
          const fundingDifference = Math.abs(data1.fundingRate - data2.fundingRate);
          
          // Check if opportunity meets criteria
          if (fundingDifference >= parseFloat(process.env.MIN_FUNDING_DIFF || '0.005') && 
              priceDifference <= parseFloat(process.env.MAX_SPREAD || '0.01')) {
            
            // Determine which exchange has higher funding rate
            const isExchange1Higher = data1.fundingRate > data2.fundingRate;
            
            opportunities.push({
              pair,
              exchange1: isExchange1Higher ? exchange1 : exchange2,
              exchange2: isExchange1Higher ? exchange2 : exchange1,
              fundingRate1: isExchange1Higher ? data1.fundingRate : data2.fundingRate,
              fundingRate2: isExchange1Higher ? data2.fundingRate : data1.fundingRate,
              price1: isExchange1Higher ? data1.price : data2.price,
              price2: isExchange1Higher ? data2.price : data1.price,
              priceDifference: priceDifference.toFixed(2),
              fundingDifference: fundingDifference.toFixed(4),
              timestamp: Date.now()
            });
          }
        });
      }
    }
    
    return opportunities;
  } catch (error) {
    console.error('Error finding arbitrage opportunities:', error);
    return [];
  }
}