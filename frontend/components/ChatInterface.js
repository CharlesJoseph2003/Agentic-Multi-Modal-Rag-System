'use client';

import { useState, useRef, useEffect } from 'react';
import { apiClient } from '../utils/api';

export default function ChatInterface({ caseId }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    // Small delay to ensure DOM is updated before scrolling
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [messages]);
  
  // Focus input when component mounts
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Call the search endpoint
      const response = await fetch(`http://127.0.0.1:8000/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content
        })
      });
      const result = await response.json();

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: result.response || result.answer || 'No response received',
        sources: result.sources || [],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Search error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error while searching. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex flex-col h-full border border-gray-200 rounded-lg bg-white overflow-hidden">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center text-gray-500 p-8">
            <div>
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-1">Welcome to Construction RAG Chat</h3>
              <p className="text-sm mb-4">
                {caseId 
                  ? "Ask questions about the documents, audio, or images in this case"
                  : "Ask questions about any documents across all your cases"
                }
              </p>
              <div className="grid grid-cols-1 gap-3 max-w-md mx-auto">
                <button 
                  onClick={() => {
                    setInputValue("What documents are available?");
                    if (inputRef.current) inputRef.current.focus();
                  }}
                  className="text-left px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                >
                  What documents are available?
                </button>
                <button 
                  onClick={() => {
                    setInputValue("Summarize the key information from all documents");
                    if (inputRef.current) inputRef.current.focus();
                  }}
                  className="text-left px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                >
                  Summarize the key information from all documents
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`w-full py-6 px-4 md:px-8 lg:px-16 xl:px-24 ${message.type === 'assistant' ? 'bg-blue-50' : 'bg-white'}`}
              >
                <div className="max-w-3xl mx-auto flex">
                  {/* Avatar */}
                  <div className="mr-4 flex-shrink-0">
                    {message.type === 'user' ? (
                      <div className="h-10 w-10 rounded-full bg-gray-800 flex items-center justify-center text-white shadow-sm">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                      </div>
                    ) : (
                      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white shadow-sm">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                          <line x1="3" y1="9" x2="21" y2="9"></line>
                          <line x1="9" y1="21" x2="9" y2="9"></line>
                        </svg>
                      </div>
                    )}
                  </div>
                  
                  {/* Message Content */}
                  <div className="flex-1">
                    <p className="font-bold text-base mb-2 text-gray-900">
                      {message.type === 'user' ? 'You' : 'Construction RAG'}
                    </p>
                    <div className="prose prose-base max-w-none">
                      <p className="whitespace-pre-wrap text-gray-800 leading-relaxed">{message.content}</p>
                    </div>
                    
                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-4 pt-2 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-500 mb-2">Sources:</p>
                        <div className="space-y-1">
                          {message.sources.map((source, idx) => (
                            <div key={idx} className="flex items-start">
                              <div className="flex-shrink-0 mr-2">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <p className="text-xs text-gray-500">
                                {source.filename || `Document ${idx + 1}`}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-400 mt-2">{formatTime(message.timestamp)}</p>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading Message */}
            {isLoading && (
              <div className="w-full py-6 px-4 md:px-8 lg:px-16 xl:px-24 bg-blue-50">
                <div className="max-w-3xl mx-auto flex">
                  <div className="mr-4 flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white shadow-sm">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="3" y1="9" x2="21" y2="9"></line>
                        <line x1="9" y1="21" x2="9" y2="9"></line>
                      </svg>
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="font-bold text-base mb-2 text-gray-900">Construction RAG</p>
                    <div className="flex items-center">
                      <div className="animate-pulse flex space-x-3">
                        <div className="h-3 w-3 bg-blue-400 rounded-full"></div>
                        <div className="h-3 w-3 bg-blue-400 rounded-full"></div>
                        <div className="h-3 w-3 bg-blue-400 rounded-full"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-gray-200 bg-white p-6 shadow-inner">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={caseId ? "Ask a question about this case..." : "Ask a question about your construction documents..."}
              className="w-full pl-5 pr-16 py-4 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800 text-base"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="absolute right-3 top-3 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 shadow-sm"
              aria-label="Send message"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-center text-gray-600 mt-3 font-medium">
            Construction RAG can make mistakes. Consider checking important information.  
          </p>
        </form>
      </div>
    </div>
  );
}
