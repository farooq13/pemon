import { useNavigate, useLocation } from 'react-router-dom';
import {
  Home,
  ArrowLeftRight,
  TrendingUp,
  CreditCard,
  User,
  Settings,
  HelpCircle,
  LogOut,
  Menu,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  //  Collapsed by default
  const [collapsed, setCollapsed] = useState(true);

  const mainNavItems = [
    { id: 'home', label: 'Home', icon: Home, path: '/dashboard' },
    { id: 'transactions', label: 'Transactions', icon: ArrowLeftRight, path: '/transactions' },
    { id: 'transfer', label: 'Transfer', icon: TrendingUp, path: '/transfer' },
    { id: 'cards', label: 'Cards', icon: CreditCard, path: '/cards' },
  ];

  const bottomNavItems = [
    { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
    { id: 'help', label: 'Help', icon: HelpCircle, path: '/help' },
  ];

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    if (confirm('Are you sure you want to logout?')) {
      logout();
      navigate('/login');
    }
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <div
        className="hidden lg:block fixed left-0 top-0 bottom-0 z-50"
        onMouseEnter={() => setCollapsed(false)}
        onMouseLeave={() => setCollapsed(true)}
      >
        <aside
          className={`
            h-full bg-white border-r border-gray-200
            flex flex-col
            transition-all duration-300 ease-in-out
            ${collapsed ? 'w-20' : 'w-64'}
          `}
        >
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
            {!collapsed && (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">P</span>
                </div>
                <span className="font-bold text-xl text-gray-900">Paymon</span>
              </div>
            )}

            <div className="p-2 rounded-lg">
              <Menu className="w-5 h-5 text-gray-600" />
            </div>
          </div>

          {/* User Info */}
          {!collapsed && (
            <div className="px-4 py-4 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">
                    {user?.first_name || user?.email?.split('@')[0] || 'User'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Main Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {mainNavItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              return (
                <button
                  key={item.id}
                  onClick={() => navigate(item.path)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-3 rounded-lg
                    transition-all
                    ${active
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-50'}
                    ${collapsed ? 'justify-center' : ''}
                  `}
                >
                  <Icon
                    className={`w-5 h-5 flex-shrink-0 ${
                      active ? 'stroke-[2.5]' : ''
                    }`}
                  />

                  {!collapsed && (
                    <>
                      <span className={`font-medium ${active ? 'font-semibold' : ''}`}>
                        {item.label}
                      </span>
                      {active && (
                        <div className="ml-auto w-1 h-6 bg-blue-600 rounded-l-full"></div>
                      )}
                    </>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Bottom Navigation */}
          <div className="border-t border-gray-200 px-3 py-4 space-y-1">
            {bottomNavItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              return (
                <button
                  key={item.id}
                  onClick={() => navigate(item.path)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-3 rounded-lg
                    transition-all
                    ${active
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-50'}
                    ${collapsed ? 'justify-center' : ''}
                  `}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {!collapsed && <span className="font-medium">{item.label}</span>}
                </button>
              );
            })}

            {/* Profile */}
            <button
              onClick={() => navigate('/profile')}
              className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-lg
                transition-all text-gray-700 hover:bg-gray-50
                ${collapsed ? 'justify-center' : ''}
              `}
            >
              <User className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="font-medium">Profile</span>}
            </button>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-lg
                transition-all text-red-600 hover:bg-red-50
                ${collapsed ? 'justify-center' : ''}
              `}
            >
              <LogOut className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span className="font-medium">Logout</span>}
            </button>
          </div>
        </aside>
      </div>

      {/* Spacer */}
      <div
        className={`
          hidden lg:block transition-all duration-300 ease-in-out
          ${collapsed ? 'w-20' : 'w-64'}
        `}
      />
    </>
  );
};

export default Sidebar;
