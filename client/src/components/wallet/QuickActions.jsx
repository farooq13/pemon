import { useNavigate } from 'react-router-dom';
import { Send, Download, Receipt, History, Lock } from 'lucide-react';


const QuickActions = ({ walletData }) => {
  const navigate = useNavigate();
  const isWalletActive = walletData && !walletData.is_frozen;

  const actions = [
    {
      id: 'send',
      label: 'Send',
      icon: Send,
      path: '/transfer',
      gradient: 'from-blue-500 to-blue-600',
      bgColor: 'bg-white',
      textColor: 'text-black',
      disabled: !isWalletActive,
    },
    {
      id: 'receive',
      label: 'Receive',
      icon: Download,
      path: '/receive',
      gradient: 'from-green-500 to-green-600',
      bgColor: 'bg-white',
      textColor: 'text-black',
      disabled: false,
    },
    {
      id: 'bills',
      label: 'Bills',
      icon: Receipt,
      path: '/bills',
      gradient: 'from-purple-500 to-purple-600',
      bgColor: 'white',
      textColor: 'text-black',
      disabled: !isWalletActive,
    },
    {
      id: 'history',
      label: 'History',
      icon: History,
      path: '/transactions',
      gradient: 'from-orange-500 to-orange-600',
      bgColor: 'white',
      textColor: 'black',
      disabled: false,
    },
  ];

  const handleClick = (action) => {
    if (action.disabled) {
      alert('Your wallet is frozen. Please contact support.');
      return;
    }
    navigate(action.path);
  };

  return (
    <div className="bg-white rounded-[24px] shadow-sm p-4 lg:p-5">
      <h3 className="font-bold text-gray-900 text-base mb-3.5 lg:mb-4">Quick Actions</h3>

      <div className="grid grid-cols-4 gap-3 lg:gap-4">
        {actions.map((action) => {
          const IconComponent = action.icon;
          
          return (
            <button
              key={action.id}
              onClick={() => handleClick(action)}
              disabled={action.disabled}
              className={`
                relative p-4 rounded-2xl transition-all text-center
                ${action.disabled 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'hover:scale-[1.02] active:scale-[0.98] cursor-pointer'
                }
                ${action.bgColor}
              `}
            >
              {/* Lock icon for disabled */}
              {action.disabled && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-white rounded-full flex items-center justify-center shadow-sm">
                  <Lock className="w-3 h-3 text-gray-500" />
                </div>
              )}

              {/* Icon */}
              <div className={`
                w-12 h-12 rounded-xl flex items-center justify-center mb-2
                mx-auto
                bg-blue-500
              `}>
                <IconComponent className="w-6 h-6 text-white" strokeWidth={2.5} />
              </div>

              {/* Label */}
              <p className={`text-sm font-semibold ${action.textColor}`}>
                {action.label}
              </p>
            </button>
          );
        })}
      </div>

      {/* Frozen Warning */}
      {!isWalletActive && walletData && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-100 rounded-xl">
          <p className="text-xs text-yellow-800 flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Some actions are disabled because your wallet is frozen.
          </p>
        </div>
      )}
    </div>
  );
};

export default QuickActions;