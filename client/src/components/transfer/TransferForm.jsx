import { useState, useEffect } from 'react';
import { Search, X, Clock, User } from 'lucide-react';
import transferService from '../../services/transferService';


const TransferForm = ({ walletData, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    recipient_identifier: '',
    amount: '',
    description: ''
  });

  const [recipientDetails, setRecipientDetails] = useState(null);
  const [recentRecipients, setRecentRecipients] = useState([]);
  const [showRecipientList, setShowRecipientList] = useState(false);
  const [validatingRecipient, setValidatingRecipient] = useState(false);
  const [errors, setErrors] = useState({});

  // Load recent recipients on mount
  useEffect(() => {
    loadRecentRecipients();
  }, []);

  const loadRecentRecipients = async () => {
    try {
      const recipients = await transferService.getRecentRecipients();
      setRecentRecipients(recipients);
    } catch (error) {
      console.error('Failed to load recent recipients:', error);
    }
  };

  const validateRecipient = async (identifier) => {
    if (!identifier || identifier.length < 3) {
      setRecipientDetails(null);
      return;
    }

    setValidatingRecipient(true);
    setErrors({ ...errors, recipient_identifier: null });

    try {
      const result = await transferService.validateRecipient(identifier);
      
      if (result.valid) {
        setRecipientDetails(result.data);
        setErrors({ ...errors, recipient_identifier: null });
      }
    } catch (error) {
      setRecipientDetails(null);
      setErrors({
        ...errors,
        recipient_identifier: error.response?.data?.message || 'Recipient not found'
      });
    } finally {
      setValidatingRecipient(false);
    }
  };

  const handleRecipientChange = (value) => {
    setFormData({ ...formData, recipient_identifier: value });
    setRecipientDetails(null);
    
    // Debounced validation
    if (value.length >= 3) {
      const timer = setTimeout(() => validateRecipient(value), 500);
      return () => clearTimeout(timer);
    }
  };

  const selectRecipient = (recipient) => {
    setFormData({
      ...formData,
      recipient_identifier: recipient.email,
      amount: formData.amount || recipient.last_transfer_amount || ''
    });
    setRecipientDetails({
      email: recipient.email,
      name: recipient.name,
      phone_number: recipient.phone_number
    });
    setShowRecipientList(false);
  };

  const handleAmountChange = (value) => {
    // Remove non-numeric characters except decimal point
    const cleaned = value.replace(/[^0-9.]/g, '');
    setFormData({ ...formData, amount: cleaned });
    setErrors({ ...errors, amount: null });
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.recipient_identifier) {
      newErrors.recipient_identifier = 'Recipient is required';
    }

    if (!recipientDetails) {
      newErrors.recipient_identifier = 'Please select a valid recipient';
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    }

    const amount = parseFloat(formData.amount);
    if (amount < 10) {
      newErrors.amount = 'Minimum transfer amount is ₦10.00';
    }

    if (walletData && amount > parseFloat(walletData.balance)) {
      newErrors.amount = `Insufficient balance (Available: ${transferService.formatAmount(walletData.balance)})`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Recipient Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Recipient
        </label>
        
        <div className="relative">
          <div className="relative">
            <input
              type="text"
              value={formData.recipient_identifier}
              onChange={(e) => handleRecipientChange(e.target.value)}
              onFocus={() => setShowRecipientList(true)}
              placeholder="Enter email or phone number"
              className={`
                w-full px-4 py-3 pl-11 pr-11 rounded-lg border
                ${errors.recipient_identifier 
                  ? 'border-red-500 focus:ring-red-500' 
                  : 'border-gray-300 focus:ring-blue-500'
                }
                focus:outline-none focus:ring-2
                text-base
              `}
            />
            
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            
            {formData.recipient_identifier && (
              <button
                type="button"
                onClick={() => {
                  setFormData({ ...formData, recipient_identifier: '' });
                  setRecipientDetails(null);
                }}
                className="absolute right-3 top-1/2 transform -translate-y-1/2"
              >
                <X className="w-5 h-5 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>

          {validatingRecipient && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>

        {/* Validation Error */}
        {errors.recipient_identifier && (
          <p className="mt-1 text-sm text-red-600">{errors.recipient_identifier}</p>
        )}

        {/* Recipient Confirmed */}
        {recipientDetails && !errors.recipient_identifier && (
          <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <User className="w-5 h-5 text-green-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {recipientDetails.name}
              </p>
              <p className="text-xs text-gray-600 truncate">{recipientDetails.email}</p>
            </div>
            <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
        )}

        {/* Recent Recipients Dropdown */}
        {showRecipientList && recentRecipients.length > 0 && !recipientDetails && (
          <div className="absolute z-10 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 max-h-60 overflow-y-auto">
            <div className="p-2">
              <p className="text-xs font-medium text-gray-500 px-3 py-2">Recent Recipients</p>
              {recentRecipients.map((recipient) => (
                <button
                  key={recipient.id}
                  type="button"
                  onClick={() => selectRecipient(recipient)}
                  className="w-full px-3 py-2 hover:bg-gray-50 rounded-lg flex items-center gap-3 text-left transition"
                >
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{recipient.name}</p>
                    <p className="text-xs text-gray-500 truncate">{recipient.email}</p>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{transferService.formatAmount(recipient.last_transfer_amount)}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Amount Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Amount
        </label>
        
        <div className="relative">
          <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 text-lg font-medium">
            ₦
          </span>
          <input
            type="text"
            inputMode="decimal"
            value={formData.amount}
            onChange={(e) => handleAmountChange(e.target.value)}
            placeholder="0.00"
            className={`
              w-full px-4 py-3 pl-9 rounded-lg border text-lg font-medium
              ${errors.amount 
                ? 'border-red-500 focus:ring-red-500' 
                : 'border-gray-300 focus:ring-blue-500'
              }
              focus:outline-none focus:ring-2
            `}
          />
        </div>

        {errors.amount && (
          <p className="mt-1 text-sm text-red-600">{errors.amount}</p>
        )}

        {/* Available Balance */}
        {walletData && (
          <p className="mt-1 text-sm text-gray-600">
            Available: {transferService.formatAmount(walletData.balance)}
          </p>
        )}

        {/* Quick Amount Buttons - Mobile Optimized */}
        <div className="grid grid-cols-3 gap-2 mt-3">
          {['100', '500', '1000'].map((amount) => (
            <button
              key={amount}
              type="button"
              onClick={() => handleAmountChange(amount)}
              className="px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition"
            >
              ₦{amount}
            </button>
          ))}
        </div>
      </div>

      {/* Description (Optional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description <span className="text-gray-400 text-xs">(Optional)</span>
        </label>
        
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="What's this for?"
          rows="3"
          maxLength="500"
          className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
        
        <p className="mt-1 text-xs text-gray-500 text-right">
          {formData.description.length}/500
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || !recipientDetails}
        className={`
          w-full py-4 rounded-lg font-semibold text-white text-lg
          transition-all duration-200
          ${loading || !recipientDetails
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
          }
        `}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            Processing...
          </span>
        ) : (
          'Continue'
        )}
      </button>
    </form>
  );
};

export default TransferForm; 