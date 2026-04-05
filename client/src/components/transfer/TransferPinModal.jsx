import React, { useState } from 'react';
import { KeyRound, X, AlertCircle } from 'lucide-react';

const TransferPinModal = ({ isOpen, onClose, onConfirm, hasPin, loading }) => {
  const [pin, setPin] = useState('');
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-blue-600" />
            Transfer Authorization
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded-full transition">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        <div className="p-6">
          {!hasPin ? (
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Transfer PIN Required</p>
                <p className="text-sm text-gray-500 mt-1">You must set up a Transfer PIN in Settings before making a transaction.</p>
              </div>
              <button
                onClick={() => window.location.href = '/settings'}
                className="w-full py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 mt-4"
              >
                Go to Settings
              </button>
            </div>
          ) : (
            <form onSubmit={(e) => { e.preventDefault(); onConfirm(pin); }} className="space-y-4">
              <div className="text-center space-y-2 mb-6">
                <p className="text-sm text-gray-600">Please enter your 4-digit Transfer PIN to authorize this transaction.</p>
              </div>
              
              <div>
                <input
                  type="password"
                  maxLength={4}
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\\D/g, ''))}
                  placeholder="PIN"
                  autoFocus
                  className="w-full text-center tracking-[1em] text-2xl px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
              
              <button
                type="submit"
                disabled={pin.length !== 4 || loading}
                className={`w-full py-3 rounded-lg font-semibold text-white transition
                  ${(pin.length !== 4 || loading) ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}
                `}
              >
                {loading ? 'Processing...' : 'Authorize Transfer'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransferPinModal;
