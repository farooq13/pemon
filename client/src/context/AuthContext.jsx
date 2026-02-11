import { createContext, useContext, useEffect, useState } from 'react';
import authService from '../services/authService';

// Create Auth Context
const AuthContext = createContext(null);

/**
 * Wraps the app and provides authentication state and methods.
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  /**
   * Initialize authentication state on mount.
   */
  useEffect(() => {
    initializeAuth();
  }, []);

  /**
   * Initialize authentication by checking for stored tokens.
   */
  const initializeAuth = async () => {
    try {
      const token = authService.getAccessToken();
      const storedUser = authService.getCurrentUser();

      if (token && storedUser) {
        // Verify token is still valid
        try {
          const response = await authService.checkAuthStatus();
          setUser(response.user);
          setIsAuthenticated(true);
        } catch (error) {
          // Token invalid, clear storage
          await authService.logout();
          setUser(null);
          setIsAuthenticated(false);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Register a new user.
   */
  const register = async (userData) => {
    try {
      const response = await authService.register(userData);
      
      // Set user state after registration
      const registeredUser = {
        id: response.user.id,
        email: response.user.email,
        phone_number: response.user.phone_number,
        first_name: response.user.first_name,
        last_name: response.user.last_name,
      };
      
      setUser(registeredUser);
      setIsAuthenticated(true);
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  /**
   * Login user with email and password.
   */
  const login = async (email, password) => {
    try {
      const response = await authService.login(email, password);
      
      setUser(response.user);
      setIsAuthenticated(true);
      
      return response;
    } catch (error) {
      throw error;
    }
  };

  /**
   * Logout user and clear state.
   */
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  /**
   * Update user profile in state.
   */
  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  /**
   * Refresh user data from API.
   */
  const refreshUser = async () => {
    try {
      const profile = await authService.getProfile();
      setUser(profile);
      localStorage.setItem('user', JSON.stringify(profile));
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  // Context value
  const value = {
    user,
    isAuthenticated,
    loading,
    register,
    login,
    logout,
    updateUser,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use Auth context.
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthContext;