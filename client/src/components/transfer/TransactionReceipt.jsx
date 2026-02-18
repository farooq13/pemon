import { useRef } from 'react';
import { X, Download, Share2 } from 'lucide-react';
import html2canvas from 'html2canvas';


const TransactionReceipt = ({ transaction, onClose }) => {
  const receiptRef = useRef(null);

  if (!transaction) return null;

  const isSuccess = transaction.status === 'COMPLETED';

  const handleShareAsImage = async () => {
    try {
      const element = receiptRef.current;
      const canvas = await html2canvas(element, {
        backgroundColor: '#1a1a1a',
        scale: 2, // Higher quality
      });

      canvas.toBlob(async (blob) => {
        const file = new File([blob], `receipt-${transaction.reference}.png`, {
          type: 'image/png',
        });

        if (navigator.share && navigator.canShare({ files: [file] })) {
          await navigator.share({
            files: [file],
            title: 'Transaction Receipt',
            text: `Receipt for ${transaction.reference}`,
          });
        } else {
          // Fallback: Download
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `receipt-${transaction.reference}.png`;
          a.click();
          URL.revokeObjectURL(url);
        }
      });
    } catch (error) {
      console.error('Failed to share as image:', error);
      alert('Failed to share receipt');
    }
  };

  const handleShareAsPDF = async () => {
    try {
      // You can implement PDF download using the backend endpoint
      alert('PDF download coming soon!');
    } catch (error) {
      console.error('Failed to share as PDF:', error);
    }
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  // Mask account number (show last 4 digits)
  const maskAccount = (account) => {
    if (!account || account.length < 4) return account;
    const lastFour = account.slice(-4);
    const stars = '*'.repeat(account.length - 4);
    return `${stars}${lastFour}`;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-black border-b border-gray-800 px-4 py-4">
        <div className="flex items-center justify-between max-w-md mx-auto">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-900 rounded-full transition"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
          <h1 className="text-lg font-semibold text-white">Share Receipt</h1>
          <div className="w-10"></div>
        </div>
      </div>

      {/* Receipt */}
      <div className="flex items-center justify-center min-h-[calc(100vh-180px)] p-4">
        <div
          ref={receiptRef}
          className="relative w-full max-w-md bg-[#2a2a2a] rounded-3xl overflow-hidden"
          style={{
            boxShadow: '0 0 60px rgba(0, 255, 200, 0.1)',
          }}
        >
          {/* Watermark Background */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none">
            <div className="absolute inset-0 flex flex-wrap">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="text-6xl font-bold text-white transform rotate-[-30deg] m-8"
                >
                  Pemon
                </div>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="relative z-10 p-8">
            {/* Header */}
            <div className="flex items-start justify-between mb-8">
              {/* Logo */}
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                  <span className="text-white font-bold text-lg">P</span>
                </div>
                <span className="text-2xl font-bold text-white">Pemon</span>
              </div>

              {/* Title */}
              <div className="text-right">
                <p className="text-sm text-gray-400">Transaction Receipt</p>
              </div>
            </div>

            {/* Amount */}
            <div className="text-center mb-8">
              <p className={`text-5xl font-bold mb-2 ${
                isSuccess ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {transaction.formatted_amount}
              </p>
              <p className={`text-lg font-medium ${
                isSuccess ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {transaction.status_display}
              </p>
              <p className="text-sm text-gray-400 mt-2">
                {formatDate(transaction.created_at)}
              </p>
            </div>

            {/* Details */}
            <div className="space-y-6">
              {/* Recipient */}
              <div>
                <p className="text-sm text-gray-400 mb-2">Recipient Details</p>
                <div className="text-right">
                  <p className="text-base font-semibold text-white uppercase tracking-wide">
                    {transaction.recipient_name || transaction.counterparty_name}
                  </p>
                  <p className="text-sm text-gray-300 font-mono">
                    Pemon | {maskAccount(transaction.recipient_account || transaction.counterparty_account)}
                  </p>
                </div>
              </div>

              {/* Sender */}
              <div>
                <p className="text-sm text-gray-400 mb-2">Sender Details</p>
                <div className="text-right">
                  <p className="text-base font-semibold text-white uppercase tracking-wide">
                    {transaction.user_name}
                  </p>
                  <p className="text-sm text-gray-300 font-mono">
                    Pemon | {maskAccount(transaction.user_account)}
                  </p>
                </div>
              </div>

              {/* Transaction Number */}
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-400">Transaction No.</p>
                <p className="text-sm text-gray-200 font-mono">
                  {transaction.reference}
                </p>
              </div>

              {/* Session ID */}
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-400">Session ID</p>
                <p className="text-sm text-gray-200 font-mono">
                  {transaction.id}
                </p>
              </div>
            </div>

            {/* Footer Note */}
            <div className="mt-8 pt-6 border-t border-gray-700">
              <p className="text-xs text-gray-500 leading-relaxed text-center">
                Enjoy seamless transactions with Pemon. Get instant transfers, 
                bill payments, and secure savings. Pemon is licensed and 
                regulated by financial authorities.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="sticky bottom-0 bg-black border-t border-gray-800 px-4 py-4">
        <div className="max-w-md mx-auto grid grid-cols-2 gap-4">
          <button
            onClick={handleShareAsImage}
            className="flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl transition"
          >
            <Share2 className="w-5 h-5" />
            Share as image
          </button>

          <button
            onClick={handleShareAsPDF}
            className="flex items-center justify-center gap-2 py-4 bg-gray-800 hover:bg-gray-700 text-emerald-400 font-semibold rounded-xl transition"
          >
            <Download className="w-5 h-5" />
            Share as PDF
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionReceipt;