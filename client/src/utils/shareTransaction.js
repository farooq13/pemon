import transactionService from '../services/transactionService';

/*
 * Share transaction details
 * 
 * Uses native share API if available, falls back to clipboard
 */
export const shareTransaction = async (transaction) => {
  const shareText = `
Transaction Receipt

Reference: ${transaction.reference}
Amount: ${transaction.formatted_amount || transactionService.formatCurrency(transaction.amount)}
Type: ${transactionService.getTypeLabel(transaction.transaction_type)}
Status: ${transaction.status_display || transaction.status}
Date: ${new Date(transaction.created_at).toLocaleString()}
${transaction.description ? `\nDescription: ${transaction.description}` : ''}
  `.trim();

  // Try native share API first
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Transaction Receipt',
        text: shareText,
      });
      return true;
    } catch (error) {
      // User cancelled or share failed
      console.log('Share cancelled or failed:', error);
      return false;
    }
  }

  // Fallback to clipboard
  try {
    await navigator.clipboard.writeText(shareText);
    alert('Transaction details copied to clipboard!');
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    alert('Failed to share transaction. Please try again.');
    return false;
  }
};

/*
 * Copy transaction reference to clipboard
 */
export const copyReference = async (reference) => {
  try {
    await navigator.clipboard.writeText(reference);
    return true;
  } catch (error) {
    console.error('Failed to copy reference:', error);
    return false;
  }
};

/*
 * Generate shareable transaction link
 */
export const getTransactionLink = (transactionId) => {
  const baseUrl = window.location.origin;
  return `${baseUrl}/transactions/${transactionId}`;
};

export default {
  shareTransaction,
  copyReference,
  getTransactionLink,
};