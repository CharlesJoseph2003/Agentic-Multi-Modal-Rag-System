'use client';

import { useState } from 'react';
import CaseUpload from '../components/CaseUpload';
import CasesList from '../components/CasesList';
import CaseDetailView from '../components/CaseDetailView';
import ChatInterface from '../components/ChatInterface';

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedCase, setSelectedCase] = useState(null);
  const [showCaseDetail, setShowCaseDetail] = useState(false);

  const handleCaseCreated = (newCase) => {
    console.log('New case created:', newCase);
    // Trigger refresh of cases list
    setRefreshTrigger(prev => prev + 1);
  };

  const handleCaseSelect = (caseItem) => {
    setSelectedCase(caseItem);
    setShowCaseDetail(true);
    console.log('Selected case:', caseItem);
  };

  const handleBackToCases = () => {
    setShowCaseDetail(false);
    setSelectedCase(null);
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
        {showCaseDetail && selectedCase ? (
          <CaseDetailView 
            caseId={selectedCase.id}
            onBack={handleBackToCases}
          />
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* Left Column - Case Upload */}
            <div>
              <CaseUpload onCaseCreated={handleCaseCreated} />
            </div>

            {/* Middle Column - Cases List */}
            <div>
              <CasesList 
                refreshTrigger={refreshTrigger}
                onCaseSelect={handleCaseSelect}
              />
            </div>

            {/* Right Column - Global Chat */}
            <div>
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                  <h2 className="font-semibold text-gray-800">💬 Global Search Chat</h2>
                  <p className="text-sm text-gray-600">Search across all cases</p>
                </div>
                <div className="p-4">
                  <ChatInterface caseId={null} />
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
