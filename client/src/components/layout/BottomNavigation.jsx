import { useNavigate, useLocation } from 'react-router-dom';
import { Home, ArrowLeftRight, TrendingUp, CreditCard, User } from 'lucide-react';

/*
  Mobile bottom navigation bar.
  Shows on mobile/tablet, hidden on desktop.
 */
const BottomNavigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    {
      id: 'home',
      label: 'Home',
      icon: Home,
      path: '/dashboard',
    },
    {
      id: 'transactions',
      label: 'Transactions',
      icon: ArrowLeftRight,
      path: '/transactions',
    },
    {
      id: 'transfer',
      label: 'Transfer',
      icon: TrendingUp,
      path: '/transfer',
    },
    {
      id: 'cards',
      label: 'Cards',
      icon: CreditCard,
      path: '/cards',
    },
    {
      id: 'profile',
      label: 'Me',
      icon: User,
      path: '/profile',
    },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 lg:hidden z-40">
      <div className="grid grid-cols-5 h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);

          return (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={`
                flex flex-col items-center justify-center gap-1 transition-colors 
                ${active 
                  ? 'text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
                }
              `}
            >
              <Icon className={`w-5 h-5 hover:cursor-pointer ${active ? 'stroke-[2.5]' : ''}`} />
              <span className={`text-xs ${active ? 'font-semibold' : 'font-medium'}`}>
                {item.label}
              </span>
              {active && (
                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-12 h-1 bg-blue-600 rounded-t-full"></div>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNavigation;