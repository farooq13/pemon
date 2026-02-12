
import api from './api';

const transferService = {
  /*
   * Process P2P transfer
   */
  async sendMoney(transferData) {
    try {
      const response = await api.post('/transfers/p2p/', transferData);
      return response.data;
    } catch (error) {
      console.error('Transfer failed:', error);
      throw error;
    }
  },

  /*
   * Validate recipient before transfer
   */
  async validateRecipient(identifier) {
    try {
      const response = await api.post('/transfers/validate-recipient/', {
        identifier
      });
      return response.data;
    } catch (error) {
      console.error('Recipient validation failed:', error);
      throw error;
    }
  },

  /*
   * Get recent transfer recipients
   */
  async getRecentRecipients() {
    try {
      const response = await api.get('/transfers/recent-recipients/');
      return response.data.data;
    } catch (error) {
      console.error('Failed to fetch recent recipients:', error);
      return [];
    }
  },

  /*
   * Format amount for display
   */
  formatAmount(amount) {
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    
    if (isNaN(numAmount)) {
      return '₦0.00';
    }
    
    return `₦${numAmount.toLocaleString('en-NG', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  },

  /*
   * Parse amount string to number
   */
  parseAmount(amountStr) {
    const cleaned = amountStr.replace(/[₦,]/g, '').trim();
    return parseFloat(cleaned) || 0;
  }
};

export default transferService;