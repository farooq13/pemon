import api from './api';

const kycService = {
  /*
    Submit KYC verification.
   */
  submitKYC: async (formData) => {
    const response = await api.post('/kyc/submit/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /*
    Get KYC status.
   */
  getStatus: async () => {
    const response = await api.get('/kyc/status/');
    return response.data;
  },

  /*
    Get detailed KYC information.
   */
  getDetail: async () => {
    const response = await api.get('/kyc/detail/');
    return response.data;
  },

  /*
    Get tier comparison.
   */
  getTiers: async () => {
    const response = await api.get('/kyc/tiers/');
    return response.data;
  },

  /*
    Check transaction eligibility.
   */
  checkEligibility: async (amount) => {
    const response = await api.post('/kyc/check-eligibility/', {
      amount,
    });
    return response.data;
  },
};

export default kycService;