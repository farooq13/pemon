import { useState, useEffect } from 'react';
import { User, AlertCircle, CheckCircle, Search } from 'lucide-react';
import transferService from '../../services/transferService';
import walletService from '../../services/walletService';


const TransferForm = ({ onTransferInitiated, walletBalance }) => {
  const [recipientAccount, setRecipientAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');

  const [validating, setValidating] = useState(false);
  const [recipientInfo, setRecipientInfo] = useState(null);
  const [validationError, setValidationError] = useState('');
  const [formErrors, setFormErrors] = useState({});

  const quickAmounts = [100, 500, 1000, 2000, 5000];

  // Validate recipient account number (debounced)
  useEffect(() => {
    const accountNumber = recipientAccount.trim();
    
    // Reset validation state if input is cleared
    if (!accountNumber) {
      setRecipientInfo(null);
      setValidationError('');
      return;
    }

    // Only validate if it looks like an account number (10-12 digits)
    if (!/^\d{10,12}$/.test(accountNumber)) {
      setRecipientInfo(null);
      setValidationError('');
      return;
    }

    const timeoutId = setTimeout(() => {
      validateRecipient(accountNumber);
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [recipientAccount]);

  const validateRecipient = async (accountNumber) => {
    setValidating(true);
    setValidationError('');
    setRecipientInfo(null);

    try {
      const response = await transferService.validateRecipient(accountNumber);
      
      if (response.valid) {
        setRecipientInfo(response.recipient);
        setValidationError('');
        setFormErrors(prev => ({ ...prev, recipient_account: '' }));
      } else {
        setValidationError('Account number not found');
        setRecipientInfo(null);
      }
    } catch (error) {
      console.error('Validation error:', error);
      setValidationError('Unable to verify account number');
      setRecipientInfo(null);
    } finally {
      setValidating(false);
    }
  };

  const handleAccountNumberChange = (e) => {
    const value = e.target.value;
    // Only allow digits
    const cleaned = value.replace(/\D/g, '');
    
    // Limit to 12 digits
    if (cleaned.length <= 12) {
      setRecipientAccount(cleaned);
      setFormErrors(prev => ({ ...prev, recipient_account: '' }));
    }
  };

  const handleAmountChange = (e) => {
    setAmount(e.target.value);
    setFormErrors(prev => ({ ...prev, amount: '' }));
  };

  const handleQuickAmount = (quickAmount) => {
    setAmount(quickAmount.toString());
    setFormErrors(prev => ({ ...prev, amount: '' }));
  };

  const handleDescriptionChange = (e) => {
    setDescription(e.target.value);
    setFormErrors(prev => ({ ...prev, description: '' }));
  };

  const validateForm = () => {
    const errors = {};

    // Account number validation
    if (!recipientAccount) {
      errors.recipient_account = 'Account number is required';
    } else if (!/^\d{10,12}$/.test(recipientAccount)) {
      errors.recipient_account = 'Account number must be 10 digits';
    } else if (!recipientInfo) {
      errors.recipient_account = 'Please wait for account verification';
    }

    // Amount validation
    const amountNum = parseFloat(amount);
    if (!amount) {
      errors.amount = 'Amount is required';
    } else if (isNaN(amountNum) || amountNum <= 0) {
      errors.amount = 'Invalid amount';
    } else if (amountNum < 10) {
      errors.amount = 'Minimum transfer amount is ₦10';
    } else if (walletBalance && amountNum > parseFloat(walletBalance)) {
      errors.amount = 'Insufficient balance';
    }

    // Description validation
    if (description && description.length > 500) {
      errors.description = 'Description too long (max 500 characters)';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    onTransferInitiated({
      recipient_identifier: recipientInfo.email, // Backend needs email
      amount: amount,
      description: description,
      recipient_info: recipientInfo,
      account_number: recipientAccount
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Account Number Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Recipient Account Number
        </label>

        <div className="relative">
          <input
            type="text"
            inputMode="numeric"
            value={recipientAccount}
            onChange={handleAccountNumberChange}
            placeholder="Enter account number"
            className={`
              w-full px-4 py-3 pl-11 rounded-lg border text-base
              ${formErrors.recipient_account
                ? 'border-red-500 focus:ring-red-500'
                : recipientInfo
                  ? 'border-green-500 focus:ring-green-500'
                  : 'border-gray-300 focus:ring-blue-500'
              }
              focus:outline-none focus:ring-2
            `}
          />

          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />

          {validating && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            </div>
          )}

          {!validating && recipientInfo && (
            <CheckCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-green-600" />
          )}

          {!validating && validationError && (
            <AlertCircle className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-red-600" />
          )}
        </div>

        {formErrors.recipient_account && (
          <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
            <AlertCircle className="w-4 h-4" />
            {formErrors.recipient_account}
          </p>
        )}

        {validationError && !formErrors.recipient_account && (
          <p className="mt-1.5 text-sm text-red-600">
            {validationError}
          </p>
        )}

        {/* Recipient Info Card */}
        {recipientInfo && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-green-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-green-900">
                  {recipientInfo.first_name} {recipientInfo.last_name}
                </p>
                <p className="text-xs text-green-700 truncate">
                  {recipientInfo.accountNumber}
                </p>
              </div>
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            </div>
          </div>
        )}

        <p className="mt-1.5 text-xs text-gray-500">
          Enter the recipient's account number
        </p>
      </div>

      {/* Amount Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Amount
        </label>

        <div className="relative">
          <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 font-medium">
            ₦
          </span>
          <input
            type="number"
            inputMode="decimal"
            value={amount}
            onChange={handleAmountChange}
            placeholder="0.00"
            min="10"
            step="0.01"
            className={`
              w-full px-4 py-3 pl-9 rounded-lg border text-base font-medium
              ${formErrors.amount
                ? 'border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:ring-blue-500'
              }
              focus:outline-none focus:ring-2
            `}
          />
        </div>

        {formErrors.amount && (
          <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
            <AlertCircle className="w-4 h-4" />
            {formErrors.amount}
          </p>
        )}

        {/* Quick Amount Buttons */}
        <div className="mt-3 flex flex-wrap gap-2">
          {quickAmounts.map((quickAmt) => (
            <button
              key={quickAmt}
              type="button"
              onClick={() => handleQuickAmount(quickAmt)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${amount === quickAmt.toString()
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                }
              `}
            >
              ₦{quickAmt.toLocaleString()}
            </button>
          ))}
        </div>

        {walletBalance && (
          <p className="mt-2 text-xs text-gray-600">
            Available balance: {walletService.formatCurrency(walletBalance)}
          </p>
        )}
      </div>

      {/* Description Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description (Optional)
        </label>

        <textarea
          value={description}
          onChange={handleDescriptionChange}
          placeholder="What's this payment for?"
          rows={3}
          maxLength={500}
          className={`
            w-full px-4 py-3 rounded-lg border text-base resize-none
            ${formErrors.description
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:ring-blue-500'
            }
            focus:outline-none focus:ring-2
          `}
        />

        <div className="flex items-center justify-between mt-1.5">
          {formErrors.description ? (
            <p className="text-sm text-red-600 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              {formErrors.description}
            </p>
          ) : (
            <p className="text-xs text-gray-500">
              Add a note for this transfer
            </p>
          )}
          <span className="text-xs text-gray-400">
            {description.length}/500
          </span>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={validating || !recipientInfo}
        className={`
          w-full py-4 rounded-lg font-semibold text-white text-base transition-all
          ${validating || !recipientInfo
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:scale-[0.98]'
          }
        `}
      >
        {validating ? 'Verifying...' : 'Continue'}
      </button>
    </form>
  );
};

export default TransferForm;