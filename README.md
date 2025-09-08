# Agentic Multi-Modal RAG System for Construction

An intelligent document processing and retrieval system designed for construction projects. This system allows users to upload documents, audio recordings, and images, then query across all content using natural language with AI-powered agents.

## 🏗️ System Overview

This RAG (Retrieval-Augmented Generation) system processes multi-modal construction data and provides intelligent querying capabilities through AI agents. Each "case" represents a construction project or situation that maintains context across all uploaded materials.

## 🔄 System Flow

### 1. **Document Ingestion**
- **Upload**: Users upload PDFs, documents, audio files, and images
- **Processing**: Docling extracts and structures content from documents
- **Transcription**: Audio files are transcribed to text
- **Vision Analysis**: Images are analyzed using AI vision models
- **Vectorization**: All content is embedded and stored in ChromaDB
- **Metadata**: File information stored in Supabase database

### 2. **AI Task Generation**
- **Content Analysis**: AI analyzes all case content
- **Task Extraction**: Automatically generates relevant tasks and action items
- **Priority Assignment**: Tasks are categorized by priority (high/medium/low)
- **Storage**: Tasks stored in Supabase for tracking

### 3. **Intelligent Querying**
- **Natural Language**: Users query in plain English
- **Agent Routing**: SmolaAgents determine the best approach
- **Multi-Modal Search**: Searches across documents, transcriptions, and image analysis
- **Contextual Responses**: AI provides comprehensive answers with source citations

## 🛠️ Technology Stack

### **Backend (FastAPI)**
- **FastAPI**: High-performance Python web framework
- **RESTful APIs**: Clean endpoints for all operations
- **Async Processing**: Non-blocking file processing
- **CORS Support**: Frontend integration

### **Document Processing (Docling)**
- **PDF Extraction**: Advanced PDF content extraction
- **Structure Preservation**: Maintains document hierarchy
- **Multi-format Support**: Handles various document types
- **Text Chunking**: Intelligent content segmentation

### **Database & Storage (Supabase)**
- **PostgreSQL**: Relational data storage
- **File Storage**: Secure cloud file storage
- **Real-time**: Live data synchronization
- **Authentication**: Built-in user management

### **Vector Database (ChromaDB)**
- **Embeddings Storage**: High-dimensional vector storage
- **Similarity Search**: Fast semantic search capabilities
- **Metadata Filtering**: Context-aware retrieval
- **Persistent Storage**: Reliable vector persistence

### **AI Agents (SmolaAgents)**
- **Tool Orchestration**: Intelligent tool selection and usage
- **Multi-step Reasoning**: Complex query handling
- **Context Management**: Maintains conversation context
- **LLM Integration**: Supports various language models

### **Frontend (Next.js)**
- **React Framework**: Modern component-based UI
- **Server-Side Rendering**: Optimized performance
- **Real-time Updates**: Dynamic content updates
- **Responsive Design**: Mobile-friendly interface

## 📋 Key Features

- **Multi-Modal Processing**: Documents, audio, and images in one system
- **Intelligent Agents**: AI-powered query understanding and response
- **Case Management**: Organized project-based content storage
- **Task Generation**: Automatic action item extraction
- **Semantic Search**: Context-aware content retrieval
- **Real-time Processing**: Live file upload and processing
- **Clean UI**: Intuitive web interface for all operations

## 🚀 Use Cases

- **Construction Project Management**: Centralize all project documents and media
- **Compliance Tracking**: Query regulations and requirements across documents
- **Progress Monitoring**: Audio logs and image documentation
- **Knowledge Retrieval**: Find specific information across large document sets
- **Task Management**: AI-generated action items from project content

## 🔧 Architecture

```
Frontend (Next.js) → FastAPI Backend → Processing Pipeline
                                    ↓
                            [Docling, Audio, Vision]
                                    ↓
                            [ChromaDB, Supabase]
                                    ↓
                            SmolaAgents → LLM Response
```

The system maintains context across all modalities, enabling comprehensive understanding of construction projects and intelligent response generation.

## 🚀 Live Demo
- **Frontend**: [https://agentic-multi-modal-rag-system.vercel.app](https://agentic-multi-modal-rag-system.vercel.app)
- **Backend API**: [https://chaero.duckdns.org\docs](https://chaero.duckdns.org\docs)
