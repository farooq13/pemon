import { X, Copy, Download, Share2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { useState } from 'react';
import transactionService from '../../services/transactionService';


const TransactionDetailModal = ({ transaction, onClose }) => {
  const [copied, setCopied] = useState(false);

  if (!transaction) return null;

  const isDebit = transaction.is_debit;

  // Status styling
  const statusConfig = {
    COMPLETED: {
      icon: CheckCircle,
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      iconColor: 'text-green-600'
    },
    PENDING: {
      icon: Clock,
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      iconColor: 'text-yellow-600'
    },
    FAILED: {
      icon: AlertCircle,
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      iconColor: 'text-red-600'
    },
    PROCESSING: {
      icon: Clock,
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      iconColor: 'text-blue-600'
    }
  };

  const config = statusConfig[transaction.status] || statusConfig.PENDING;
  const StatusIcon = config.icon;

  const handleCopyReference = async () => {
    try {
      await navigator.clipboard.writeText(transaction.reference);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleDownloadReceipt = async () => {
    try {
      await transactionService.downloadReceipt(transaction.id, 'pdf');
    } catch (error) {
      console.error('Failed to download receipt:', error);
      alert('Failed to download receipt');
    }
  };

  const handleShare = async () => {
    const shareData = {
      title: 'Transaction Receipt',
      text: `Transaction ${transaction.reference}\nAmount: ${transaction.formatted_amount}\nStatus: ${transaction.status_display}`,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(shareData.text);
        alert('Transaction details copied to clipboard!');
      }
    } catch (error) {
      console.error('Share failed:', error);
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
        <div className="relative bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-3xl max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">Transaction Details</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            {/* Status Banner */}
            <div className={`p-4 rounded-xl border ${config.bg} ${config.border}`}>
              <div className="flex items-center gap-3">
                <StatusIcon className={`w-6 h-6 ${config.iconColor}`} />
                <div>
                  <p className={`text-sm font-semibold ${config.text}`}>
                    {transaction.status_display}
                  </p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {new Date(transaction.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Amount */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 text-center">
              <p className="text-sm text-gray-600 mb-1">
                {isDebit ? 'Amount Sent' : 'Amount Received'}
              </p>
              <p className={`text-4xl font-bold ${
                isDebit ? 'text-red-600' : 'text-green-600'
              }`}>
                {isDebit ? '-' : '+'}{transaction.formatted_amount}
              </p>
            </div>

            {/* Transaction Info */}
            <div className="space-y-4">
              {/* Reference */}
              <div>
                <p className="text-xs text-gray-500 mb-1">Transaction Reference</p>
                <div className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                  <p className="text-sm font-mono font-medium text-gray-900">
                    {transaction.reference}
                  </p>
                  <button
                    onClick={handleCopyReference}
                    className="p-1.5 hover:bg-gray-200 rounded transition"
                  >
                    {copied ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-600" />
                    )}
                  </button>
                </div>
              </div>

              {/* Type */}
              <div>
                <p className="text-xs text-gray-500 mb-1">Transaction Type</p>
                <p className="text-sm font-medium text-gray-900">
                  {transaction.type_display}
                </p>
              </div>

              {/* Sender (show account number) */}
              {transaction.user_account && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">From</p>
                  <div className="bg-gray-50 rounded-lg px-3 py-2">
                    <p className="text-sm font-semibold text-gray-900">
                      {transaction.user_name}
                    </p>
                    <p className="text-xs text-gray-600 font-mono">
                      {transaction.user_account}
                    </p>
                  </div>
                </div>
              )}

              {/* Recipient (show account number) */}
              {transaction.recipient_account && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">To</p>
                  <div className="bg-gray-50 rounded-lg px-3 py-2">
                    <p className="text-sm font-semibold text-gray-900">
                      {transaction.recipient_name}
                    </p>
                    <p className="text-xs text-gray-600 font-mono">
                      {transaction.recipient_account}
                    </p>
                  </div>
                </div>
              )}

              {/* Description */}
              {transaction.description && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Description</p>
                  <p className="text-sm text-gray-900">
                    {transaction.description}
                  </p>
                </div>
              )}

              {/* Ledger Entries */}
              {transaction.ledger_entries && transaction.ledger_entries.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-2">Ledger Entries</p>
                  <div className="space-y-2">
                    {transaction.ledger_entries.map((entry) => (
                      <div key={entry.id} className="bg-gray-50 rounded-lg px-3 py-2 text-xs">
                        <div className="flex justify-between mb-1">
                          <span className="font-medium text-gray-700">
                            {entry.entry_type}
                          </span>
                          <span className="font-mono">
                            {entry.wallet_account_number}
                          </span>
                        </div>
                        <div className="flex justify-between text-gray-600">
                          <span>Amount:</span>
                          <span className="font-mono">₦{parseFloat(entry.amount).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-gray-600">
                          <span>Balance After:</span>
                          <span className="font-mono">₦{parseFloat(entry.balance_after).toLocaleString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 space-y-3">
            {transaction.status === 'COMPLETED' && (
              <button
                onClick={handleDownloadReceipt}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition flex items-center justify-center gap-2"
              >
                <Download className="w-5 h-5" />
                Download Receipt
              </button>
            )}

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleShare}
                className="py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition flex items-center justify-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>

              <button
                onClick={onClose}
                className="py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionDetailModal;