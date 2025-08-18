'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';

export default function CasesList({ refreshTrigger, onCaseSelect }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Cases</h2>
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading cases...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Cases</h2>
        <div className="text-center py-8">
          <div className="text-red-600 mb-2">{error}</div>
          <button
            onClick={fetchCases}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Recent Cases</h2>
        <button
          onClick={fetchCases}
          className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
        >
          Refresh
        </button>
      </div>

      {cases.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No cases found. Create your first case above!
        </div>
      ) : (
        <div className="space-y-3">
          {cases.map((case_item) => (
            <div
              key={case_item.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onCaseSelect && onCaseSelect(case_item)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-gray-800">Case ID:</span>
                    <span className="text-blue-600 font-mono text-sm">{case_item.id}</span>
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-2">
                    Created: {formatDate(case_item.created_at)}
                  </div>
                  
                  {case_item.files && (
                    <div className="flex gap-4 text-sm">
                      <span className="text-gray-500">
                        📄 {case_item.files.filter(f => f.file_type === 'document').length} docs
                      </span>
                      <span className="text-gray-500">
                        🎵 {case_item.files.filter(f => f.file_type === 'audio').length} audio
                      </span>
                      <span className="text-gray-500">
                        🖼️ {case_item.files.filter(f => f.file_type === 'image').length} images
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="text-right">
                  <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                    Active
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
