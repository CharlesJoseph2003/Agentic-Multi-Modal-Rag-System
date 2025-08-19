'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';

export default function CasesList({ refreshTrigger, onCaseSelect, isSidebar = false }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingCaseId, setDeletingCaseId] = useState(null);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getCases(20, 0);
      setCases(response.cases || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch cases');
      console.error('Error fetching cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [refreshTrigger]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDeleteCase = async (caseId, event) => {
    event.stopPropagation(); // Prevent case selection when clicking delete
    
    if (!confirm('Are you sure you want to delete this case? This will permanently remove all files, data, and tasks associated with this case.')) {
      return;
    }

    try {
      setDeletingCaseId(caseId);
      await apiClient.deleteCase(caseId);
      
      // Remove the case from the local state
      setCases(prevCases => prevCases.filter(c => c.id !== caseId));
      
      // Show success message
      alert('Case deleted successfully');
    } catch (error) {
      console.error('Error deleting case:', error);
      alert('Failed to delete case. Please try again.');
    } finally {
      setDeletingCaseId(null);
    }
  };

  if (loading) {
    return (
      <div className={isSidebar ? "p-4" : "bg-white rounded-lg shadow-md p-6"}>
        {!isSidebar && <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Cases</h2>}
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600 text-sm">Loading cases...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={isSidebar ? "p-4" : "bg-white rounded-lg shadow-md p-6"}>
        {!isSidebar && <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Cases</h2>}
        <div className="text-center py-4">
          <div className="text-red-600 mb-2 text-sm">{error}</div>
          <button
            onClick={fetchCases}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={isSidebar ? "" : "bg-white rounded-lg shadow-md p-6"}>
      {!isSidebar && (
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">Recent Cases</h2>
          <button
            onClick={fetchCases}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
          >
            Refresh
          </button>
        </div>
      )}

      {cases.length === 0 ? (
        <div className="text-center py-4 text-gray-500 text-sm">
          No cases found. {isSidebar ? "Click + to create one!" : "Create your first case above!"}
        </div>
      ) : (
        <div className={`${isSidebar ? "space-y-1" : "space-y-3"}`}>
          {cases.map((case_item) => (
            <div
              key={case_item.id}
              className={`${isSidebar 
                ? "border-b border-gray-100 p-3 hover:bg-gray-50 cursor-pointer transition-colors" 
                : "border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"}`}
              onClick={() => onCaseSelect && onCaseSelect(case_item)}
            >
              {isSidebar ? (
                // Enhanced sidebar view
                <div className="flex flex-col p-2">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-gray-800 text-base truncate">
                      Case {case_item.id.substring(0, 8)}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">
                        Active
                      </span>
                      <button
                        onClick={(e) => handleDeleteCase(case_item.id, e)}
                        disabled={deletingCaseId === case_item.id}
                        className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                        title="Delete case"
                      >
                        {deletingCaseId === case_item.id ? (
                          <div className="animate-spin h-3 w-3 border border-red-500 border-t-transparent rounded-full"></div>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600 mt-2">
                    {new Date(case_item.created_at).toLocaleDateString()}
                  </div>
                  
                  <div className="flex gap-3 mt-3 items-center">
                    {case_item.files && (
                      <>
                        <div className="flex items-center text-sm text-blue-600">
                          <span className="bg-blue-50 p-1.5 rounded-md mr-1.5">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                            </svg>
                          </span>
                          <span>{case_item.files.filter(f => f.file_type === 'document').length}</span>
                        </div>
                        
                        <div className="flex items-center text-sm text-purple-600">
                          <span className="bg-purple-50 p-1.5 rounded-md mr-1.5">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                            </svg>
                          </span>
                          <span>{case_item.files.filter(f => f.file_type === 'audio').length}</span>
                        </div>
                        
                        <div className="flex items-center text-sm text-green-600">
                          <span className="bg-green-50 p-1.5 rounded-md mr-1.5">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                            </svg>
                          </span>
                          <span>{case_item.files.filter(f => f.file_type === 'image').length}</span>
                        </div>
                      </>
                    )}
                    {case_item.tasks && case_item.tasks.length > 0 && (
                      <div className="flex items-center text-sm text-amber-600">
                        <span className="bg-amber-50 p-1.5 rounded-md mr-1.5">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </span>
                        <span>{case_item.tasks.length}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                // Original full view
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium text-gray-800">Case ID:</span>
                      <span className="text-blue-600 font-mono text-sm">{case_item.id}</span>
                    </div>
                    
                    <div className="text-sm text-gray-600 mb-2">
                      Created: {formatDate(case_item.created_at)}
                    </div>
                    
                    <div className="flex gap-4 text-sm">
                      {case_item.files && (
                        <>
                          <span className="text-gray-500">
                            📄 {case_item.files.filter(f => f.file_type === 'document').length} docs
                          </span>
                          <span className="text-gray-500">
                            🎵 {case_item.files.filter(f => f.file_type === 'audio').length} audio
                          </span>
                          <span className="text-gray-500">
                            🖼️ {case_item.files.filter(f => f.file_type === 'image').length} images
                          </span>
                        </>
                      )}
                      {case_item.tasks && (
                        <span className="text-gray-500">
                          ✅ {case_item.tasks.length} tasks
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right flex items-center gap-2">
                    <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                      Active
                    </span>
                    <button
                      onClick={(e) => handleDeleteCase(case_item.id, e)}
                      disabled={deletingCaseId === case_item.id}
                      className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                      title="Delete case"
                    >
                      {deletingCaseId === case_item.id ? (
                        <div className="animate-spin h-4 w-4 border border-red-500 border-t-transparent rounded-full"></div>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {isSidebar && (
        <div className="p-3 mt-2">
          <button
            onClick={fetchCases}
            className="w-full px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 flex items-center justify-center gap-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Cases
          </button>
        </div>
      )}
    </div>
  );
}
