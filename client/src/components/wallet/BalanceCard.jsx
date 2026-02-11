import { useState } from 'react';
import walletService from '../../services/walletService';


const BalanceCard = ({ walletData, loading, onRefresh }) => {
  const [showBalance, setShowBalance] = useState(true);

  /*
   * Toggle balance visibility
   */
  const toggleBalanceVisibility = () => {
    setShowBalance(!showBalance);
  };

  /*
    Copy virtual account number to clipboard
   */
  const copyAccountNumber = () => {
    if (walletData?.virtual_account_number) {
      navigator.clipboard.writeText(walletData.virtual_account_number);
      // You can add a toast notification here
      alert('Account number copied!');
    }
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-6 animate-pulse">
        <div className="h-6 bg-blue-500 rounded w-1/3 mb-4"></div>
        <div className="h-12 bg-blue-500 rounded w-2/3 mb-6"></div>
        <div className="h-4 bg-blue-500 rounded w-1/2"></div>
      </div>
    );
  }

  if (!walletData) {
    return (
      <div className="bg-gradient-to-r from-gray-600 to-gray-700 rounded-2xl shadow-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white text-lg font-semibold">Wallet</h3>
        </div>
        <p className="text-white text-center py-8">
          No wallet found. Please complete KYC verification.
        </p>
      </div>
    );
  }

  const isActive = walletService.isWalletActive(walletData);

  return (
    <div className={`rounded-2xl shadow-xl p-6 ${
      isActive 
        ? 'bg-gradient-to-r from-blue-600 to-blue-700' 
        : 'bg-gradient-to-r from-red-600 to-red-700'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-lg font-semibold">Wallet Balance</h3>
        <button
          onClick={onRefresh}
          className="text-white hover:cursor-pointer hover:scale-115 p-2 rounded-lg transition"
          title="Refresh balance"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Status Badge */}
      {!isActive && (
        <div className="bg-white bg-opacity-20 rounded-lg px-3 py-2 mb-4">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <p className="text-white text-sm font-medium">
              {walletService.getStatusMessage(walletData)}
            </p>
          </div>
        </div>
      )}

      {/* Balance Display */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <p className="text-white text-opacity-90 text-sm mb-1">Available Balance</p>
            <div className="flex items-center gap-3">
              <p className="text-white text-4xl font-bold">
                {showBalance 
                  ? walletData.formatted_balance || walletService.formatCurrency(walletData.balance)
                  : '********'
                }
              </p>
              <button
                onClick={toggleBalanceVisibility}
                className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition"
                title={showBalance ? 'Hide balance' : 'Show balance'}
              >
                {showBalance ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Virtual Account Number */}
      <div className=" bg-opacity-10 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-white text-opacity-80 text-xs mb-1">Account Number</p>
            <p className="text-white text-lg font-mono font-semibold">
              {walletData.virtual_account_number || 'N/A'}
            </p>
          </div>
          <button
            onClick={copyAccountNumber}
            className="text-white hover:scale-115 hover:cursor-pointer hover:bg-opacity-20 p-2 rounded-lg transition"
            title="Copy account number"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
      </div>

      {/* User Info (Optional) */}
      {walletData.user_name && (
        <div className="mt-4 pt-4 border-t border-white border-opacity-20">
          <p className="text-white text-opacity-80 text-sm">
            {walletData.user_name}
          </p>
          <p className="text-white text-opacity-60 text-xs">
            {walletData.user_email}
          </p>
        </div>
      )}
    </div>
  );
};

export default BalanceCard;