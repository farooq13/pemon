import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import walletService from '../services/walletService';
import kycService from '../services/kycService';
import BalanceCard from '../components/wallet/BalanceCard';
import QuickActions from '../components/wallet/QuickActions';


const Dashboard = () => {
  const { user } = useAuth();

  const [walletData, setWalletData] = useState(null);
  const [kycStatus, setKycStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  /*
    Fetch wallet and KYC data on component mount
   */
  useEffect(() => {
    fetchDashboardData();
  }, []);

  /*
    Fetch all dashboard data
   */
  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');

    try {
      // Fetch wallet balance and KYC status in parallel
      const [wallet, kyc] = await Promise.all([
        walletService.getBalance().catch(() => null),
        kycService.getStatus().catch(() => null),
      ]);

      setWalletData(wallet);
      setKycStatus(kyc);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Refresh wallet balance
   */
  const refreshBalance = async () => {
    try {
      const wallet = await walletService.getBalance();
      setWalletData(wallet);
    } catch (err) {
      console.error('Error refreshing balance:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Welcome back, {user?.email || 'User'}!
              </p>
            </div>

            {/* Notification Bell (Placeholder) */}
            <button className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {/* Notification badge */}
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-red-600 font-medium">{error}</p>
              <button
                onClick={fetchDashboardData}
                className="text-red-700 text-sm underline mt-1"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Balance & Actions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Balance Card */}
            <BalanceCard
              walletData={walletData}
              loading={loading}
              onRefresh={refreshBalance}
            />

            {/* Quick Actions */}
            <QuickActions walletData={walletData} />

            {/* Recent Transactions Preview (Placeholder) */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">Recent Transactions</h3>
                <button className="text-blue-600 hover:text-blue-700 hover:cursor-pointer text-sm font-medium">
                  View all →
                </button>
              </div>

              {/* Empty state or loading */}
              <div className="text-center py-8 text-gray-500">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p>No recent transactions</p>
                <p className="text-sm mt-1">Your transactions will appear here</p>
              </div>
            </div>
          </div>

          {/* Right Column - KYC Status & Info */}
          <div className="space-y-6">
            {/* KYC Status Widget */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">KYC Status</h3>

              {loading ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ) : kycStatus ? (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-700">Verification Tier</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      kycStatus.tier === 3 ? 'bg-green-100 text-green-800' :
                      kycStatus.tier === 2 ? 'bg-purple-100 text-purple-800' :
                      kycStatus.tier === 1 ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      Tier {kycStatus.tier}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-700">Status</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      kycStatus.status === 'approved' ? 'bg-green-100 text-green-800' :
                      kycStatus.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      kycStatus.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {kycStatus.status_display || kycStatus.status}
                    </span>
                  </div>

                  {kycStatus.limits && (
                    <div className="pt-4 border-t border-gray-200">
                      <p className="text-sm text-gray-600 mb-2">Transaction Limits</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Daily:</span>
                          <span className="font-medium">{kycStatus.limits.daily_limit_formatted || '₦0'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Per Transaction:</span>
                          <span className="font-medium">{kycStatus.limits.single_transaction_limit_formatted || '₦0'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {kycStatus.can_upgrade?.can_upgrade && (
                    <button className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition">
                      Upgrade to Tier {kycStatus.can_upgrade.next_tier?.tier || (kycStatus.tier + 1)}
                    </button>
                  )}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-600 mb-4">Complete KYC to unlock full features</p>
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition">
                    Start KYC
                  </button>
                </div>
              )}
            </div>

            {/* Help & Support */}
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl shadow-lg p-6 border border-purple-100">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Need Help?</h3>
              <p className="text-gray-700 text-sm mb-4">
                Our support team is available 24/7 to assist you.
              </p>
              <button className="w-full bg-white hover:bg-gray-50 text-gray-900 font-medium py-2 rounded-lg transition border border-gray-200">
                Contact Support
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;