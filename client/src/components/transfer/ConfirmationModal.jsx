import { X, User, ArrowRight, AlertCircle } from 'lucide-react';
import transferService from '../../services/transferService';


const ConfirmationModal = ({ 
  isOpen, 
  onClose, 
  transferData, 
  recipientDetails,
  onConfirm,
  loading 
}) => {
  if (!isOpen) return null;

  const amount = parseFloat(transferData.amount);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-end sm:items-center justify-center p-0 sm:p-4">
        <div className="relative bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-2xl shadow-xl transform transition-all">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-2xl">
            <h3 className="text-lg font-bold text-gray-900">Confirm Transfer</h3>
            <button
              onClick={onClose}
              disabled={loading}
              className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-6 space-y-6">
            {/* Warning Banner */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Please verify the details</p>
                <p className="mt-1">This action cannot be undone. Make sure all information is correct.</p>
              </div>
            </div>

            {/* Transfer Flow Visualization */}
            <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl p-6">
              <div className="flex items-center justify-between">
                {/* Sender */}
                <div className="flex-1 text-center">
                  <div className="mx-auto w-16 h-16 rounded-full bg-blue-600 flex items-center justify-center mb-2">
                    <User className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-sm font-medium text-gray-900">You</p>
                </div>

                {/* Arrow */}
                <div className="flex-shrink-0 px-4">
                  <ArrowRight className="w-8 h-8 text-gray-400" />
                </div>

                {/* Recipient */}
                <div className="flex-1 text-center">
                  <div className="mx-auto w-16 h-16 rounded-full bg-green-600 flex items-center justify-center mb-2">
                    <User className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate px-2">
                    {recipientDetails?.name || 'Recipient'}
                  </p>
                </div>
              </div>

              {/* Amount Display */}
              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600 mb-1">Transfer Amount</p>
                <p className="text-4xl font-bold text-gray-900">
                  {transferService.formatAmount(amount)}
                </p>
              </div>
            </div>

            {/* Transfer Details */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-start">
                <span className="text-sm text-gray-600">To</span>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {recipientDetails?.name}
                  </p>
                  <p className="text-xs text-gray-600">{recipientDetails?.email}</p>
                </div>
              </div>

              <div className="border-t border-gray-200"></div>

              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Amount</span>
                <span className="text-sm font-medium text-gray-900">
                  {transferService.formatAmount(amount)}
                </span>
              </div>

              {transferData.description && (
                <>
                  <div className="border-t border-gray-200"></div>
                  <div className="flex justify-between items-start">
                    <span className="text-sm text-gray-600">Description</span>
                    <p className="text-sm text-gray-900 text-right max-w-[200px]">
                      {transferData.description}
                    </p>
                  </div>
                </>
              )}

              <div className="border-t border-gray-200"></div>

              {/* Fee (if applicable) */}
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Fee</span>
                <span className="text-sm font-medium text-green-600">
                  Free
                </span>
              </div>

              <div className="border-t-2 border-gray-300 pt-2"></div>

              {/* Total */}
              <div className="flex justify-between items-center">
                <span className="text-base font-semibold text-gray-900">Total</span>
                <span className="text-lg font-bold text-gray-900">
                  {transferService.formatAmount(amount)}
                </span>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 space-y-3 rounded-b-2xl">
            <button
              onClick={onConfirm}
              disabled={loading}
              className={`
                w-full py-4 rounded-lg font-semibold text-white text-lg
                transition-all duration-200
                ${loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
                }
              `}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Sending...
                </span>
              ) : (
                'Confirm & Send'
              )}
            </button>

            <button
              onClick={onClose}
              disabled={loading}
              className="w-full py-3 text-gray-700 font-medium hover:bg-gray-50 rounded-lg transition disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;