import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import kycService from '../services/kycService';

const KYCStatus = () => {
  const [kycStatus, setKycStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  /**
   * Fetch KYC status on mount.
   */
  useEffect(() => {
    fetchKYCStatus();
  }, []);

  /*
   * Fetch KYC status from API.
   */
  const fetchKYCStatus = async () => {
    try {
      const data = await kycService.getStatus();
      setKycStatus(data);
      setError('');
    } catch (err) {
      error.message('Failed to fetch KYC status:', err);
      // Set default unverified status if error
      setKycStatus({
        tier: 0,
        status: 'unverified',
        limits: {
          daily_limit: '₦0',
          single_transaction_limit: '₦0',
          total_balance_limit: '₦0',
        },
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get status badge color.
   */
  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  /**
   * Get status icon.
   */
  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'pending':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 11-2 0 1 1 0 012 0zM8.707 13.707a1 1 0 001.414-1.414L10.414 11H13a1 1 0 100-2h-2.586l-.707.707a1 1 0 01-1.414-1.414l2-2a1 1 0 011.414 0l2 2a1 1 0 01-1.414 1.414L10.414 9H13a1 1 0 100 2h-2.586l.707.707a1 1 0 001.414-1.414l-2-2a1 1 0 00-1.414 0l-2 2z" clipRule="evenodd" />
          </svg>
        );
      case 'rejected':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  /**
   * Get tier badge color.
   */
  const getTierColor = (tier) => {
    switch (tier) {
      case 0:
        return 'bg-gray-100 text-gray-800';
      case 1:
        return 'bg-blue-100 text-blue-800';
      case 2:
        return 'bg-purple-100 text-purple-800';
      case 3:
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * Get tier name.
   */
  const getTierName = (tier) => {
    switch (tier) {
      case 0:
        return 'Unverified';
      case 1:
        return 'Tier 1 - Basic KYC';
      case 2:
        return 'Tier 2 - Intermediate KYC';
      case 3:
        return 'Tier 3 - Full KYC';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M6.29 1.884A1.5 1.5 0 108.107 6.21L9 7.11V3a1.5 1.5 0 00-2.71-.884zM1 11a1 1 0 011-1h1.05a2.5 2.5 0 014.9 0h2.1a2.5 2.5 0 014.9 0H17a1 1 0 110 2h-1.05a2.5 2.5 0 01-4.9 0h-2.1a2.5 2.5 0 01-4.9 0H2a1 1 0 01-1-1z" />
          </svg>
          KYC Verification Status
        </h3>
      </div>

      <div className="p-6 space-y-6">
        {/* Status & Tier Row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Status */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Status</p>
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border-2 font-semibold text-sm ${getStatusColor(kycStatus?.status)}`}>
              {getStatusIcon(kycStatus?.status)}
              <span className="capitalize">{kycStatus?.status || 'Unverified'}</span>
            </div>
          </div>

          {/* Tier */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Tier</p>
            <span className={`inline-block px-4 py-2 rounded-full font-semibold text-sm ${getTierColor(kycStatus?.tier)}`}>
              {getTierName(kycStatus?.tier)}
            </span>
          </div>
        </div>

        {/* Transaction Limits */}
        {kycStatus?.limits && (
          <div className="border-t pt-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Your Transaction Limits</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-xs text-gray-600 mb-1">Daily Limit</p>
                <p className="text-lg font-bold text-blue-600">{kycStatus.limits.daily_limit}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-xs text-gray-600 mb-1">Per Transaction</p>
                <p className="text-lg font-bold text-green-600">{kycStatus.limits.single_transaction_limit}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-xs text-gray-600 mb-1">Wallet Balance</p>
                <p className="text-lg font-bold text-purple-600">{kycStatus.limits.total_balance_limit}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Section */}
        <div className="border-t pt-6">
          {kycStatus?.status === 'approved' ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <div>
                  <p className="font-medium text-green-900">Verification Complete</p>
                  <p className="text-sm text-green-700">You can now use all Pemon features</p>
                </div>
              </div>
            </div>
          ) : kycStatus?.status === 'pending' ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <svg className="w-6 h-6 text-yellow-600 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 11-2 0 1 1 0 012 0zM8.707 13.707a1 1 0 001.414-1.414L10.414 11H13a1 1 0 100-2h-2.586l-.707.707a1 1 0 01-1.414-1.414l2-2a1 1 0 011.414 0l2 2a1 1 0 01-1.414 1.414L10.414 9H13a1 1 0 100 2h-2.586l.707.707a1 1 0 001.414-1.414l-2-2a1 1 0 00-1.414 0l-2 2z" clipRule="evenodd" />
                </svg>
                <div>
                  <p className="font-medium text-yellow-900">Under Review</p>
                  <p className="text-sm text-yellow-700">Your KYC is being verified. This usually takes 24-48 hours.</p>
                </div>
              </div>
            </div>
          ) : kycStatus?.status === 'rejected' ? (
            <div className="space-y-3">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-3">
                  <svg className="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="font-medium text-red-900">Verification Rejected</p>
                </div>
                {kycStatus?.rejection_reason && (
                  <p className="text-sm text-red-700 ml-9">{kycStatus.rejection_reason}</p>
                )}
              </div>
              <Link
                to="/kyc"
                className="block bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-center transition duration-200"
              >
                Resubmit KYC
              </Link>
            </div>
          ) : (
            <Link
              to="/kyc"
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-3 rounded-lg transition duration-200 w-full"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Start KYC Verification
            </Link>
          )}
        </div>

        {/* Info Section */}
        {kycStatus?.tier === 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
              </svg>
              <div className="text-sm text-blue-700">
                <p className="font-medium mb-1">Complete KYC to unlock features</p>
                <p className="text-xs">Verify your identity to start transacting and access higher transaction limits.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KYCStatus;
