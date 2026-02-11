import { useState } from 'react';
import { X, Download, Share2, Copy, CheckCircle, AlertCircle } from 'lucide-react';
import transactionService from '../../services/transactionService';

/*
 * Mobile-responsive modal showing complete transaction details.
 * Includes receipt download and share functionality.
 */
const TransactionDetailModal = ({ transaction, isOpen, onClose }) => {
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen || !transaction) return null;

  const statusColors = transactionService.getStatusColor(transaction.status);

  const handleDownloadReceipt = async () => {
    setDownloading(true);
    try {
      await transactionService.downloadReceipt(transaction.id, 'pdf');
    } catch (error) {
      alert('Failed to download receipt. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyReference = async () => {
    try {
      await navigator.clipboard.writeText(transaction.reference);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      alert('Failed to copy reference');
    }
  };

  const handleShare = async () => {
    const shareData = {
      title: 'Transaction Receipt',
      text: `Transaction ${transaction.reference} - ${transactionService.formatCurrency(transaction.amount)}`,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      // Fallback: copy to clipboard
      handleCopyReference();
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-end sm:items-center justify-center p-0 sm:p-4">
        <div className="relative bg-white w-full sm:max-w-2xl sm:rounded-2xl rounded-t-2xl shadow-xl transform transition-all max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-2xl z-10">
            <h3 className="text-lg font-bold text-gray-900">Transaction Details</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content - Scrollable */}
          <div className="overflow-y-auto flex-1 px-6 py-6 space-y-6">
            {/* Status Banner */}
            <div className={`
              rounded-xl p-4 flex items-center justify-between
              ${statusColors.bg} ${statusColors.border} border
            `}>
              <div className="flex items-center gap-3">
                {transaction.status === 'COMPLETED' ? (
                  <CheckCircle className={`w-6 h-6 ${statusColors.text}`} />
                ) : (
                  <AlertCircle className={`w-6 h-6 ${statusColors.text}`} />
                )}
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className={`font-semibold ${statusColors.text}`}>
                    {transaction.status_display || transaction.status}
                  </p>
                </div>
              </div>
              
              {transaction.status === 'COMPLETED' && (
                <svg className={`w-12 h-12 ${statusColors.text}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
            </div>

            {/* Amount */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 text-center">
              <p className="text-sm text-gray-600 mb-1">Amount</p>
              <p className="text-4xl font-bold text-gray-900">
                {transaction.formatted_amount || transactionService.formatCurrency(transaction.amount)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {transactionService.getTypeLabel(transaction.transaction_type)}
              </p>
            </div>

            {/* Transaction Information */}
            <div className="bg-gray-50 rounded-lg divide-y divide-gray-200">
              {/* Reference */}
              <div className="p-4">
                <p className="text-xs text-gray-600 mb-1">Reference Number</p>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-mono font-semibold text-gray-900 break-all">
                    {transaction.reference}
                  </p>
                  <button
                    onClick={handleCopyReference}
                    className="flex-shrink-0 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition"
                    title="Copy reference"
                  >
                    {copied ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Date & Time */}
              <div className="p-4">
                <p className="text-xs text-gray-600 mb-1">Date & Time</p>
                <p className="text-sm font-medium text-gray-900">
                  {new Date(transaction.created_at).toLocaleString('en-US', {
                    weekday: 'short',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>

              {/* Type */}
              <div className="p-4">
                <p className="text-xs text-gray-600 mb-1">Transaction Type</p>
                <p className="text-sm font-medium text-gray-900">
                  {transactionService.getTypeLabel(transaction.transaction_type)}
                </p>
              </div>

              {/* Sender (if available) */}
              {transaction.user_email && (
                <div className="p-4">
                  <p className="text-xs text-gray-600 mb-1">From</p>
                  <p className="text-sm font-medium text-gray-900">
                    {transaction.sender_name || transaction.user_email}
                  </p>
                  <p className="text-xs text-gray-500">{transaction.user_email}</p>
                </div>
              )}

              {/* Recipient (if available) */}
              {transaction.recipient_email && (
                <div className="p-4">
                  <p className="text-xs text-gray-600 mb-1">To</p>
                  <p className="text-sm font-medium text-gray-900">
                    {transaction.recipient_name || transaction.recipient_email}
                  </p>
                  <p className="text-xs text-gray-500">{transaction.recipient_email}</p>
                </div>
              )}

              {/* Description */}
              {transaction.description && (
                <div className="p-4">
                  <p className="text-xs text-gray-600 mb-1">Description</p>
                  <p className="text-sm text-gray-900">{transaction.description}</p>
                </div>
              )}
            </div>

            {/* Ledger Entries (if available) */}
            {transaction.ledger_entries && transaction.ledger_entries.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3">Ledger Entries</h4>
                <div className="bg-gray-50 rounded-lg divide-y divide-gray-200">
                  {transaction.ledger_entries.map((entry, index) => (
                    <div key={index} className="p-4 flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {entry.entry_type === 'DEBIT' ? 'Debit' : 'Credit'}
                        </p>
                        <p className="text-xs text-gray-600">{entry.wallet_owner}</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${
                          entry.entry_type === 'DEBIT' ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {entry.formatted_amount}
                        </p>
                        <p className="text-xs text-gray-600">
                          Balance: {transactionService.formatCurrency(entry.balance_after)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Info */}
            {transaction.metadata && Object.keys(transaction.metadata).length > 0 && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-medium text-blue-900 mb-2">Additional Information</p>
                <pre className="text-xs text-blue-800 overflow-x-auto">
                  {JSON.stringify(transaction.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 space-y-3 rounded-b-2xl">
            {transaction.status === 'COMPLETED' && (
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleDownloadReceipt}
                  disabled={downloading}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  {downloading ? 'Downloading...' : 'Receipt'}
                </button>

                <button
                  onClick={handleShare}
                  className="flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition"
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
              </div>
            )}

            <button
              onClick={onClose}
              className="w-full py-3 text-gray-700 font-medium hover:bg-gray-50 rounded-lg transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionDetailModal;