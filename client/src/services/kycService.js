import api, { getErrorMessage } from './api';

/*
 * KYC Service - Handles all KYC-related API calls.
 */
const kycService = {
  /*
   * Get current user's KYC status.
   */
  getStatus: async () => {
    try {
      const response = await api.get('/kyc/status/');
      return response.data;
    } catch (error) {
      throw getErrorMessage(error) || 'Failed to fetch KYC status';
    }
  },

  /*
   * Get detailed KYC information.
   */
  getDetail: async () => {
    try {
      const response = await api.get('/kyc/detail/');
      return response.data;
    } catch (error) {
      throw getErrorMessage(error) || 'Failed to fetch KYC details';
    }
  },

  /*
   * Submit KYC information with documents.
   */
  submitKYC: async (formData, idDocument, selfie) => {
    try {
      const data = new FormData();
      
      // Add text fields
      data.append('bvn', formData.bvn);
      data.append('nin', formData.nin || '');
      data.append('date_of_birth', formData.date_of_birth);
      data.append('address', formData.address);
      data.append('city', formData.city);
      data.append('state', formData.state);
      data.append('id_type', formData.id_type);
      data.append('id_number', formData.id_number);
      
      // Add files
      if (idDocument) {
        data.append('id_document', idDocument);
      }
      
      if (selfie) {
        data.append('selfie', selfie);
      }
      
      // Use native fetch for multipart upload to avoid the axios instance's
      // default `Content-Type: application/json` header which would prevent
      // the browser from adding the required multipart boundary.
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
      const url = `${API_BASE_URL}/kyc/submit/`;

      // Include Authorization header if present
      const headers = {};
      const token = localStorage.getItem('access_token');
      if (token) headers.Authorization = `Bearer ${token}`;

      const fetchResponse = await fetch(url, {
        method: 'POST',
        headers,
        body: data,
      });

      const responseData = await fetchResponse.json().catch(() => null);

      if (!fetchResponse.ok) {
        const err = new Error(responseData?.message || 'Failed to submit KYC');
        err.response = { data: responseData, status: fetchResponse.status };
        throw err;
      }

      return responseData;
    } catch (error) {
      // Rethrow error to allow caller to handle field-specific errors
      throw error;
    }
  },

  /*
   * Get tier comparison information.
   */
  getTiers: async () => {
    try {
      const response = await api.get('/kyc/tiers/');
      return response.data;
    } catch (error) {
      throw getErrorMessage(error) || 'Failed to fetch tier information';
    }
  },

  /*
   * Check if user can perform a transaction of given amount.
   */
  checkEligibility: async (amount) => {
    try {
      const response = await api.post('/kyc/check-eligibility/', {
        amount,
      });
      return response.data;
    } catch (error) {
      throw getErrorMessage(error) || 'Failed to check transaction eligibility';
    }
  },
};

export default kycService;
