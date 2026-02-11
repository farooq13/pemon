import { ArrowUpRight, ArrowDownLeft, Clock } from 'lucide-react';
import transactionService from '../../services/transactionService';


const TransactionItem = ({ transaction, onClick, currentUserEmail }) => {
  const isDebit = transaction.is_debit || transaction.user_email === currentUserEmail;
  const statusColors = transactionService.getStatusColor(transaction.status);

  return (
    <div
      onClick={() => onClick(transaction)}
      className="bg-white border-b border-gray-200 hover:bg-gray-50 active:bg-gray-100 cursor-pointer transition-colors"
    >
      <div className="px-4 py-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className={`
            flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
            ${isDebit ? 'bg-red-100' : 'bg-green-100'}
          `}>
            {isDebit ? (
              <ArrowUpRight className="w-5 h-5 text-red-600" />
            ) : (
              <ArrowDownLeft className="w-5 h-5 text-green-600" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Type & Recipient/Sender */}
            <div className="flex items-start justify-between gap-2 mb-1">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {transactionService.getTypeLabel(transaction.transaction_type)}
                </p>
                
                {transaction.recipient_email && isDebit && (
                  <p className="text-xs text-gray-600 truncate">
                    To: {transaction.recipient_email}
                  </p>
                )}
                
                {transaction.user_email && !isDebit && (
                  <p className="text-xs text-gray-600 truncate">
                    From: {transaction.user_email}
                  </p>
                )}
              </div>

              {/* Amount */}
              <div className="flex-shrink-0 text-right">
                <p className={`text-sm font-bold ${
                  isDebit ? 'text-red-600' : 'text-green-600'
                }`}>
                  {isDebit ? '-' : '+'}{transaction.formatted_amount || transactionService.formatCurrency(transaction.amount)}
                </p>
              </div>
            </div>

            {/* Description (if exists) */}
            {transaction.description && (
              <p className="text-xs text-gray-500 truncate mb-1">
                {transaction.description}
              </p>
            )}

            {/* Status & Date */}
            <div className="flex items-center justify-between gap-2 mt-2">
              {/* Status Badge */}
              <span className={`
                inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                ${statusColors.bg} ${statusColors.text}
              `}>
                {transaction.status_display || transaction.status}
              </span>

              {/* Date & Time */}
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                <span>{new Date(transaction.created_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionItem;