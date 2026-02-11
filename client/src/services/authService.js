import api from './api';

const authService = {
  /**
   * Register a new user.
   */
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    
    // Extract tokens from response
    const { user } = response.data;
    
    if (user.access_token && user.refresh_token) {
      // Save tokens to localStorage
      localStorage.setItem('access_token', user.access_token);
      localStorage.setItem('refresh_token', user.refresh_token);
      localStorage.setItem('user', JSON.stringify({
        id: user.id,
        email: user.email,
        phone_number: user.phone_number,
        first_name: user.first_name,
        last_name: user.last_name,
      }));
    }
    
    return response.data;
  },

  /**
    Login user with email and password.
   */
  login: async (email, password) => {
    const response = await api.post('/auth/login/', {
      email,
      password,
    });
    
    const { access, refresh, user } = response.data;
    
    // Save tokens and user info to localStorage
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  /**
   * Logout user and clear local storage.
   */
  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    
    try {
      // Call logout endpoint to blacklist token
      if (refreshToken) {
        await api.post('/auth/logout/', {
          refresh_token: refreshToken,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of API call result
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  /**
   * Get current user profile.
   */
  getProfile: async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  /**
   * Update user profile.
   */
  updateProfile: async (profileData) => {
    const response = await api.patch('/auth/profile/', profileData);
    
    // Update user in localStorage
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    localStorage.setItem('user', JSON.stringify({ ...user, ...response.data }));
    
    return response.data;
  },

  /**
   * Verify OTP code.
   */
  verifyOTP: async (otpCode, otpType) => {
    const response = await api.post('/auth/verify-otp/', {
      otp_code: otpCode,
      otp_type: otpType,
    });
    
    // Update user in localStorage
    const user = response.data.user;
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  /**
   * Resend OTP code.
   */
  resendOTP: async (otpType) => {
    const response = await api.post('/auth/resend-otp/', {
      otp_type: otpType,
    });
    return response.data;
  },

  /**
   * Change user password.
   */
  changePassword: async (oldPassword, newPassword, newPasswordConfirm) => {
    const response = await api.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
    return response.data;
  },

  /**
   * Check authentication status.
   */
  checkAuthStatus: async () => {
    const response = await api.get('/auth/status/');
    return response.data;
  },

  /**
   * Get current user from localStorage.
   */
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated.
   * 
   * @returns {boolean} True if user has valid tokens
   */
  isAuthenticated: () => {
    const token = localStorage.getItem('access_token');
    return !!token;
  },

  /**
   * Get access token.
   */
  getAccessToken: () => {
    return localStorage.getItem('access_token');
  },

  /**
   * Get refresh token.
   */
  getRefreshToken: () => {
    return localStorage.getItem('refresh_token');
  },
};

export default authService;