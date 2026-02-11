import api from './api';

const transactionService = {
  /*
   * Get paginated transaction list with filters
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

  /*
   * Get single transaction details
   */
  async getTransactionDetail(transactionId) {
    try {
      const response = await api.get(`/transactions/${transactionId}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch transaction details:', error);
      throw error;
    }
  },

  /*
   * Get transaction statistics
   */
  async getTransactionStats(period = '30d') {
    try {
      const response = await api.get('/transactions/stats/', {
        params: { period }
      });
      return response.data.data;
    } catch (error) {
      console.error('Failed to fetch transaction stats:', error);
      throw error;
    }
  },

  /*
   * Get transaction summary
   */
  async getTransactionSummary() {
    try {
      const response = await api.get('/transactions/summary/');
      return response.data.data;
    } catch (error) {
      console.error('Failed to fetch transaction summary:', error);
      throw error;
    }
  },

  /*
   * Download transaction receipt
   */
  async downloadReceipt(transactionId, format = 'pdf') {
    try {
      const response = await api.get(
        `/transactions/${transactionId}/receipt/`,
        {
          params: { format },
          responseType: format === 'pdf' ? 'blob' : 'text'
        }
      );

      if (format === 'pdf') {
        // Create download link for PDF
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `receipt_${transactionId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } else {
        // Open HTML in new window
        const newWindow = window.open();
        newWindow.document.write(response.data);
        newWindow.document.close();
      }
    } catch (error) {
      console.error('Failed to download receipt:', error);
      throw error;
    }
  },

  /*
   * Export transactions to CSV
   */
  async exportTransactions(params = {}) {
    try {
      const response = await api.get('/transactions/export/', {
        params,
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const filename = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
      link.setAttribute('download', filename);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export transactions:', error);
      throw error;
    }
  },

  /*
   * Format transaction type for display
   */
  getTypeLabel(type) {
    const labels = {
      'DEPOSIT': 'Deposit',
      'WITHDRAWAL': 'Withdrawal',
      'TRANSFER': 'Transfer',
      'BILL_PAYMENT': 'Bill Payment',
      'AIRTIME': 'Airtime',
      'DATA': 'Data',
      'ELECTRICITY': 'Electricity',
      'CABLE_TV': 'Cable TV',
      'REVERSAL': 'Reversal',
      'REFUND': 'Refund',
      'COMMISSION': 'Commission',
      'CHARGE': 'Charge',
    };
    
    return labels[type] || type;
  },

  /*
   * Get status color
   */
  getStatusColor(status) {
    const colors = {
      'COMPLETED': {
        bg: 'bg-green-100',
        text: 'text-green-800',
        border: 'border-green-200'
      },
      'PENDING': {
        bg: 'bg-yellow-100',
        text: 'text-yellow-800',
        border: 'border-yellow-200'
      },
      'PROCESSING': {
        bg: 'bg-blue-100',
        text: 'text-blue-800',
        border: 'border-blue-200'
      },
      'FAILED': {
        bg: 'bg-red-100',
        text: 'text-red-800',
        border: 'border-red-200'
      },
      'REVERSED': {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        border: 'border-gray-200'
      }
    };
    
    return colors[status] || colors['PENDING'];
  },

  /*
   * Format currency
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
   * Get transaction direction (debit/credit) for user
   */
  getTransactionDirection(transaction, userId) {
    // If user is sender, it's a debit
    if (transaction.user_email === userId || transaction.is_debit === true) {
      return 'debit';
    }
    
    // If user is recipient, it's a credit
    return 'credit';
  }
};

export default transactionService;