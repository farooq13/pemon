import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';

/**
 * TransactionItem Component - FIXED
 * 
 * Now correctly passes transaction object (not event) to onClick
 */
const TransactionItem = ({ transaction, onClick, currentUserEmail }) => {
  const isDebit = transaction.is_debit;
  
  // Get display name and account
  const displayName = transaction.counterparty_name || 'Unknown';
  const displayAccount = transaction.counterparty_account || 'N/A';

  // Status color
  const statusColors = {
    COMPLETED: 'bg-green-100 text-green-800',
    PENDING: 'bg-yellow-100 text-yellow-800',
    FAILED: 'bg-red-100 text-red-800',
    PROCESSING: 'bg-blue-100 text-blue-800',
  };

  // FIXED: Pass transaction to onClick, not event
  const handleClick = () => {
    console.log('TransactionItem clicked, calling onClick with:', transaction);
    onClick(transaction);  // Pass the transaction object!
  };

  return (
    <button
      onClick={handleClick}  // Call our handler instead of onClick directly
      className="w-full px-4 py-3.5 hover:bg-gray-50 hover:cursor-pointer active:bg-gray-100 transition-colors text-left"
    >
      <div className="flex items-center gap-3">
        {/* Icon */}
        <div className={`
          w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0
          ${isDebit ? 'bg-red-50' : 'bg-green-50'}
        `}>
          {isDebit ? (
            <ArrowUpRight className="w-5 h-5 text-red-600" strokeWidth={2.5} />
          ) : (
            <ArrowDownLeft className="w-5 h-5 text-green-600" strokeWidth={2.5} />
          )}
        </div>

        {/* Details */}
        <div className="flex-1 min-w-0">
          {/* Top row: Name and Amount */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {displayName}
              </p>
              <p className="text-xs text-gray-500 font-mono">
                {displayAccount}
              </p>
            </div>
            
            <p className={`text-sm font-bold flex-shrink-0 ${
              isDebit ? 'text-red-600' : 'text-green-600'
            }`}>
              {isDebit ? '-' : '+'}{transaction.formatted_amount}
            </p>
          </div>

          {/* Bottom row: Description/Type and Status */}
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-gray-600 truncate">
              {transaction.description || transaction.type_display}
            </p>
            
            <span className={`
              text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0
              ${statusColors[transaction.status] || 'bg-gray-100 text-gray-800'}
            `}>
              {transaction.status_display}
            </span>
          </div>

          {/* Date */}
          <p className="text-xs text-gray-400 mt-1">
            {new Date(transaction.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </p>
        </div>
      </div>
    </button>
  );
};

export default TransactionItem;