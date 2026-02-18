import { useRef } from 'react';
import { X, Download, Share2 } from 'lucide-react';
import html2canvas from 'html2canvas';

const TransactionReceipt = ({ transaction, onClose }) => {
  const receiptRef = useRef(null);

  if (!transaction) return null;

  const isSuccess = transaction.status === 'COMPLETED';

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const maskAccount = (account) => {
    if (!account || account.length < 4) return account;
    const lastFour = account.slice(-4);
    return `**** **** **** ${lastFour}`;
  };

  const handleShareAsImage = async () => {
    try {
      const canvas = await html2canvas(receiptRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      link.download = `receipt-${transaction.reference}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center p-4">
      
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold text-gray-900">
            Transaction Receipt
          </h2>
          <button onClick={onClose}>
            <X className="w-5 h-5 text-gray-500 hover:text-gray-700" />
          </button>
        </div>

        {/* Receipt Content */}
        <div ref={receiptRef} className="p-6">

          {/* Logo */}
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-blue-600">Pemon</h1>
            <p className="text-sm text-gray-500">
              Seamless & Secure Payments
            </p>
          </div>

          {/* Amount */}
          <div className="text-center mb-6">
            <p className={`text-4xl font-bold ${
              isSuccess ? 'text-green-600' : 'text-red-600'
            }`}>
              {transaction.formatted_amount}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {transaction.status_display}
            </p>
            <p className="text-xs text-gray-400 mt-2">
              {formatDate(transaction.created_at)}
            </p>
          </div>

          {/* Divider */}
          <div className="border-t my-4"></div>

          {/* Recipient */}
          <div className="mb-4">
            <p className="text-xs text-gray-500 uppercase mb-1">
              Recipient
            </p>
            <p className="font-semibold text-gray-900">
              {transaction?.recipient_name || 'N/A'}
            </p>
            <p className="text-sm text-gray-600">
              {maskAccount(transaction?.recipient_account)}
            </p>
          </div>

          {/* Sender */}
          <div className="mb-4">
            <p className="text-xs text-gray-500 uppercase mb-1">
              Sender
            </p>
            <p className="font-semibold text-gray-900">
              {transaction?.user_name || 'N/A'}
            </p>
            <p className="text-sm text-gray-600">
              {maskAccount(transaction?.user_account)}
            </p>
          </div>

          {/* Divider */}
          <div className="border-t my-4"></div>

          {/* Meta Info */}
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Reference</span>
              <span className="font-medium text-gray-900">
                {transaction.reference}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-500">Transaction ID</span>
              <span className="font-medium text-gray-900">
                {transaction.id}
              </span>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 pt-4 border-t text-center text-xs text-gray-400">
            Thank you for using Pemon.
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-4 p-4 border-t bg-gray-50">
          <button
            onClick={handleShareAsImage}
            className="flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
          >
            <Share2 className="w-4 h-4" />
            Share
          </button>

          <button
            onClick={handleShareAsImage}
            className="flex items-center justify-center gap-2 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-lg transition"
          >
            <Download className="w-4 h-4" />
            Download
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionReceipt;
