import { useState } from 'react';

const PersonalInfoStep = ({ formData, onFormDataChange, onNext }) => {
  const [fieldErrors, setFieldErrors] = useState({});

  /*
   * Handle input change and validate in real-time.
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors({ ...fieldErrors, [name]: null });
    }
    
    onFormDataChange({
      ...formData,
      [name]: value,
    });
  };

  /*
    Validate BVN format (11 digits).
   */
  const validateBVN = (bvn) => {
    const cleaned = bvn.replace(/\D/g, '');
    
    if (!cleaned) {
      return 'BVN is required';
    }
    
    if (cleaned.length !== 11) {
      return 'BVN must be exactly 11 digits';
    }
    
    return '';
  };

  /**
   * Validate NIN format (11 digits).
   */
  const validateNIN = (nin) => {
    if (!nin) {
      return ''; // NIN is optional for Tier 1
    }
    
    const cleaned = nin.replace(/\D/g, '');
    
    if (cleaned.length !== 11) {
      return 'NIN must be exactly 11 digits';
    }
    
    return '';
  };

  /**
   * Validate date of birth.
   */
  const validateDateOfBirth = (dob) => {
    if (!dob) {
      return 'Date of birth is required';
    }
    
    const date = new Date(dob);
    const today = new Date();
    const age = today.getFullYear() - date.getFullYear();
    
    if (age < 18) {
      return 'You must be at least 18 years old';
    }
    
    if (age > 120) {
      return 'Please enter a valid date of birth';
    }
    
    return '';
  };

  /**
   * Handle form submission and validation.
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    const errors = {};
    
    // Validate each field
    const bvnError = validateBVN(formData.bvn);
    if (bvnError) errors.bvn = bvnError;
    
    const ninError = validateNIN(formData.nin);
    if (ninError) errors.nin = ninError;
    
    const dobError = validateDateOfBirth(formData.date_of_birth);
    if (dobError) errors.date_of_birth = dobError;
    
    if (!formData.address.trim()) {
      errors.address = 'Address is required';
    }
    
    if (!formData.city.trim()) {
      errors.city = 'City is required';
    }
    
    if (!formData.state.trim()) {
      errors.state = 'State is required';
    }
    
    // If there are errors, display them
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    
    // All validations passed, proceed to next step
    onNext();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Personal Information</h2>
        <p className="text-gray-600">Please provide your personal details for verification</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* BVN */}
        <div>
          <label htmlFor="bvn" className="block text-sm font-medium text-gray-700 mb-2">
            BVN (Bank Verification Number) <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="bvn"
            name="bvn"
            value={formData.bvn}
            onChange={handleChange}
            placeholder="Enter your 11-digit BVN"
            maxLength="11"
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.bvn
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition placeholder:text-gray-500`}
          />
          {fieldErrors.bvn && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.bvn}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            You can find your BVN on your bank statement or ATM card
          </p>
        </div>

        {/* NIN */}
        <div>
          <label htmlFor="nin" className="block text-sm font-medium text-gray-700 mb-2">
            NIN (National Identification Number)
            <span className="text-gray-500 text-xs ml-1">(Optional)</span>
          </label>
          <input
            type="text"
            id="nin"
            name="nin"
            value={formData.nin}
            onChange={handleChange}
            placeholder="Enter your 11-digit NIN"
            maxLength="11"
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.nin
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition placeholder:text-gray-500`}
          />
          {fieldErrors.nin && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.nin}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Required for Tier 2 and Tier 3 verification
          </p>
        </div>

        {/* Date of Birth */}
        <div>
          <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700 mb-2">
            Date of Birth <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="date_of_birth"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleChange}
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.date_of_birth
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition`}
          />
          {fieldErrors.date_of_birth && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.date_of_birth}</p>
          )}
        </div>

        {/* Address */}
        <div>
          <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
            Residential Address <span className="text-red-500">*</span>
          </label>
          <textarea
            id="address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            placeholder="Enter your residential address"
            rows="3"
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.address
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition placeholder:text-gray-500 resize-none`}
          />
          {fieldErrors.address && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.address}</p>
          )}
        </div>

        {/* City */}
        <div>
          <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">
            City <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="city"
            name="city"
            value={formData.city}
            onChange={handleChange}
            placeholder="Enter your city"
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.city
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition placeholder:text-gray-500`}
          />
          {fieldErrors.city && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.city}</p>
          )}
        </div>

        {/* State */}
        <div>
          <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-2">
            State <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="state"
            name="state"
            value={formData.state}
            onChange={handleChange}
            placeholder="Enter your state"
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.state
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition placeholder:text-gray-500`}
          />
          {fieldErrors.state && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.state}</p>
          )}
        </div>

        {/* Submit Button */}
        <div className="pt-6">
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition duration-200"
          >
            Continue to Documents
          </button>
        </div>
      </form>
    </div>
  );
};

export default PersonalInfoStep;
