import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import TransferForm from '../components/transfer/TransferForm';
import ConfirmationModal from '../components/transfer/ConfirmationModal';
import transferService from '../services/transferService';
import walletService from '../services/walletService';


const Transfer = () => {
  const navigate = useNavigate();

  const [walletData, setWalletData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [transferData, setTransferData] = useState(null);
  const [recipientDetails, setRecipientDetails] = useState(null);
  const [transferResult, setTransferResult] = useState(null);

  useEffect(() => {
    fetchWalletData();
  }, []);

  const fetchWalletData = async () => {
    try {
      const wallet = await walletService.getBalance();
      setWalletData(wallet);
    } catch (error) {
      console.error('Failed to fetch wallet:', error);
    }
  };

  const handleFormSubmit = async (formData) => {
    // Validate recipient one more time
    try {
      const result = await transferService.validateRecipient(
        formData.recipient_identifier
      );

      if (result.valid) {
        setTransferData(formData);
        setRecipientDetails(result.recipient);
        setShowConfirmModal(true);
      }
    } catch (error) {
      alert(error.response?.data?.message || 'Invalid recipient');
    }
  };

  const handleConfirmTransfer = async () => {
    setLoading(true);

    try {
      const result = await transferService.sendMoney(transferData);

      // Success
      setTransferResult({
        success: true,
        data: result.data,
        message: result.message
      });

      // Refresh wallet balance
      fetchWalletData();

      // Close confirmation modal
      setShowConfirmModal(false);
    } catch (error) {
      // Error
      setTransferResult({
        success: false,
        message: error.response?.data?.message || 'Transfer failed. Please try again.',
        errors: error.response?.data?.errors
      });

      setShowConfirmModal(false);
    } finally {
      setLoading(false);
    }
  };

  const handleStartNewTransfer = () => {
    setTransferResult(null);
    setTransferData(null);
    setRecipientDetails(null);
  };

  // Success Screen
  if (transferResult?.success) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 text-gray-700 hover:text-gray-900 hover:cursor-pointer"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Back to Dashboard</span>
            </button>
          </div>
        </header>

        {/* Success Content */}
        <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            {/* Success Icon */}
            <div className="mx-auto w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>

            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Transfer Successful!
            </h1>
            <p className="text-gray-600 mb-6">
              Your money has been sent successfully
            </p>

            {/* Amount */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 mb-6">
              <p className="text-sm text-gray-600 mb-1">Amount Sent</p>
              <p className="text-4xl font-bold text-gray-900">
                {transferResult.data.formatted_amount}
              </p>
            </div>

            {/* Transaction Details */}
            <div className="bg-gray-50 rounded-lg p-4 text-left space-y-3 mb-6">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Recipient</span>
                <span className="text-sm font-medium text-gray-900">
                  {transferResult.data.recipient_name}
                </span>
              </div>

              <div className="border-t border-gray-200"></div>

              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Reference</span>
                <span className="text-sm font-mono text-gray-900">
                  {transferResult.data.reference}
                </span>
              </div>

              <div className="border-t border-gray-200"></div>

              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Date</span>
                <span className="text-sm text-gray-900">
                  {new Date(transferResult.data.created_at).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              <button
                onClick={handleStartNewTransfer}
                className="w-full bg-blue-600 hover:bg-blue-700 hover:cursor-pointer text-white font-semibold py-3 rounded-lg transition"
              >
                Send Again
              </button>

              <button
                onClick={() => navigate('/transactions')}
                className="w-full border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50 hover:cursor-pointer transition"
              >
                View Transaction History
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                className="w-full text-gray-600 font-medium py-2 hover:cursor-pointer"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Error Screen
  if (transferResult && !transferResult.success) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4">
            <button
              onClick={handleStartNewTransfer}
              className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium">Try Again</span>
            </button>
          </div>
        </header>

        {/* Error Content */}
        <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            {/* Error Icon */}
            <div className="mx-auto w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mb-4">
              <XCircle className="w-12 h-12 text-red-600" />
            </div>

            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Transfer Failed
            </h1>
            <p className="text-gray-600 mb-6">
              {transferResult.message}
            </p>

            {/* Actions */}
            <div className="space-y-3">
              <button
                onClick={handleStartNewTransfer}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
              >
                Try Again
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                className="w-full text-gray-600 font-medium py-2"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Transfer Form Screen
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
          >
            <ArrowLeft className="w-5 h-5 hover:cursor-pointer" />
            <span className="font-medium">Send Money</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-6 pb-24">
        {/* Wallet Balance Card */}
        {walletData && (
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-lg p-6 mb-6">
            <p className="text-blue-100 text-sm mb-1">Available Balance</p>
            <p className="text-white text-3xl font-bold">
              {walletService.formatCurrency(walletData.balance)}
            </p>
          </div>
        )}

        {/* Transfer Form */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            Transfer Details
          </h2>

          <TransferForm
            walletBalance={walletData?.balance}
            onTransferInitiated={handleFormSubmit}
          />
        </div>
      </main>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        transferData={transferData}
        recipientDetails={recipientDetails}
        onConfirm={handleConfirmTransfer}
        loading={loading}
      />
    </div>
  );
};

export default Transfer;