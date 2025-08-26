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
  const [showCaseUpload, setShowCaseUpload] = useState(false);

  const handleCaseCreated = (newCase) => {
    console.log('New case created:', newCase);
    // Trigger refresh of cases list
    setRefreshTrigger(prev => prev + 1);
    setShowCaseUpload(false);
  };

  const handleCaseDeleted = (deletedCaseId) => {
    console.log('Case deleted:', deletedCaseId);
    // Trigger refresh of cases list to ensure consistency
    setRefreshTrigger(prev => prev + 1);
    // If the deleted case was selected, clear the selection
    if (selectedCase && selectedCase.id === deletedCaseId) {
      setSelectedCase(null);
      setShowCaseDetail(false);
    }
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
  
  const handleNewCaseClick = () => {
    setShowCaseUpload(true);
    setShowCaseDetail(false);
    setSelectedCase(null);
  };

  return (
    <div className="h-screen bg-gray-100 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-white shadow-md border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <div className="bg-gradient-to-br from-blue-500 to-blue-700 text-white p-2 rounded-xl mr-3 shadow-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <span>Chaero</span>
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm bg-green-50 text-green-700 px-3 py-1 rounded-full font-medium">
                Connected to Backend
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Sidebar Layout */}
      <div className="flex flex-1 overflow-hidden h-[calc(100vh-64px)]">
        {/* Left Sidebar - Cases List */}
        <div className="w-80 bg-white flex flex-col shadow-lg z-5">
          {/* Sidebar Header with Plus Button */}
          <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-gradient-to-r from-blue-50 to-white flex-shrink-0">
            <h2 className="font-bold text-gray-800 text-lg">Cases</h2>
            <button 
              onClick={handleNewCaseClick}
              className="p-2 rounded-full bg-blue-600 text-white hover:bg-blue-700 flex items-center justify-center shadow-sm transition-all duration-200 hover:shadow"
              title="Create new case"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          
          {/* Cases List */}
          <div className="flex-1 overflow-y-auto bg-gradient-to-b from-white to-gray-50 min-h-0">
            <CasesList 
              refreshTrigger={refreshTrigger}
              onCaseSelect={handleCaseSelect}
              onCaseDeleted={handleCaseDeleted}
              isSidebar={true}
            />
          </div>
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden bg-gray-50">
          {showCaseDetail && selectedCase ? (
            <div className="p-6 h-full overflow-y-auto">
              <CaseDetailView 
                caseId={selectedCase.id}
                onBack={handleBackToCases}
              />
            </div>
          ) : showCaseUpload ? (
            <div className="p-8 max-w-4xl mx-auto">
              <CaseUpload onCaseCreated={handleCaseCreated} />
            </div>
          ) : (
            <div className="h-full flex flex-col p-6">
              {/* Chat Interface */}
              <div className="flex-1 overflow-hidden max-w-5xl mx-auto w-full">
                <div className="bg-white rounded-xl shadow-md h-full flex flex-col border border-gray-200">
                  <div className="p-5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
                    <div className="flex items-center">
                      <div className="bg-blue-100 p-2 rounded-lg mr-3">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="font-bold text-gray-800 text-lg">Global Search Chat</h2>
                        <p className="text-sm text-gray-600">Search across all documents</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <ChatInterface caseId={null} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
