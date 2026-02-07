import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getFieldErrors } from '../services/api';
import ProgressBar from '../components/kyc/ProgressBar';
import PersonalInfoStep from '../components/kyc/PersonalInfoStep';
import DocumentsStep from '../components/kyc/DocumentsStep';
import ReviewStep from '../components/kyc/ReviewStep';
import kycService from '../services/kycService';

const KYC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Current step (0 = personal info, 1 = documents, 2 = review)
  const [currentStep, setCurrentStep] = useState(0);

  // Steps for progress bar
  const steps = [
    { label: 'Personal Info' },
    { label: 'Documents' },
    { label: 'Review' },
  ];

  // Form data
  const [formData, setFormData] = useState({
    bvn: '',
    nin: '',
    date_of_birth: '',
    address: '',
    city: '',
    state: '',
    id_type: '',
    id_number: '',
  });

  // Document files
  const [documents, setDocuments] = useState({
    id_document: null,
    selfie: null,
  });

  // UI state
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [fieldValidationErrors, setFieldValidationErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const [showSuccessScreen, setShowSuccessScreen] = useState(false);

  /*
   * Check if user already has approved KYC.
   */
  useEffect(() => {
    const checkKYCStatus = async () => {
      try {
        const status = await kycService.getStatus();
        
        // If already approved, redirect to dashboard
        if (status.status === 'approved') {
          navigate('/dashboard', {
            state: {
              message: 'Your KYC is already approved!',
            },
          });
          return;
        }
        
        // If pending, show message
        if (status.status === 'pending') {
          setError('Your KYC is already pending review. Please wait for approval.');
        }
      } catch (err) {
        // User might not have KYC yet, which is fine
        err.message
        ('No existing KYC found, allowing new submission');
      } finally {
        setLoading(false);
      }
    };

    checkKYCStatus();
  }, [navigate]);

  /**
   * Handle form data changes.
   */
  const handleFormDataChange = (newData) => {
    setFormData(newData);
    if (error) setError('');
  };

  /**
   * Handle document changes.
   */
  const handleDocumentsChange = (newDocuments) => {
    setDocuments(newDocuments);
    if (error) setError('');
  };

  /**
   * Clear a specific server-side field error (when user edits a field).
   */
  const clearServerFieldError = (field) => {
    setFieldValidationErrors((prev) => {
      if (!prev || !prev[field]) return prev;
      const copy = { ...prev };
      delete copy[field];
      return copy;
    });
    if (error) setError('');
  };

  /**
   * Move to next step.
   */
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
      window.scrollTo(0, 0);
    }
  };

  /**
   * Move to previous step.
   */
  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      window.scrollTo(0, 0);
    }
  };

  /**
   * Submit KYC form.
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    setFieldValidationErrors({});

    try {
      const response = await kycService.submitKYC(
        formData,
        documents.id_document,
        documents.selfie
      );

      if (response.message) {
        setSuccessMessage(response.message);
      }

      // Show success screen for 3 seconds then redirect
      setShowSuccessScreen(true);
      setTimeout(() => {
        navigate('/dashboard', {
          state: {
            message: 'Your KYC verification is under review. We\'ll notify you once it\'s approved.',
          },
        });
      }, 3000);
    } catch (err) {
      // Default error message
      let errorMessage = err?.message || 'Failed to submit KYC. Please try again.';

      // Try to extract structured field errors first
      if (err?.response?.data) {
        // Check for business logic error from backend (like "KYC already pending")
        const businessError = err?.response?.data?.error?.message || err?.response?.data?.detail;
        if (businessError && typeof businessError === 'string') {
          errorMessage = businessError;
        } else {
          // Try parsing field-specific validation errors
          const fieldErrors = getFieldErrors(err);

          if (Object.keys(fieldErrors).length > 0) {
            setFieldValidationErrors(fieldErrors);
            const errorMessages = [];
            for (const [field, messages] of Object.entries(fieldErrors)) {
              const msg = Array.isArray(messages) ? messages[0] : messages;
              errorMessages.push(`${field}: ${msg}`);
            }
            errorMessage = `Validation error: ${errorMessages.join('. ')}`;
          } else {
            // Handle unstructured DRF validation strings like:
            // "Validation error: id_type: "national_id_card" is not a valid choice."
            const raw = err?.response?.data?.detail || err?.response?.data?.message || err?.response?.data;
            const text = typeof raw === 'string' ? raw : String(raw);
            const match = text.match(/Validation error:\s*(\w+):\s*"([^"]+)"\s*is not a valid choice/i);
            if (match) {
              const field = match[1];
              const value = match[2];
              const ID_TYPE_LABELS = {
                passport: 'Passport',
                driver_license: "Driver's License",
                national_id_card: 'National ID Card',
                voters_card: "Voter's Card",
              };
              const prettyValue = ID_TYPE_LABELS[value] || value;
              const msg = `${prettyValue} is not a valid choice`;
              setFieldValidationErrors({ [field]: [msg] });
              errorMessage = `Validation error: ${field}: ${msg}`;
            }
          }
        }
      }

      setError(errorMessage);
      window.scrollTo(0, 0);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center mb-4">
            <svg className="animate-spin h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show success screen
  if (showSuccessScreen) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-2xl p-8 text-center">
            {/* Success Icon */}
            <div className="mb-6 flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-green-100 rounded-full animate-ping opacity-75"></div>
                <div className="relative bg-green-100 rounded-full p-4">
                  <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Title */}
            <h2 className="text-2xl font-bold text-gray-900 mb-2">KYC Submitted Successfully! 🎉</h2>

            {/* Message */}
            <p className="text-gray-600 mb-2">
              Your Know Your Customer verification has been submitted.
            </p>
            <p className="text-gray-500 text-sm mb-6">
              Our team will review your information and documents. You'll receive an email notification once your verification is approved.
            </p>

            {/* What's Next */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold text-blue-900 mb-2">What's Next?</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>✓ We'll verify your information within 24-48 hours</li>
                <li>✓ Check your email for updates</li>
                <li>✓ You'll be able to increase transaction limits once approved</li>
              </ul>
            </div>

            {/* Countdown */}
            <p className="text-gray-500 text-xs mb-6">
              Redirecting to dashboard in <span className="font-semibold text-gray-700">3 seconds</span>...
            </p>

            {/* Button */}
            <button
              onClick={() =>
                navigate('/dashboard', {
                  state: {
                    message: 'Your KYC verification is under review. We\'ll notify you once it\'s approved.',
                  },
                })
              }
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900 p-2 rounded-lg hover:bg-gray-100 transition"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-blue-600">Pemon KYC</h1>
              <p className="text-sm text-gray-600">Verify your identity</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <svg className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p className="text-green-600 text-sm">{successMessage}</p>
          </div>
        )}

        {/* Form Container */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Progress Bar */}
          <ProgressBar currentStep={currentStep} steps={steps} />

          {/* Form Content */}
          <div className="mt-8">
            {currentStep === 0 && (
              <PersonalInfoStep
                formData={formData}
                onFormDataChange={handleFormDataChange}
                onNext={handleNext}
                serverErrors={fieldValidationErrors}
                clearServerError={clearServerFieldError}
              />
            )}

            {currentStep === 1 && (
              <DocumentsStep
                formData={formData}
                documents={documents}
                onFormDataChange={handleFormDataChange}
                onDocumentsChange={handleDocumentsChange}
                onNext={handleNext}
                onPrev={handlePrev}
                serverErrors={fieldValidationErrors}
                clearServerError={clearServerFieldError}
              />
            )}

            {currentStep === 2 && (
              <ReviewStep
                formData={formData}
                documents={documents}
                onSubmit={handleSubmit}
                onPrev={handlePrev}
                isLoading={submitting}
                serverErrors={fieldValidationErrors}
              />
            )}
          </div>
        </div>

        {/* Info Box */}
        <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex gap-4">
            <svg className="w-6 h-6 text-blue-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Why do we need KYC?</h3>
              <p className="text-sm text-gray-700">
                KYC (Know Your Customer) verification helps us comply with regulatory requirements and protects both you and our platform from fraudulent activities. Once verified, you'll be able to enjoy full access to all Pemon features with higher transaction limits.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default KYC;
