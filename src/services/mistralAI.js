const axios = require('axios');
const logger = require('../utils/logger');

class MistralAIService {
  constructor() {
    this.apiKey = process.env.MISTRAL_API_KEY;
    this.model = process.env.MISTRAL_MODEL || 'mistral-large-latest';
    this.apiUrl = 'https://api.mistral.ai/v1/chat/completions';
    this.rateLimitResetTime = null;
    this.maxRetries = 3;
    this.baseDelay = 1000; // 1 second
  }

  async isAvailable() {
    if (!this.apiKey) {
      logger.warn('Mistral API key not configured');
      return false;
    }
    
    // Check if we're currently rate limited
    if (this.rateLimitResetTime && Date.now() < this.rateLimitResetTime) {
      logger.warn('Mistral AI currently rate limited');
      return false;
    }
    
    try {
      // Simple health check
      await axios.get('https://api.mistral.ai/v1/models', {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        },
        timeout: 5000
      });
      return true;
    } catch (error) {
      logger.error(`Mistral AI health check failed: ${error.message}`);
      return false;
    }
  }

  async makeRequest(prompt, temperature = 0.7, maxRetries = this.maxRetries) {
    // Check if we have a recent rate limit error
    if (this.rateLimitResetTime && Date.now() < this.rateLimitResetTime) {
      const waitTime = this.rateLimitResetTime - Date.now();
      logger.warn(`Rate limited, waiting ${Math.ceil(waitTime/1000)} seconds before retry`);
      await new Promise(resolve => setTimeout(resolve, Math.min(waitTime, 30000)));
    }

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await axios.post(this.apiUrl, {
          model: this.model,
          messages: [{ role: 'user', content: prompt }],
          temperature: temperature
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          },
          timeout: 30000
        });

        // Reset rate limit tracking on success
        this.rateLimitResetTime = null;
        
        return response.data.choices[0].message;
      } catch (error) {
        logger.error(`Mistral AI request failed (attempt ${attempt + 1}/${maxRetries + 1}): ${error.message}`);
        
        // Handle rate limiting
        if (error.response && error.response.status === 429) {
          if (attempt < maxRetries) {
            // Calculate wait time with exponential backoff
            const waitTime = Math.min(this.baseDelay * Math.pow(2, attempt), 30000); // Max 30 seconds
            logger.warn(`Rate limited, waiting ${waitTime}ms before retry ${attempt + 1}`);
            
            // Set rate limit reset time if provided by server
            const resetHeader = error.response.headers['x-ratelimit-reset'];
            if (resetHeader) {
              this.rateLimitResetTime = parseInt(resetHeader) * 1000;
            } else {
              this.rateLimitResetTime = Date.now() + waitTime + 2000; // Add 2 second buffer
            }
            
            await new Promise(resolve => setTimeout(resolve, waitTime));
            continue;
          }
        }
        
        // Handle other errors
        if (attempt < maxRetries && this.isRetryableError(error)) {
          const waitTime = this.baseDelay * Math.pow(2, attempt);
          logger.warn(`Retryable error, waiting ${waitTime}ms before retry ${attempt + 1}`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          continue;
        }
        
        throw error;
      }
    }
    
    throw new Error('Max retries exceeded for Mistral AI request');
  }

  isRetryableError(error) {
    // Define which errors are retryable
    if (!error.response) return true; // Network errors
    const status = error.response.status;
    return status === 408 || status === 429 || status === 500 || status === 502 || status === 503 || status === 504;
  }

  // New method to get a more conservative estimate of availability
  async getConservativeAvailability() {
    if (!this.apiKey) {
      return { available: false, reason: 'API key not configured' };
    }
    
    // Check rate limit
    if (this.rateLimitResetTime && Date.now() < this.rateLimitResetTime) {
      const secondsLeft = Math.ceil((this.rateLimitResetTime - Date.now()) / 1000);
      return { available: false, reason: `Rate limited for ${secondsLeft} seconds` };
    }
    
    return { available: true, reason: 'Ready for requests' };
  }
}

module.exports = MistralAIService;