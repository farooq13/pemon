import { useState } from 'react';
import { X, Download, Calendar } from 'lucide-react';
import transactionService from '../../services/transactionService';

/*
 * Modal for exporting transactions to CSV with date range selection.
 */
const ExportModal = ({ isOpen, onClose }) => {
  const [exporting, setExporting] = useState(false);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    type: '',
  });

  if (!isOpen) return null;

  const handleExport = async () => {
    setExporting(true);

    try {
      // Build export parameters
      const params = {};
      
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      if (filters.type) params.type = filters.type;

      await transactionService.exportTransactions(params);
      
      // Close modal after successful export
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (error) {
      alert('Failed to export transactions. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const transactionTypes = [
    { value: '', label: 'All Types' },
    { value: 'TRANSFER', label: 'Transfers' },
    { value: 'DEPOSIT', label: 'Deposits' },
    { value: 'WITHDRAWAL', label: 'Withdrawals' },
    { value: 'BILL_PAYMENT', label: 'Bill Payments' },
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-end sm:items-center justify-center p-0 sm:p-4">
        <div className="relative bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-2xl shadow-xl transform transition-all">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-2xl">
            <h3 className="text-lg font-bold text-gray-900">Export Transactions</h3>
            <button
              onClick={onClose}
              disabled={exporting}
              className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-6 space-y-6">
            {/* Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex gap-3">
                <Download className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">CSV Export</p>
                  <p>Download your transactions as a CSV file for use in Excel or other tools.</p>
                </div>
              </div>
            </div>

            {/* Date Range */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-gray-900">Date Range (Optional)</h4>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Start Date */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2">
                    From Date
                  </label>
                  <div className="relative">
                    <input
                      type="date"
                      value={filters.start_date}
                      onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                      max={filters.end_date || undefined}
                      className="w-full px-3 py-2 pl-9 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <Calendar className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  </div>
                </div>

                {/* End Date */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-2">
                    To Date
                  </label>
                  <div className="relative">
                    <input
                      type="date"
                      value={filters.end_date}
                      onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                      min={filters.start_date || undefined}
                      className="w-full px-3 py-2 pl-9 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <Calendar className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* Transaction Type Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-2">
                Transaction Type (Optional)
              </label>
              <select
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {transactionTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Export Details */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Format:</span>
                <span className="font-medium text-gray-900">CSV</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Includes:</span>
                <span className="font-medium text-gray-900">All fields</span>
              </div>
              {filters.start_date && filters.end_date && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Period:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(filters.start_date).toLocaleDateString()} - {new Date(filters.end_date).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 space-y-3 rounded-b-2xl">
            <button
              onClick={handleExport}
              disabled={exporting}
              className={`
                w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-white transition
                ${exporting 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700'
                }
              `}
            >
              <Download className="w-5 h-5" />
              {exporting ? 'Exporting...' : 'Export to CSV'}
            </button>

            <button
              onClick={onClose}
              disabled={exporting}
              className="w-full py-3 text-gray-700 font-medium hover:bg-gray-50 rounded-lg transition disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;