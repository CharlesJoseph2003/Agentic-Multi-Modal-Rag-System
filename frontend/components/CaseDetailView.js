'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';

export default function CaseDetailView({ caseId, onBack }) {
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('documents');

  useEffect(() => {
    if (caseId) {
      fetchCaseDetails();
    }
  }, [caseId]);

  const fetchCaseDetails = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getCaseDetails(caseId);
      console.log('DEBUG: Case data received:', data);
      console.log('DEBUG: Documents array:', data.files?.documents);
      setCaseData(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch case details');
      console.error('Error fetching case details:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading case details...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">{error}</div>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 mr-2"
          >
            Back to Cases
          </button>
          <button
            onClick={fetchCaseDetails}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!caseData) return null;

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex space-x-2 mb-4">
              <button
                onClick={onBack}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
              >
                ← Back to Cases
              </button>
              <button
                onClick={() => {
                  // First go back to cases, then the main page logic will show the chat
                  onBack();
                }}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
                Return to Chat
              </button>
            </div>
            <h1 className="text-2xl font-bold text-gray-800">Case Details</h1>
            <p className="text-blue-600 font-mono text-sm mt-1">{caseData.case.id}</p>
            <p className="text-gray-600 text-sm">Created: {formatDate(caseData.case.created_at)}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {['documents', 'audio', 'images', 'tasks'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'documents' && (
          <div className="space-y-4">
            {caseData.files.document.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No documents found</p>
            ) : (
              caseData.files.document.map((doc, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-800">{doc.filename}</h3>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(doc.file_size)} • {formatDate(doc.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <a
                        href={`http://127.0.0.1:8000/download/${doc.id}`}
                        download={doc.filename}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700"
                      >
                        Download PDF
                      </a>
                      {doc.total_chunks && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                          {doc.total_chunks} chunks
                        </span>
                      )}
                    </div>
                  </div>
                  {doc.content && (
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700">
                      <p className="font-medium mb-2">Content Preview:</p>
                      <p className="whitespace-pre-wrap">{doc.content}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'audio' && (
          <div className="space-y-4">
            {caseData.files.audio.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No audio files found</p>
            ) : (
              caseData.files.audio.map((audio, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-800">{audio.filename}</h3>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(audio.file_size)} • {formatDate(audio.created_at)}
                      </p>
                    </div>
                    <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                      Audio
                    </span>
                  </div>
                  
                  {/* Audio Player */}
                  <div className="mb-4">
                    <audio 
                      controls 
                      className="w-full"
                      preload="metadata"
                    >
                      <source src={`http://127.0.0.1:8000/audio/${audio.id}`} type="audio/mpeg" />
                      <source src={`http://127.0.0.1:8000/audio/${audio.id}`} type="audio/mp4" />
                      <source src={`http://127.0.0.1:8000/audio/${audio.id}`} type="audio/wav" />
                      Your browser does not support the audio element.
                    </audio>
                  </div>

                  {audio.content && (
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700">
                      <p className="font-medium mb-2">Transcription:</p>
                      <p className="whitespace-pre-wrap">{audio.content}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'images' && (
          <div className="space-y-4">
            {caseData.files.image.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No images found</p>
            ) : (
              caseData.files.image.map((image, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-800">{image.filename}</h3>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(image.file_size)} • {formatDate(image.created_at)}
                      </p>
                    </div>
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                      Image
                    </span>
                  </div>
                  
                  {/* Image Preview */}
                  <div className="mb-4">
                    <img 
                      src={`http://127.0.0.1:8000/image/${image.id}`}
                      alt={image.filename}
                      className="max-w-full h-auto rounded-lg shadow-sm border border-gray-200"
                      style={{ maxHeight: '400px' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'block';
                      }}
                    />
                    <div className="hidden text-center py-8 text-gray-500">
                      <p>Unable to load image preview</p>
                      <p className="text-sm">File: {image.filename}</p>
                    </div>
                  </div>

                  {image.content && (
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700">
                      <p className="font-medium mb-2">AI Analysis:</p>
                      <p className="whitespace-pre-wrap">{image.content}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="space-y-6">
            {caseData.tasks.total === 0 ? (
              <p className="text-gray-500 text-center py-8">No tasks found</p>
            ) : (
              <>
                {['high', 'medium', 'low'].map((priority) => (
                  caseData.tasks.by_priority[priority].length > 0 && (
                    <div key={priority}>
                      <h3 className="font-medium text-gray-800 mb-3 capitalize">
                        {priority} Priority Tasks ({caseData.tasks.by_priority[priority].length})
                      </h3>
                      <div className="space-y-3">
                        {caseData.tasks.by_priority[priority].map((task, index) => (
                          <div key={index} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium text-gray-800">{task.title}</h4>
                              <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(task.priority)}`}>
                                {task.priority}
                              </span>
                            </div>
                            <p className="text-gray-600 text-sm mb-2">{task.description}</p>
                            {task.category && (
                              <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                                {task.category}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
