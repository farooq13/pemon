import { useState } from 'react';
import CameraCapture from './CameraCapture';

const DocumentsStep = ({ formData, documents, onFormDataChange, onDocumentsChange, onNext, onPrev, serverErrors = {}, clearServerError = () => {} }) => {
  const [fieldErrors, setFieldErrors] = useState({});
  const [dragActive, setDragActive] = useState({});
  const [showCamera, setShowCamera] = useState(false);

  /**
   * Handle camera capture callback.
   */
  const handleCameraCapture = (file) => {
    onDocumentsChange({
      ...documents,
      selfie: file,
    });
  };

  /**
   * Handle ID type change.
   */
  const handleIDTypeChange = (e) => {
    const { value } = e.target;
    onFormDataChange({
      ...formData,
      id_type: value,
    });
    
    // Clear local and server-side errors when user selects
    if (fieldErrors.id_type) {
      setFieldErrors({ ...fieldErrors, id_type: null });
    }
    if (serverErrors?.id_type) clearServerError('id_type');
  };

  /**
   * Handle ID number input.
   */
  const handleIDNumberChange = (e) => {
    const { value } = e.target;
    onFormDataChange({
      ...formData,
      id_number: value,
    });
    
    if (fieldErrors.id_number) {
      setFieldErrors({ ...fieldErrors, id_number: null });
    }
    if (serverErrors?.id_number) clearServerError('id_number');
  };

  /**
   * Handle file selection from input.
   */
  const handleFileSelect = (e, fileType) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file, fileType);
    }
  };

  /**
   * Handle drag over.
   */
  const handleDrag = (e, fileType) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive({ ...dragActive, [fileType]: true });
    } else if (e.type === 'dragleave') {
      setDragActive({ ...dragActive, [fileType]: false });
    }
  };

  /**
   * Handle file drop.
   */
  const handleDrop = (e, fileType) => {
    e.preventDefault();
    e.stopPropagation();
    
    setDragActive({ ...dragActive, [fileType]: false });
    
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      processFile(file, fileType);
    }
  };

  /**
   * Validate and process file.
   */
  const processFile = (file, fileType) => {
    const errors = { ...fieldErrors };
    
    // Check file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      errors[fileType] = 'File size must be less than 5MB';
      setFieldErrors(errors);
      return;
    }
    
    // Check file type
    const validTypes = fileType === 'selfie'
      ? ['image/jpeg', 'image/png', 'image/webp']
      : ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
    
    if (!validTypes.includes(file.type)) {
      errors[fileType] = fileType === 'selfie'
        ? 'Only JPG, PNG, or WebP images are allowed'
        : 'Only JPG, PNG, WebP, or PDF files are allowed';
      setFieldErrors(errors);
      return;
    }
    
    // Clear any previous error for this field
    if (errors[fileType]) {
      delete errors[fileType];
      setFieldErrors(errors);
    }

    // Clear any server-side error for this file field
    if (serverErrors?.[fileType]) clearServerError(fileType);
    
    // Update documents
    onDocumentsChange({
      ...documents,
      [fileType]: file,
    });
  };

  /**
   * Remove uploaded file.
   */
  const removeFile = (fileType) => {
    onDocumentsChange({
      ...documents,
      [fileType]: null,
    });
    
    // Clear error
    if (fieldErrors[fileType]) {
      setFieldErrors({ ...fieldErrors, [fileType]: null });
    }
    if (serverErrors?.[fileType]) clearServerError(fileType);
  };

  /**
   * Get file preview text.
   */
  const getFilePreview = (file) => {
    if (!file) return null;
    
    return (
      <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="text-sm font-medium text-green-900">{file.name}</p>
            <p className="text-xs text-green-700">{(file.size / 1024).toFixed(2)} KB</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => removeFile(file === documents.id_document ? 'id_document' : 'selfie')}
          className="text-red-600 hover:text-red-700 font-medium text-sm"
        >
          Remove
        </button>
      </div>
    );
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    const errors = {};
    
    // Validate ID type
    if (!formData.id_type) {
      errors.id_type = 'Please select an ID type';
    }
    
    // Validate ID number
    if (!formData.id_number.trim()) {
      errors.id_number = 'ID number is required';
    }
    
    // Validate ID document
    if (!documents.id_document) {
      errors.id_document = 'Please upload your ID document';
    }
    
    // Validate selfie
    if (!documents.selfie) {
      errors.selfie = 'Please upload a selfie photo';
    }
    
    // If there are errors, display them
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    
    // All validations passed
    onNext();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Documents</h2>
        <p className="text-gray-600">Please upload your ID and a clear selfie for verification</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* ID Type */}
        <div>
          <label htmlFor="id_type" className="block text-sm font-medium text-gray-700 mb-2">
            ID Document Type <span className="text-red-500">*</span>
          </label>
          <select
            id="id_type"
            value={formData.id_type}
            onChange={handleIDTypeChange}
            className={`w-full px-4 py-3 rounded-lg border ${
              (fieldErrors.id_type || serverErrors?.id_type)
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition`}
          >
            <option value="">Select an ID type</option>
            <option value="INTERNATIONAL_PASSPORT">Passport</option>
            <option value="DRIVERS_LICENSE">Driver's License</option>
            <option value="NIN">National ID Card</option>
            <option value="VOTERS_CARD">Voter's Card</option>
          </select>
          {(fieldErrors.id_type || serverErrors?.id_type) && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.id_type || serverErrors.id_type?.[0]}</p>
          )}
        </div>

        {/* ID Number */}
        <div>
          <label htmlFor="id_number" className="block text-sm font-medium text-gray-700 mb-2">
            ID Document Number <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="id_number"
            value={formData.id_number}
            onChange={handleIDNumberChange}
            placeholder="Enter the ID document number"
            className={`w-full px-4 py-3 rounded-lg border ${
              fieldErrors.id_number
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-white'
            } focus:ring-2 focus:ring-blue-500 focus:border-transparent transition placeholder:text-gray-500`}
          />
          {(fieldErrors.id_number || serverErrors?.id_number) && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.id_number || serverErrors.id_number?.[0]}</p>
          )}
        </div>

        {/* ID Document Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            ID Document <span className="text-red-500">*</span>
          </label>
          
          {documents.id_document ? (
            getFilePreview(documents.id_document)
          ) : (
            <div
              onDragEnter={(e) => handleDrag(e, 'id_document')}
              onDragLeave={(e) => handleDrag(e, 'id_document')}
              onDragOver={(e) => handleDrag(e, 'id_document')}
              onDrop={(e) => handleDrop(e, 'id_document')}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
                dragActive.id_document
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 bg-gray-50 hover:border-blue-400'
              }`}
            >
              <input
                type="file"
                id="id_document"
                onChange={(e) => handleFileSelect(e, 'id_document')}
                accept=".jpg,.jpeg,.png,.webp,.pdf"
                className="hidden"
              />
              <label htmlFor="id_document" className="cursor-pointer">
                <svg className="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
                </svg>
                <p className="text-sm font-medium text-gray-700 mb-1">
                  Drag and drop your ID or click to upload
                </p>
                <p className="text-xs text-gray-500">
                  Supported formats: JPG, PNG, WebP, PDF (Max 5MB)
                </p>
              </label>
            </div>
          )}
          
          {(fieldErrors.id_document || serverErrors?.id_document) && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.id_document || serverErrors.id_document?.[0]}</p>
          )}
        </div>

        {/* Selfie Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Selfie Photo <span className="text-red-500">*</span>
          </label>
          
          {documents.selfie ? (
            getFilePreview(documents.selfie)
          ) : (
            <button
              type="button"
              onClick={() => setShowCamera(true)}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-4 rounded-lg transition flex items-center justify-center gap-3 border-2 border-blue-600"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
              </svg>
              <div className="text-left">
                <div className="font-semibold">Take Selfie with Camera</div>
                <div className="text-xs opacity-90">Click to open your device camera</div>
              </div>
            </button>
          )}
          
          {(fieldErrors.selfie || serverErrors?.selfie) && (
            <p className="mt-2 text-sm text-red-600">{fieldErrors.selfie || serverErrors.selfie?.[0]}</p>
          )}
          <p className="mt-2 text-xs text-gray-500">
            ℹ️ A clear photo of your face is required for verification
          </p>
        </div>

        {/* Navigation Buttons */}
        <div className="pt-6 flex gap-3">
          <button
            type="button"
            onClick={onPrev}
            className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium py-3 px-4 rounded-lg transition duration-200"
          >
            Back
          </button>
          <button
            type="submit"
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition duration-200"
          >
            Review & Submit
          </button>
        </div>
      </form>

      {/* Camera Capture Modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}
    </div>
  );
};

export default DocumentsStep;
