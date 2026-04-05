import api from './api';

const transactionService = {
  /**
   * Get transaction history with filters and pagination
   * Note: This might be called getTransactions OR getTransactionHistory
   */
  async getTransactions(params = {}) {
    try {
      const response = await api.get('/transactions/', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
      throw error;
    }
  },

  // Alias for compatibility
  async getTransactionHistory(params = {}) {
    return this.getTransactions(params);
  },

  /**
   * Get detailed information about a specific transaction
   * THIS IS THE KEY METHOD THAT WAS MISSING!
   */
  async getTransactionDetail(transactionId) {
    try {
      console.log('🔍 Fetching transaction detail for ID:', transactionId);
      const response = await api.get(`/transactions/${transactionId}/`);
      console.log('📦 Response:', response.data);
      
      // Handle different response formats
      const data = response.data.data || response.data;
      console.log('✓ Parsed transaction data:', data);
      
      return data;
    } catch (error) {
      console.error('❌ Failed to fetch transaction detail:', error);
      throw error;
    }
  },

  /**
   * Download transaction receipt as PDF
   */
  async downloadReceipt(transactionId, format = 'pdf') {
    try {
      const response = await api.get(`/transactions/${transactionId}/receipt/`, {
        params: { format },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `receipt-${transactionId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download receipt:', error);
      throw error;
    }
  },

  /**
   * Export transactions to CSV
   */
  async exportToCSV(filters = {}) {
    try {
      const response = await api.get('/transactions/export/', {
        params: { ...filters, format: 'csv' },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transactions-${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export transactions:', error);
      throw error;
    }
  },

  /**
   * Get formatted label for transaction type
   */
  getTypeLabel(type) {
    if (!type) return 'Unknown';
    return type
      .toString()
      .replace(/_/g, ' ')
      .trim()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  },

  /**
   * Format currency for display
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

  /**
   * Format date for display
   */
  formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

export default transactionService;