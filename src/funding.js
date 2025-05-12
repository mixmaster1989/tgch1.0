// Import dependencies
import axios from 'axios';

// CoinGlass API configuration
const COINGLASS_API = 'https://futures2.coinglass.com/api/pro/v1/futures/funding_rates';

/**
 * Fetch funding rates from multiple exchanges
 * @param {Array} exchanges - List of exchange names
 * @param {Array} pairs - Trading pairs to check
 * @returns {Object} Funding rate data
 */
export async function getFundingRates(exchanges = ['Kraken', 'MEXC'], pairs = ['BTC/USDT', 'ETH/USDT']) {
  try {
    // Get API key from environment
    const apiKey = process.env.COINGLASS_API_KEY;
    
    // Make API request to CoinGlass
    const response = await axios.get(COINGLASS_API, {
      params: {
        api_key: apiKey,
        symbol: pairs[0].replace('/', ''), // API expects format like BTCUSDT
        period: '8h' // Funding period
      }
    });
    
    // Process response data
    const processedData = {};
    
    // Process exchanges
    if (response.data && response.data.data) {
      const exchangesData = response.data.data.exchangeRates || [];
      
      exchangesData.forEach(exchangeData => {
        if (exchanges.includes(exchangeData.exchange)) {
          processedData[exchangeData.exchange] = {};
          
          // Process pairs
          pairs.forEach(pair => {
            processedData[exchangeData.exchange][pair] = {
              fundingRate: parseFloat(exchangeData.rate),
              price: parseFloat(exchangeData.price),
              exchange: exchangeData.exchange,
              timestamp: Date.now()
            };
          });
        }
      });
    }
    
    return {
      timestamp: Date.now(),
      data: processedData
    };
  } catch (error) {
    console.error('Error fetching funding rates:', error.response?.data || error.message);
    throw error;
  }
}