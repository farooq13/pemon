import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Search, X, Download } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import transactionService from '../services/transactionService';
import useDebounce from '../hooks/useDebounce';
import TransactionList from '../components/transactions/TransactionList';
import TransactionFilters from '../components/transactions/TransactionFilters';
import Pagination from '../components/transactions/Pagination';
import TransactionReceipt from '../components/transactions/TransactionReceipt';
import ExportModal from '../components/transactions/ExportModal';


const Transactions = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const itemsPerPage = 20;

  // Filters
  const [filters, setFilters] = useState({
    type: '',
    status: '',
    start_date: '',
    end_date: '',
  });

  // Search
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  // Modals
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);

  // Fetch transactions
  useEffect(() => {
    fetchTransactions();
  }, [currentPage, debouncedSearch, filters]);

  const fetchTransactions = async () => {
    setLoading(true);
    setError('');

    try {
      const params = {
        page: currentPage,
        page_size: itemsPerPage,
        search: debouncedSearch,
        ...filters,
      };

      // Remove empty filter values
      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key];
      });

      const response = await transactionService.getTransactions(params);
      
      setTransactions(response.data);
      
      // Calculate pagination from response
      if (response.count !== undefined) {
        setTotalCount(response.count);
        setTotalPages(Math.ceil(response.count / itemsPerPage));
      }
    } catch (err) {
      console.error('Failed to fetch transactions:', err);
      setError('Failed to load transactions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page
  };

  const handleClearFilters = () => {
    setFilters({
      type: '',
      status: '',
      start_date: '',
      end_date: '',
    });
    setSearchTerm('');
    setCurrentPage(1);
  };

  const handleTransactionClick = (transaction) => {
    setSelectedTransaction(transaction);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 text-gray-700 hover:text-gray-900 hover:cursor-pointer"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="font-medium hidden sm:inline">Back</span>
            </button>

            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              Transactions
            </h1>

            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition"
            >
              <Download className="w-4 h-4 hover:cursor-pointer" />
              <span className="hidden sm:inline hover:cursor-pointer">Export</span>
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by reference, recipient, or description..."
              className="w-full px-4 py-3 pl-11 pr-11 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
            />
            
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Filters */}
      <TransactionFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onClear={handleClearFilters}
      />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        {/* Error Message */}
        {error && (
          <div className="mx-4 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{error}</p>
            <button
              onClick={fetchTransactions}
              className="text-red-700 text-sm underline mt-1"
            >
              Try again
            </button>
          </div>
        )}

        {/* Transaction List */}
        <div className="mt-0">
          <TransactionList
            transactions={transactions}
            loading={loading}
            onTransactionClick={handleTransactionClick}
            currentUserEmail={user?.email}
          />
        </div>

        {/* Pagination */}
        {!loading && Array.isArray(transactions) && transactions.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalCount}
            itemsPerPage={itemsPerPage}
            onPageChange={handlePageChange}
          />
        )}
      </main>

      {/* Transaction Receipt Modal */}
      {selectedTransaction && (
        <TransactionReceipt
          transaction={selectedTransaction}
          isOpen={!!selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
};

export default Transactions;