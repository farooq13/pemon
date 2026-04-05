import React, { useState, useEffect } from 'react';
import { Shield, KeyRound, CheckCircle, AlertCircle, Save } from 'lucide-react';
import authService from '../services/authService';

const Settings = () => {
  const [user, setUser] = useState(null);
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch latest user profile to check if transfer pin is set
    const fetchUser = async () => {
      try {
        const profile = await authService.getProfile();
        setUser(profile);
        // Sync to localStorage so other components see the updated has_transfer_pin
        const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
        localStorage.setItem('user', JSON.stringify({ ...storedUser, ...profile }));
      } catch (err) {
        console.error('Error fetching profile', err);
      }
    };
    fetchUser();
  }, []);

  const handleSetPin = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (pin.length !== 4 || !/^\d+$/.test(pin)) {
      setError('PIN must be exactly 4 digits.');
      return;
    }
    
    if (pin !== confirmPin) {
      setError('PINs do not match.');
      return;
    }

    setLoading(true);
    try {
      // Create a specific service method or use api directly
      const { default: api } = await import('../services/api');
      const res = await api.post('/auth/set-transfer-pin/', { pin });
      setMessage(res.data.message || 'Transfer PIN updated successfully.');
      setPin('');
      setConfirmPin('');
      
      // Update local state and localStorage
      setUser((prev) => prev ? { ...prev, has_transfer_pin: true } : prev);
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
      localStorage.setItem('user', JSON.stringify({ ...storedUser, has_transfer_pin: true }));
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.pin?.[0] || 'Unable to set transfer PIN.');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex justify-center items-center h-full min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage your account settings and preferences.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Security</h2>
          </div>
          <p className="text-sm text-gray-600">
            Set up a secure transfer PIN to authorize all your transactions.
          </p>
        </div>

        <div className="p-6">
          <div className="max-w-md">
            {user.has_transfer_pin ? (
              <div className="mb-6 p-4 bg-green-50 rounded-lg flex items-start gap-3 border border-green-100">
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-green-900">Transfer PIN is set</p>
                  <p className="text-sm text-green-700 mt-1">
                    Your account is secure. You can update your PIN below.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mb-6 p-4 bg-yellow-50 rounded-lg flex items-start gap-3 border border-yellow-100">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-yellow-900">Transfer PIN missing</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    You must set a Transfer PIN before you can send money.
                  </p>
                </div>
              </div>
            )}

            <form onSubmit={handleSetPin} className="space-y-4">
              {message && (
                <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm border border-green-100">
                  {message}
                </div>
              )}
              {error && (
                <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm border border-red-100">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {user.has_transfer_pin ? 'New Transfer PIN' : 'Create Transfer PIN'}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <KeyRound className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    maxLength={4}
                    inputMode="numeric"
                    value={pin}
                    onChange={(e) => setPin(e.target.value.replace(/\\D/g, ''))}
                    placeholder="Enter 4-digit PIN"
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm Transfer PIN
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <KeyRound className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    maxLength={4}
                    inputMode="numeric"
                    value={confirmPin}
                    onChange={(e) => setConfirmPin(e.target.value.replace(/\\D/g, ''))}
                    placeholder="Confirm 4-digit PIN"
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading || pin.length !== 4 || confirmPin.length !== 4}
                  className={`
                    w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white 
                    ${loading || pin.length !== 4 || confirmPin.length !== 4
                      ? 'bg-blue-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                    }
                  `}
                >
                  <Save className="w-5 h-5 mr-2" />
                  {loading ? 'Saving...' : 'Save PIN'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
