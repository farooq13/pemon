import { useEffect, useRef, useState } from 'react';

const CameraCapture = ({ onCapture, onClose }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const initializingRef = useRef(false);
  const initializedRef = useRef(false);

  const [cameraActive, setCameraActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [error, setError] = useState('');
  const [isCapturing, setIsCapturing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Stop camera stream.
   */
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  /**
   * Start camera.
   */
  const initCamera = async () => {
    // Prevent multiple initializations
    if (initializingRef.current || streamRef.current) {
      return;
    }

    initializingRef.current = true;

    try {
      setError('');
      setIsLoading(true);

      // Check if video element exists BEFORE requesting camera
      if (!videoRef.current) {
        // Wait a bit more and check again
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (!videoRef.current) {
          throw new Error('Video element not found');
        }
      }


      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });

      streamRef.current = stream;

      // Check again if video element is still available (might have unmounted during async operation)
      if (!videoRef.current) {
        console.warn('Video element lost during camera request');
        // Stop the stream we just got
        stream.getTracks().forEach(track => track.stop());
        throw new Error('Video element not found');
      }

      // Attach stream
      videoRef.current.srcObject = stream;

      // Wait for video to load
      await new Promise((resolve, reject) => {
        const video = videoRef.current;
        if (!video) {
          reject(new Error('Video element lost'));
          return;
        }

        const timeout = setTimeout(() => {
          if (video.readyState >= 2) {
            resolve();
          } else {
            reject(new Error('Video load timeout'));
          }
        }, 5000);

        video.onloadedmetadata = () => {
          clearTimeout(timeout);
          resolve();
        };

        video.onerror = (err) => {
          clearTimeout(timeout);
          reject(err);
        };
      });

      // Play video
      await videoRef.current.play().catch(err => {
        console.warn('Autoplay blocked (ok):', err.message);
      });

      setCameraActive(true);
      setIsLoading(false);

    } catch (err) {
      error.message('Camera initialization failed:', err);
      
      let errorMessage = 'Unable to access camera';
      
      if (err.name === 'NotAllowedError') {
        errorMessage = 'Camera permission denied. Please allow camera access in your browser settings.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No camera found on this device.';
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'Camera is in use by another application.';
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      setIsLoading(false);
    } finally {
      initializingRef.current = false;
    }
  };

  /**
   * Capture photo.
   */
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera not ready');
      return;
    }

    try {
      setIsCapturing(true);
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (!video.videoWidth || !video.videoHeight) {
        throw new Error('Video not loaded');
      }

      // Set canvas size
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw video frame
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);

      // Convert to blob
      canvas.toBlob((blob) => {
        if (!blob) {
          setError('Failed to capture photo');
          setIsCapturing(false);
          return;
        }

        const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
        const preview = canvas.toDataURL('image/jpeg');

        setCapturedImage({ file, preview });
        setIsCapturing(false);
      }, 'image/jpeg', 0.95);

    } catch (err) {
      console.error('Capture error:', err);
      setError('Failed to capture photo: ' + err.message);
      setIsCapturing(false);
    }
  };

  /**
   * Retake photo.
   */
  const handleRetake = () => {
    setCapturedImage(null);
    setError('');
  };

  /**
   * Confirm and send photo.
   */
  const handleConfirm = () => {
    if (capturedImage?.file) {
      onCapture(capturedImage.file);
      onClose();
    }
  };

  /**
   * Retry camera initialization.
   */
  const handleRetry = () => {
    stopCamera();
    setError('');
    setCameraActive(false);
    setIsLoading(true);
    initializingRef.current = false;
    setTimeout(initCamera, 500);
  };

  /**
   * Initialize on mount.
   */
  useEffect(() => {
    let mounted = true;

    const init = async () => {
      // Prevent duplicate initialization in Strict Mode
      if (initializedRef.current) {
        return;
      }

      // Wait for refs to be attached
      let attempts = 0;
      while (attempts < 10 && mounted && !videoRef.current) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
      }

      if (!mounted) {
        return;
      }

      if (videoRef.current) {
        initializedRef.current = true;
        initCamera();
      } else {
        console.error('Video ref never became available');
        setError('Camera component initialization failed');
        setIsLoading(false);
      }
    };

    init();

    return () => {
      mounted = false;
      stopCamera();
      initializedRef.current = false;
    };
  }, []); // Only run once

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Take Selfie</h3>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition"
            type="button"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* Video element - always present */}
          <div className={cameraActive && !capturedImage && !error ? 'block' : 'hidden'}>
            <div className="space-y-4">
              <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                  style={{ transform: 'scaleX(-1)' }}
                />
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-48 h-48 border-4 border-green-400 rounded-full opacity-50"></div>
                </div>
              </div>

              <p className="text-sm text-gray-600 text-center">
                Position your face in the center and ensure good lighting
              </p>

              <button
                onClick={capturePhoto}
                disabled={isCapturing}
                type="button"
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
              >
                {isCapturing ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Capturing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
                    </svg>
                    Capture Photo
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && !error && !capturedImage && (
            <div className="flex flex-col items-center justify-center py-12">
              <svg className="animate-spin h-12 w-12 text-blue-600 mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-gray-600 font-medium">Initializing camera...</p>
              <p className="text-xs text-gray-500 mt-2">Please allow camera access when prompted</p>
            </div>
          )}

          {/* Preview View */}
          {capturedImage && (
            <div className="space-y-4">
              <div className="bg-gray-100 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
                <img
                  src={capturedImage.preview}
                  alt="Captured selfie"
                  className="w-full h-full object-cover"
                  style={{ transform: 'scaleX(-1)' }}
                />
              </div>

              <p className="text-sm text-gray-600 text-center">
                Make sure your face is clearly visible and well-lit
              </p>

              <div className="flex gap-3">
                <button
                  onClick={handleRetake}
                  type="button"
                  className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-900 font-semibold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Retake
                </button>
                <button
                  onClick={handleConfirm}
                  type="button"
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Confirm
                </button>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex gap-3">
                  <svg className="w-6 h-6 text-red-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-medium text-red-900 mb-2">{error}</p>
                    {error.includes('permission') && (
                      <p className="text-sm text-red-700 mb-4">
                        Check your browser settings to allow camera access.
                      </p>
                    )}
                    <div className="flex gap-2">
                      <button
                        onClick={handleRetry}
                        type="button"
                        className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded transition"
                      >
                        Try Again
                      </button>
                      <button
                        onClick={onClose}
                        type="button"
                        className="bg-gray-300 hover:bg-gray-400 text-gray-900 font-medium px-4 py-2 rounded transition"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hidden canvas for photo capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
};

export default CameraCapture;