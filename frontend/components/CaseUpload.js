'use client';

import { useState, useRef } from 'react';
import { apiClient } from '../utils/api';

export default function CaseUpload({ onCaseCreated }) {
  const [files, setFiles] = useState([]);
  const [audioFiles, setAudioFiles] = useState([]);
  const [imageFiles, setImageFiles] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const fileInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const imageInputRef = useRef(null);

  // Handle file uploads
  const handleFileChange = (e, type) => {
    const selectedFiles = Array.from(e.target.files);
    
    if (type === 'documents') {
      setFiles(prev => [...prev, ...selectedFiles]);
    } else if (type === 'audio') {
      setAudioFiles(prev => [...prev, ...selectedFiles]);
    } else if (type === 'images') {
      setImageFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  // Remove file from list
  const removeFile = (index, type) => {
    if (type === 'documents') {
      setFiles(prev => prev.filter((_, i) => i !== index));
    } else if (type === 'audio') {
      setAudioFiles(prev => prev.filter((_, i) => i !== index));
    } else if (type === 'images') {
      setImageFiles(prev => prev.filter((_, i) => i !== index));
    }
  };

  // Start audio recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], `recording-${Date.now()}.wav`, { type: 'audio/wav' });
        setAudioFiles(prev => [...prev, audioFile]);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Error accessing microphone. Please check permissions.');
    }
  };

  // Stop audio recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Submit case
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (files.length === 0 && audioFiles.length === 0 && imageFiles.length === 0) {
      alert('Please add at least one file, audio recording, or image.');
      return;
    }

    setIsUploading(true);
    setUploadProgress('Preparing files...');

    try {
      const formData = new FormData();
      
      // Add documents
      files.forEach(file => {
        formData.append('files', file);
      });
      
      // Add audio files
      audioFiles.forEach(file => {
        formData.append('audio_files', file);
      });
      
      // Add image files
      imageFiles.forEach(file => {
        formData.append('image_files', file);
      });

      setUploadProgress('Uploading and processing files...');
      const result = await apiClient.createCase(formData);
      
      setUploadProgress('Generating AI tasks...');
      
      // Reset form
      setFiles([]);
      setAudioFiles([]);
      setImageFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (audioInputRef.current) audioInputRef.current.value = '';
      if (imageInputRef.current) imageInputRef.current.value = '';
      
      setUploadProgress('Case created successfully!');
      
      // Notify parent component
      if (onCaseCreated) {
        onCaseCreated(result);
      }
      
      setTimeout(() => {
        setUploadProgress('');
      }, 3000);
      
    } catch (error) {
      console.error('Error creating case:', error);
      setUploadProgress('Error creating case. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Create New Case</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Document Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Documents (PDF, DOC, etc.)
          </label>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt"
            onChange={(e) => handleFileChange(e, 'documents')}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {files.length > 0 && (
            <div className="mt-2 space-y-1">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                  <span className="text-sm text-gray-600">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(index, 'documents')}
                    className="text-red-500 hover:text-red-700"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Audio Recording and Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Audio Files
          </label>
          
          <div className="flex gap-4 mb-2">
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={`px-4 py-2 rounded-md font-medium ${
                isRecording 
                  ? 'bg-red-500 text-white hover:bg-red-600' 
                  : 'bg-green-500 text-white hover:bg-green-600'
              }`}
            >
              {isRecording ? '🛑 Stop Recording' : '🎤 Start Recording'}
            </button>
          </div>
          
          <input
            ref={audioInputRef}
            type="file"
            multiple
            accept="audio/*"
            onChange={(e) => handleFileChange(e, 'audio')}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
          />
          
          {audioFiles.length > 0 && (
            <div className="mt-2 space-y-1">
              {audioFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                  <span className="text-sm text-gray-600">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(index, 'audio')}
                    className="text-red-500 hover:text-red-700"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Image Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Images
          </label>
          <input
            ref={imageInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => handleFileChange(e, 'images')}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
          />
          {imageFiles.length > 0 && (
            <div className="mt-2 space-y-1">
              {imageFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                  <span className="text-sm text-gray-600">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(index, 'images')}
                    className="text-red-500 hover:text-red-700"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isUploading}
          className={`w-full py-3 px-4 rounded-md font-medium ${
            isUploading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          } text-white transition-colors`}
        >
          {isUploading ? 'Creating Case...' : 'Create Case'}
        </button>

        {/* Progress Message */}
        {uploadProgress && (
          <div className={`text-center p-3 rounded-md ${
            uploadProgress.includes('Error') 
              ? 'bg-red-100 text-red-700' 
              : uploadProgress.includes('successfully')
              ? 'bg-green-100 text-green-700'
              : 'bg-blue-100 text-blue-700'
          }`}>
            {uploadProgress}
          </div>
        )}
      </form>
    </div>
  );
}
