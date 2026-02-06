import axios from 'axios';

// Base API URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add authentication token to requests.
 */
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for handling common response scenarios.
 */
api.interceptors.response.use(
  (response) => {
    // Return response data directly
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          const response = await axios.post(
            `${API_BASE_URL}/auth/token/refresh/`,
            { refresh: refreshToken }
          );

          const { access } = response.data;
          
          // Save new access token
          localStorage.setItem('access_token', access);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        // Redirect to login
        window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    return Promise.reject(error);
  }
);

/**
 * Helper function to handle API errors consistently.
 * 
 * @param {Error} error - Axios error object
 * @returns {Object} Formatted error object
 */
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { data, status } = error.response;
    
    // Extract field errors from DRF format
    // DRF returns errors as: { fieldName: [{ string: 'message', code: 'code' }] } or { fieldName: ['message'] }
    const fieldErrors = {};
    const errors = data?.error?.field_errors || data?.errors || data || {};
    
    for (const [field, messages] of Object.entries(errors)) {
      if (Array.isArray(messages) && messages.length > 0) {
        // Handle both ErrorDetail objects and plain strings
        fieldErrors[field] = messages.map((msg) => 
          typeof msg === 'string' ? msg : msg.string || String(msg)
        );
      } else if (typeof messages === 'string') {
        fieldErrors[field] = [messages];
      }
    }
    
    // Get a general error message
    const message = data?.error?.message || data?.message || data?.detail || 'An error occurred';
    
    return {
      message: typeof message === 'string' ? message : 'An error occurred',
      code: data?.error?.code || 'error',
      fieldErrors,
      status,
    };
  } else if (error.request) {
    // Request made but no response received
    return {
      message: 'Unable to connect to server. Please check your internet connection.',
      code: 'network_error',
      fieldErrors: {},
    };
  } else {
    // Something else happened
    return {
      message: error.message || 'An unexpected error occurred',
      code: 'unknown_error',
      fieldErrors: {},
    };
  }
};

/**
 * Get formatted error message from API error.
 * 
 * @param {Error} error - Axios error object
 * @returns {string} Error message
 */
export const getErrorMessage = (error) => {
  const apiError = handleApiError(error);
  return apiError.message;
};

/**
 * Get field-specific errors from API error.
 * 
 * @param {Error} error - Axios error object
 * @returns {Object} Field errors object
 */
export const getFieldErrors = (error) => {
  const apiError = handleApiError(error);
  return apiError.fieldErrors;
};

export default api;