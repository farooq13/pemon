import { useState } from 'react';

const ReviewStep = ({ formData, documents, onSubmit, onPrev, isLoading }) => {
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState('');

  /**
   * Format date to readable format.
   */
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  /**
   * Handle form submission after review.
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    setError('');
    
    if (!acceptedTerms) {
      setError('Please accept the terms and conditions to proceed');
      return;
    }
    
    // Submit the KYC
    onSubmit();
  };

  const ID_TYPE_LABELS = {
    NIN: 'National ID Card',
    DRIVERS_LICENSE: "Driver's License",
    VOTERS_CARD: "Voter's Card",
    INTERNATIONAL_PASSPORT: 'Passport',
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Your Information</h2>
        <p className="text-gray-600">Please review your details carefully before submitting</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Personal Information Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
            <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Personal Information
          </h3>
          
          <div className="space-y-4">
            {/* BVN */}
            <div className="flex justify-between items-start border-b border-blue-100 pb-3">
              <span className="text-sm font-medium text-gray-700">BVN:</span>
              <span className="text-sm text-gray-900">{formData.bvn}</span>
            </div>
            
            {/* NIN */}
            {formData.nin && (
              <div className="flex justify-between items-start border-b border-blue-100 pb-3">
                <span className="text-sm font-medium text-gray-700">NIN:</span>
                <span className="text-sm text-gray-900">{formData.nin}</span>
              </div>
            )}
            
            {/* DOB */}
            <div className="flex justify-between items-start border-b border-blue-100 pb-3">
              <span className="text-sm font-medium text-gray-700">Date of Birth:</span>
              <span className="text-sm text-gray-900">{formatDate(formData.date_of_birth)}</span>
            </div>
            
            {/* Address */}
            <div className="flex justify-between items-start border-b border-blue-100 pb-3">
              <span className="text-sm font-medium text-gray-700">Address:</span>
              <span className="text-sm text-gray-900 text-right max-w-xs">{formData.address}</span>
            </div>
            
            {/* City */}
            <div className="flex justify-between items-start border-b border-blue-100 pb-3">
              <span className="text-sm font-medium text-gray-700">City:</span>
              <span className="text-sm text-gray-900">{formData.city}</span>
            </div>
            
            {/* State */}
            <div className="flex justify-between items-start pb-3">
              <span className="text-sm font-medium text-gray-700">State:</span>
              <span className="text-sm text-gray-900">{formData.state}</span>
            </div>
          </div>
        </div>

        {/* Document Information Section */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
            <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Documentation
          </h3>
          
          <div className="space-y-4">
            {/* ID Type */}
            <div className="flex justify-between items-start border-b border-green-100 pb-3">
              <span className="text-sm font-medium text-gray-700">ID Type:</span>
              <span className="text-sm text-gray-900">{ID_TYPE_LABELS[formData.id_type] || formData.id_type.replace(/_/g, ' ')}</span>
            </div>
            
            {/* ID Number */}
            <div className="flex justify-between items-start border-b border-green-100 pb-3">
              <span className="text-sm font-medium text-gray-700">ID Number:</span>
              <span className="text-sm text-gray-900">{formData.id_number}</span>
            </div>
            
            {/* ID Document */}
            <div className="flex justify-between items-start border-b border-green-100 pb-3">
              <span className="text-sm font-medium text-gray-700">ID Document:</span>
              <div className="text-right">
                <p className="text-sm text-gray-900">{documents.id_document?.name}</p>
                <p className="text-xs text-gray-500">{(documents.id_document?.size / 1024).toFixed(2)} KB</p>
              </div>
            </div>
            
            {/* Selfie */}
            <div className="flex justify-between items-start pb-3">
              <span className="text-sm font-medium text-gray-700">Selfie:</span>
              <div className="text-right">
                <p className="text-sm text-gray-900">{documents.selfie?.name}</p>
                <p className="text-xs text-gray-500">{(documents.selfie?.size / 1024).toFixed(2)} KB</p>
              </div>
            </div>
          </div>
        </div>

        {/* Information Box */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex gap-3">
            <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="text-sm text-yellow-800">
              <p className="font-medium mb-1">Please ensure all information is accurate</p>
              <p className="text-xs">Any false or misleading information may result in rejection of your KYC verification.</p>
            </div>
          </div>
        </div>

        {/* Terms & Conditions */}
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            id="acceptTerms"
            checked={acceptedTerms}
            onChange={(e) => {
              setAcceptedTerms(e.target.checked);
              if (error) setError('');
            }}
            className="mt-1 w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          />
          <label htmlFor="acceptTerms" className="text-sm text-gray-700">
            I confirm that all information provided is accurate and true. I understand that providing false information may result in account suspension or legal action. <span className="text-red-500">*</span>
          </label>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="pt-6 flex gap-3">
          <button
            type="button"
            onClick={onPrev}
            disabled={isLoading}
            className="flex-1 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900 font-medium py-3 px-4 rounded-lg transition duration-200"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={isLoading || !acceptedTerms}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition duration-200 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Submit KYC
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ReviewStep;
