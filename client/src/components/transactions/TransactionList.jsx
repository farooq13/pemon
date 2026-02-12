import TransactionItem from './TransactionItem';

/*
 * Displays list of transactions with loading skeleton.
 */
const TransactionList = ({ transactions, loading, onTransactionClick, currentUserEmail }) => {
  // Loading Skeleton
  if (loading) {
    return (
      <div className="bg-white divide-y divide-gray-200">
        {[...Array(5)].map((_, index) => (
          <div key={index} className="px-4 py-4 animate-pulse">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                <div className="flex gap-2">
                  <div className="h-5 bg-gray-200 rounded w-16"></div>
                  <div className="h-5 bg-gray-200 rounded w-24"></div>
                </div>
              </div>
              <div className="flex-shrink-0">
                <div className="h-5 bg-gray-200 rounded w-20"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty State
  if (!transactions || transactions.length === 0) {
    return (
      <div className="bg-white">
        <div className="px-4 py-16 text-center">
          <svg
            className="mx-auto w-24 h-24 text-gray-300 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            No transactions found
          </h3>
          <p className="text-gray-600 text-sm">
            Your transactions will appear here
          </p>
        </div>
      </div>
    );
  }

  // Transaction List
  return (
    <div className="bg-white divide-y divide-gray-200">
      {transactions.map((transaction) => (
        <TransactionItem
          key={transaction.id}
          transaction={transaction}
          onClick={onTransactionClick}
          currentUserEmail={currentUserEmail}
        />
      ))}
    </div>
  );
};

export default TransactionList;