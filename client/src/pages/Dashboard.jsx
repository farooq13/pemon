import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Bell, 
  Eye, 
  EyeOff, 
  Plus, 
  ArrowUpRight,
  ArrowDownLeft,
  ChevronRight,
  Zap
} from 'lucide-react';
import walletService from '../services/walletService';
import kycService from '../services/kycService';
import transactionService from '../services/transactionService';
import QuickActions from '../components/wallet/QuickActions';
import BottomNavigation from '../components/layout/BottomNavigation';
import Sidebar from '../components/layout/Sidebar';


const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [walletData, setWalletData] = useState(null);
  const [kycStatus, setKycStatus] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showBalance, setShowBalance] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');

    try {
      const [wallet, kyc, transactions] = await Promise.all([
        walletService.getBalance().catch(() => null),
        kycService.getStatus().catch(() => null),
        transactionService.getTransactions({ page_size: 3 }).catch(() => ({ data: [] })),
      ]);

      setWalletData(wallet);
      setKycStatus(kyc);
      setRecentTransactions(transactions.data || []);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  /*
    Copy virtual account number to clipboard
   */
  const copyAccountNumber = () => {
    if (walletData?.virtual_account_number) {
      navigator.clipboard.writeText(walletData.virtual_account_number);
      // You can add a toast notification here
      alert('Account number copied!');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20 lg:pb-0 lg:ml-32">
      {/* Sidebar - Desktop/Tablet */}
      <Sidebar />

      {/* Main Container */}
      <div className="lg:pl-0 pb-20 lg:pb-0">
        {/* Mobile Header - Minimal & Clean */}
        <header className="bg-white sticky top-0 z-10 lg:hidden">
          <div className="px-4 py-3">
            <div className="flex items-center justify-between">
              {/* User Greeting */}
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-600 to-blue-600 flex items-center justify-center">
                  <span className="text-white font-bold text-sm">
                    {user?.email?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 leading-none mb-0.5">Hi</p>
                  <p className="text-sm font-bold text-gray-900 leading-none">
                    {user?.first_name || user?.email?.split('@')[0] || 'User'}
                  </p>
                </div>
              </div>

              {/* Notification Bell */}
              <button className="relative p-2 hover:bg-gray-50 rounded-full transition-colors active:scale-95">
                <Bell className="w-5 h-5 text-gray-700" strokeWidth={2.5} />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
              </button>
            </div>
          </div>
        </header>

        {/* Desktop Header */}
        <header className="hidden lg:block bg-white border-b border-gray-100">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">
                  Welcome back, {user?.first_name || user?.email?.split('@')[0]}
                </p>
              </div>
              
              <button className="relative p-2.5 hover:bg-gray-50 rounded-full transition-colors">
                <Bell className="w-6 h-6 text-gray-700" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="px-4 py-4 lg:px-6 lg:py-6 max-w-7xl mx-auto space-y-4 lg:space-y-6">
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-white text-xs">!</span>
              </div>
              <div className="flex-1">
                <p className="text-red-700 font-medium text-sm">{error}</p>
                <button
                  onClick={fetchDashboardData}
                  className="text-red-600 text-xs font-medium mt-1 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          )}

          {/* Balance Card - Modern Design */}
          <div className="relative overflow-hidden">
            <div className="bg-blue-500 from-blue-600 via-blue-700 to-purple-700 rounded-[15px] p-5 lg:p-6 text-white shadow-xl shadow-blue-200">
              {loading ? (
                <div className="animate-pulse space-y-4">
                  <div className="h-3 bg-blue-500/50 rounded w-1/3"></div>
                  <div className="h-10 bg-blue-500/50 rounded w-2/3"></div>
                  <div className="h-3 bg-blue-500/50 rounded w-1/2"></div>
                </div>
              ) : walletData ? (
                <>
                  {/* Top Row */}
                  <div className="flex items-start justify-between mb-8">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-7 h-7 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
                            <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd"/>
                          </svg>
                        </div>
                        <span className="text-xs font-medium text-white/80">Available Balance</span>
                      </div>

                      {/* Balance Amount */}
                      <div className="flex items-baseline gap-2">
                        <p className="text-[32px] lg:text-[40px] font-bold leading-none">
                          {showBalance ? (
                            walletData.formatted_balance?.replace('₦', '') || 
                            walletService.formatCurrency(walletData.balance).replace('₦', '')
                          ) : (
                            '••••••'
                          )}
                        </p>
                        <span className="text-lg font-medium text-white/90">₦</span>
                      </div>
                    </div>

                    {/* Eye Toggle */}
                    <button
                      onClick={() => setShowBalance(!showBalance)}
                      className="p-2 hover:bg-white/10 hover:cursor-pointer rounded-full transition-all active:scale-95"
                    >
                      {showBalance ? (
                        <Eye className="w-5 h-5" strokeWidth={2.5} />
                      ) : (
                        <EyeOff className="w-5 h-5" strokeWidth={2.5} />
                      )}
                    </button>
                  </div>

                  {/* Bottom Row */}
                  <div className="flex items-end justify-between">
                    {/* Account Number */}
                    <div className="bg-white/10 backdrop-blur-sm rounded-xl px-3 py-2 border border-white/20">
                      <p className="text-[10px] text-white/70 mb-0.5">Account Number</p>
                      <div className='flex justify-between items-center'>
                        <p className="font-mono font-semibold text-sm">
                          {walletData.virtual_account_number}
                        </p>
                        <button
                          onClick={copyAccountNumber}
                          className="text-white hover:scale-115 hover:cursor-pointer hover:bg-opacity-20 p-2 rounded-lg transition"
                          title="Copy account number"
                          >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                    

                    {/* Add Money Button */}
                    <button
                      onClick={() => navigate('/deposit')}
                      className="bg-white text-blue-600 px-4 py-2 rounded-xl font-semibold text-sm flex items-center gap-1.5 hover:bg-blue-50 hover:cursor-pointer transition-all active:scale-95 shadow-lg"
                    >
                      <Plus className="w-4 h-4" strokeWidth={2.5} />
                      Add Money
                    </button>
                  </div>

                  {/* Frozen Warning */}
                  {walletData.is_frozen && (
                    <div className="mt-3 p-2.5 bg-yellow-400/20 backdrop-blur-sm border border-yellow-300/30 rounded-lg">
                      <p className="text-xs text-yellow-100 flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5" />
                        Wallet is frozen. Contact support.
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-white/90 mb-1 font-medium">No wallet found</p>
                  <p className="text-xs text-white/70">Complete KYC verification to get started</p>
                </div>
              )}

              {/* Background Decoration */}
              <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/5 rounded-full blur-3xl"></div>
              <div className="absolute -left-10 top-0 w-32 h-32 bg-purple-500/20 rounded-full blur-2xl"></div>
            </div>
          </div>

          {/* Quick Actions */}
          <QuickActions walletData={walletData} />

          {/* Recent Transactions */}
          <div className="bg-white rounded-[24px] shadow-sm overflow-hidden">
            <div className="px-4 py-3.5 flex items-center justify-between border-b border-gray-100">
              <h3 className="font-bold text-gray-900 text-base">Recent Transactions</h3>
              <button
                onClick={() => navigate('/transactions')}
                className="text-blue-600 text-sm font-semibold flex items-center gap-0.5 hover:gap-1 transition-all"
              >
                See all
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="divide-y divide-gray-100">
              {recentTransactions.length > 0 ? (
                recentTransactions.map((txn) => {
                  const isDebit = txn.is_debit || txn.user_email === user?.email;
                  
                  return (
                    <button
                      key={txn.id}
                      onClick={() => navigate(`/transactions`)}
                      className="w-full px-4 py-3.5 hover:bg-gray-50 transition-colors text-left"
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
                          <p className="text-sm font-semibold text-gray-900 truncate">
                            {transactionService.getTypeLabel(txn.transaction_type)}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {new Date(txn.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>

                        {/* Amount */}
                        <div className="text-right">
                          <p className={`text-sm font-bold ${
                            isDebit ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {isDebit ? '-' : '+'}{txn.formatted_amount || transactionService.formatCurrency(txn.amount)}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })
              ) : (
                <div className="px-4 py-16 text-center">
                  <div className="w-14 h-14 mx-auto mb-3 bg-gray-100 rounded-2xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <p className="text-gray-900 font-medium text-sm mb-1">No transactions yet</p>
                  <p className="text-gray-500 text-xs">Your transaction history will appear here</p>
                </div>
              )}
            </div>
          </div>

          {/* KYC Status Banner */}
          {kycStatus && (
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-[24px] p-4 border border-purple-100/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-purple-200">
                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 mb-0.5">KYC Verification</p>
                    <p className="text-sm font-bold text-gray-900">
                      Tier {kycStatus.tier} - {kycStatus.status_display || kycStatus.status}
                    </p>
                  </div>
                </div>
                
                {kycStatus.can_upgrade?.can_upgrade && (
                  <button
                    onClick={() => navigate('/kyc')}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl transition-colors active:scale-95 shadow-lg shadow-purple-200"
                  >
                    Upgrade
                  </button>
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Bottom Navigation - Mobile Only */}
      <BottomNavigation />
    </div>
  );
};

export default Dashboard;