import { X, AlertCircle } from 'lucide-react';

const ConfirmationModal = ({ isOpen, transferData, onConfirm, onClose, loading }) => {
  if (!isOpen || !transferData) {
    return null;
  }

  const { recipient_info, amount, description, account_number } = transferData;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={loading ? undefined : onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden z-10">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-600 px-6 py-4 text-white">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">Confirm Transfer</h2>
              {!loading && (
                <button
                  onClick={onClose}
                  className="p-1 hover:bg-white/20 hover:cursor-pointer rounded-full transition"
                >
                  <X className="w-6 h-6" />
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Warning */}
            <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-900">
                  Please review the details carefully
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  This action cannot be undone
                </p>
              </div>
            </div>

            {/* Amount */}
            <div className="text-center py-4">
              <p className="text-sm text-gray-600 mb-1">You're sending</p>
              <p className="text-4xl font-bold text-gray-900">
                ₦{parseFloat(amount).toLocaleString('en-NG', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </p>
            </div>

            {/* Recipient Details */}
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-500 mb-1">To</p>
                <p className="text-base font-semibold text-gray-900">
                  {recipient_info.first_name} {recipient_info.last_name}
                </p>
                <p className="text-sm text-gray-600">{recipient_info.email}</p>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">Account Number</p>
                <p className="text-base font-mono font-medium text-gray-900">
                  {account_number}
                </p>
              </div>

              {description && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Description</p>
                  <p className="text-sm text-gray-700">{description}</p>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="bg-gray-50 px-6 py-4 flex gap-3">
            <button
              onClick={onClose}
              disabled={loading}
              className={`
                flex-1 py-3 rounded-lg font-semibold transition hover:cursor-pointer
                ${loading
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              Cancel
            </button>

            <button
              onClick={onConfirm}
              disabled={loading}
              className={`
                flex-1 py-3 rounded-lg font-semibold text-white transition hover:cursor-pointer
                ${loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
                }
              `}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Processing...
                </span>
              ) : (
                'Confirm & Send'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;