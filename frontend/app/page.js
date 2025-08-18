'use client';

import { useState } from 'react';
import CaseUpload from '../components/CaseUpload';
import CasesList from '../components/CasesList';

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedCase, setSelectedCase] = useState(null);

  const handleCaseCreated = (newCase) => {
    console.log('New case created:', newCase);
    // Trigger refresh of cases list
    setRefreshTrigger(prev => prev + 1);
  };

  const handleCaseSelect = (caseItem) => {
    setSelectedCase(caseItem);
    // You can add navigation to case detail page here
    console.log('Selected case:', caseItem);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🏗️ Construction RAG System
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Backend: http://127.0.0.1:8000
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Case Upload */}
          <div>
            <CaseUpload onCaseCreated={handleCaseCreated} />
          </div>

          {/* Right Column - Cases List */}
          <div>
            <CasesList 
              refreshTrigger={refreshTrigger}
              onCaseSelect={handleCaseSelect}
            />
          </div>
        </div>

        {/* Selected Case Info */}
        {selectedCase && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              Selected Case: {selectedCase.id}
            </h3>
            <p className="text-blue-700">
              Click on a case to view details. Case detail page coming soon!
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
