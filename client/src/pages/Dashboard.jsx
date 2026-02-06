import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [showMessage, setShowMessage] = useState(false);
  const message = location.state?.message;

  useEffect(() => {
    if (message) {
      setShowMessage(true);
      // Auto-hide message after 5 seconds
      const timer = setTimeout(() => setShowMessage(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-blue-600">Pemon</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">
              {user?.full_name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-red-500 hover:text-white transition hover:cursor-pointer"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Success Message */}
      {showMessage && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start">
            <svg className="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-green-700">{message}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Welcome to Pemon! 
            </h2>
            <p className="text-gray-600 mb-6">
              Your account has been created successfully.
            </p>

            {/* User Info Card */}
            <div className="max-w-md mx-auto bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm opacity-90">Account Details</span>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  user?.email_verified ? 'bg-green-500' : 'bg-yellow-500'
                }`}>
                  {user?.email_verified ? '✓ Verified' : ' Pending Verification'}
                </span>
              </div>
              
              <div className="space-y-3 text-left">
                <div>
                  <p className="text-xs opacity-75">Name</p>
                  <p className="font-medium">{user?.full_name}</p>
                </div>
                <div>
                  <p className="text-xs opacity-75">Email</p>
                  <p className="font-medium">{user?.email}</p>
                </div>
                <div>
                  <p className="text-xs opacity-75">Phone</p>
                  <p className="font-medium">{user?.phone_number}</p>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="mt-8 text-left max-w-md mx-auto">
              <h3 className="font-semibold text-gray-900 mb-4">Next Steps:</h3>
              <div className="space-y-3">
                <div className="flex items-start">
                  <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                    user?.email_verified ? 'bg-green-500' : 'bg-gray-300'
                  }`}>
                    {user?.email_verified ? (
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <span className="text-xs text-gray-600">1</span>
                    )}
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Verify your email</p>
                    <p className="text-xs text-gray-500">Check your inbox for verification code</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center">
                    <span className="text-xs text-gray-600">2</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Complete KYC verification</p>
                    <p className="text-xs text-gray-500">Coming in Sprint 2</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center">
                    <span className="text-xs text-gray-600">3</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Create your wallet</p>
                    <p className="text-xs text-gray-500">Coming in Sprint 3</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center">
                    <span className="text-xs text-gray-600">4</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Start transacting</p>
                    <p className="text-xs text-gray-500">Send money, pay bills, and more</p>
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Button */}
            {!user?.email_verified && (
              <div className="mt-8">
                <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 hover:cursor-pointer text-white font-medium rounded-lg transition">
                  Verify Email Now
                </button>
              </div>
            )}
          </div>
        </div>

        
      </main>
    </div>
  );
};

export default Dashboard;