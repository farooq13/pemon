import { useNavigate } from 'react-router-dom';
import { Send, Wallet, ReceiptText, History, Lock, AlertTriangle } from 'lucide-react';


const QuickActions = ({ walletData }) => {
  const navigate = useNavigate();
  const isWalletActive = walletData && !walletData.is_frozen;

  const actions = [
    {
      id: 'send',
      label: 'Send Money',
      icon: Send,
      path: '/transfer',
      color: 'from-blue-500 to-blue-600',
      disabled: !isWalletActive,
    },
    {
      id: 'receive',
      label: 'Receive',
      icon: Wallet,
      path: '/receive',
      color: 'from-green-500 to-green-600',
      disabled: false,
    },
    {
      id: 'bills',
      label: 'Pay Bills',
      icon: ReceiptText,
      path: '/bills',
      color: 'from-purple-500 to-purple-600',
      disabled: !isWalletActive,
    },
    {
      id: 'history',
      label: 'History',
      icon: History,
      path: '/transactions',
      color: 'from-orange-500 to-orange-600',
      disabled: false,
    },
  ];

  const handleClick = (action) => {
    if (action.disabled) {
      alert('Your wallet is frozen. Contact support.');
      return;
    }
    navigate(action.path);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {actions.map((action) => {
          
          const IconComponent = action.icon;
          
          return (
            <button
              key={action.id}
              onClick={() => handleClick(action)}
              disabled={action.disabled}
              className={`
                relative p-2 rounded-full 
                ${action.color}
                transition-all duration-200
                ${action.disabled 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'hover:cursor-pointer hover:scale-105 active:scale-95'
                }
              `}
            >
              {/* Lock icon for disabled actions */}
              {action.disabled && (
                <div className="absolute top-2 right-2 bg-white rounded-full p-1">
                  <Lock className="w-3 h-3 text-gray-600" />
                </div>
              )}

              <div className="text-center">
                {/* Actions Icons */}
                <div className="flex justify-center mb-2">
                  <IconComponent className="w-6 h-6" />
                </div>
                <div className="text-sm font-semibold">{action.label}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Warning if wallet is frozen */}
      {!isWalletActive && walletData && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-yellow-800">
              Some actions are disabled. Your wallet is frozen.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuickActions;