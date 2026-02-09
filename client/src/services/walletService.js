import api from './api';

const walletService = {
  /*
    Get wallet balance
   */
  async getBalance() {
    try {
      const response = await api.get('/wallet/balance/');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching wallet balance:', error);
      throw error;
    }
  },

  /*
    Get detailed wallet information
    Includes KYC limits, transaction counts, and comprehensive status
   */
  async getWalletDetails() {
    try {
      const response = await api.get('/wallet/detail/');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching wallet details:', error);
      throw error;
    }
  },

  /*
    Check if user has a wallet and its status
   */
  async checkWalletStatus() {
    try {
      const response = await api.get('/wallet/status/');
      return response.data.data;
    } catch (error) {
      console.error('Error checking wallet status:', error);
      throw error;
    }
  },

  /*
    Format currency amount
   */
  formatCurrency(amount) {
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
    Parse formatted currency string to number
   */
  parseCurrency(formattedAmount) {
    if (!formattedAmount) return 0;
    
    // Remove currency symbol and commas
    const numericString = formattedAmount
      .replace('₦', '')
      .replace(/,/g, '')
      .trim();
    
    return parseFloat(numericString) || 0;
  },

  /*
    Validate if wallet is active
   */
  isWalletActive(walletData) {
    return walletData?.status?.active === true && !walletData?.is_frozen;
  },

  /*
    Get wallet status message
   */
  getStatusMessage(walletData) {
    if (!walletData) {
      return 'Wallet not found';
    }
    
    if (walletData.is_frozen) {
      return walletData.status?.reason || 'Wallet is frozen';
    }
    
    return 'Wallet is active';
  }
};

export default walletService;