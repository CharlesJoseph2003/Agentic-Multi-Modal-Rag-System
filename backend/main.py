import os
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .text_embedding import Embeddings
from .audio_processing import Audio
from .image_processing import ImageProcessing
from .database import create_case_in_supabase
from .utils import create_case_id, process_single_file_with_case, save_uploaded_file_to_temp, process_audio_for_case, \
cleanup_temp_file, vectordb_output_processing, process_image_for_case, get_case_content_from_chromadb
from .tasks import generate_tasks_with_ai, store_tasks_in_supabase
from supabase import create_client, Client


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
text_embedding = Embeddings()
audio_process = Audio()
image_process = ImageProcessing()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}


@app.post("/create_case/")
async def create_new_case(files: List[UploadFile] = File(default=[]), audio_files: List[UploadFile] = File(default=[]), 
image_files: List[UploadFile] = File(default=[])):
    """
    Create a new case with documents and audio files.
    All files will share the same case_id.
    """
    if not files and not audio_files and not image_files:
        return {"error": "At least one document or audio file must be provided"}
    
    # Generate case ID for all files
    case_id = create_case_id()

    await create_case_in_supabase(case_id)

    results = {
        "case_id": case_id,
        "documents": [],
        "audio": [],
        "images": []
    }
    
    # Process documents if provided
    if files:
        for upload_file in files:
            # Modify process_single_file to accept case_id
            result = await process_single_file_with_case(upload_file, case_id)
            results["documents"].append(result)
    
    # Process audio if provided
    if audio_files:
        for audio_file in audio_files:
            # Save audio to temp
            tmp_path = await save_uploaded_file_to_temp(audio_file)
            try:
                result = await process_audio_for_case(
                    str(tmp_path), 
                    case_id, 
                    audio_file.filename
                )
                results["audio"].append(result)
            finally:
                cleanup_temp_file(tmp_path)

    if image_files:
        for image_file in image_files:
            tmp_path = await save_uploaded_file_to_temp(image_file)
            try:
                result = await process_image_for_case(
                    str(tmp_path), 
                    case_id, 
                    image_file.filename
                )
                results["images"].append(result)
            finally:
                cleanup_temp_file(tmp_path)
    try:
        # Get all content that was just added to ChromaDB
        case_content = await get_case_content_from_chromadb(case_id)
        
        # Generate tasks with AI
        generated_tasks = await generate_tasks_with_ai(case_content, case_id)
        
        # Store tasks in Supabase
        if generated_tasks:
            stored_tasks = await store_tasks_in_supabase(generated_tasks, case_id)
            results["tasks"] = {
                "generated": len(stored_tasks),
                "tasks": stored_tasks
            }
        else:
            results["tasks"] = {
                "generated": 0,
                "tasks": []
            }
            
    except Exception as e:
        print(f"Error generating tasks: {e}")
        results["tasks"] = {
            "error": "Failed to generate tasks",
            "message": str(e)
        }
    
    return results
    
@app.get("/cases")
async def list_cases(limit: int = 10, offset: int = 0):
    """List all cases with pagination"""
    
    cases = supabase.table('cases')\
        .select("*, files(*), tasks(*)")\
        .order('created_at', desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    return {
        "cases": cases.data,
        "total": len(cases.data),
        "limit": limit,
        "offset": offset
    }

@app.get("/case/{case_id}")
async def get_case_details(case_id: str):
    """Get comprehensive case details with all files, content, and tasks"""
    try:
        # Get case info
        case = supabase.table('cases').select("*").eq('id', case_id).single().execute()
        if not case.data:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Get all files for this case
        files = supabase.table('files').select("*").eq('case_id', case_id).execute()
        print(f"DEBUG: Files query returned {len(files.data)} files")
        if files.data:
            print(f"DEBUG: First file: {files.data[0]}")
        
        # Get all tasks for this case
        tasks = supabase.table('tasks').select("*").eq('case_id', case_id).order('priority').execute()
        
        # Get document content from ChromaDB for this case
        case_content = await get_case_content_from_chromadb(case_id)
        print(f"DEBUG: Retrieved case content keys: {case_content.keys()}")
        print(f"DEBUG: Documents count: {len(case_content.get('documents', []))}")
        if case_content.get('documents'):
            print(f"DEBUG: First document metadata: {case_content['documents'][0].get('metadata', {})}")
        
        # Organize files by type with enhanced info
        organized_files = {
            "document": [],
            "audio": [],
            "image": []
        }
        
        for file_record in files.data:
            file_type = file_record['file_type']
            print(f"DEBUG: Processing file: {file_record['original_filename']}, type: {file_type}")
            if file_type in organized_files:
                # Add file metadata
                file_info = {
                    "id": file_record['id'],
                    "filename": file_record['original_filename'],
                    "file_path": file_record.get('file_path', ''),
                    "created_at": file_record['created_at'],
                    "file_size": file_record.get('file_size'),
                    "processing_status": file_record.get('processing_status', 'completed')
                }
                
                # Add content preview for documents and audio (transcriptions)
                if file_type == 'document':
                    # Find matching content from ChromaDB documents
                    matching_content = [
                        content for content in case_content.get('documents', [])
                        if content.get('metadata', {}).get('original_filename') == file_record['original_filename']
                    ]
                    print(f"DEBUG: Looking for file: {file_record['original_filename']}")
                    print(f"DEBUG: Found {len(matching_content)} matching chunks")
                    if matching_content:
                        # Combine all chunks for this file
                        full_content = "\n\n".join([chunk['text'] for chunk in matching_content])
                        file_info['content'] = full_content[:2000] + "..." if len(full_content) > 2000 else full_content
                        file_info['total_chunks'] = len(matching_content)
                        print(f"DEBUG: Added content preview of length: {len(file_info['content'])}")
                    else:
                        print(f"DEBUG: No matching content found for {file_record['original_filename']}")
                
                elif file_type == 'audio':
                    # Find matching content from ChromaDB audio transcriptions
                    matching_content = [
                        content for content in case_content.get('audio_transcriptions', [])
                        if content.get('metadata', {}).get('original_filename') == file_record['original_filename']
                    ]
                    if matching_content:
                        # Combine all chunks for this file
                        full_content = "\n\n".join([chunk['text'] for chunk in matching_content])
                        file_info['content'] = full_content[:2000] + "..." if len(full_content) > 2000 else full_content
                        file_info['total_chunks'] = len(matching_content)
                
                organized_files[file_type].append(file_info)
                print(f"DEBUG: Added {file_type} file to organized_files. Total {file_type}s: {len(organized_files[file_type])}")
            else:
                print(f"DEBUG: File type '{file_type}' not in organized_files keys: {list(organized_files.keys())}")
        
        # Organize tasks by priority
        organized_tasks = {
            "high": [t for t in tasks.data if t.get('priority') == 'high'],
            "medium": [t for t in tasks.data if t.get('priority') == 'medium'],
            "low": [t for t in tasks.data if t.get('priority') == 'low']
        }
        
        return {
            "case": case.data,
            "files": organized_files,
            "tasks": {
                "total": len(tasks.data),
                "by_priority": organized_tasks,
                "all": tasks.data
            },
            "content_summary": {
                "total_chunks": len(case_content),
                "document_count": len(organized_files["document"]),
                "audio_count": len(organized_files["audio"]),
                "image_count": len(organized_files["image"]),
                "task_count": len(tasks.data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving case details: {str(e)}")

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download a file by its ID"""
    try:
        # Get file info from Supabase
        file_record = supabase.table('files').select("*").eq('id', file_id).single().execute()
        
        if not file_record.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = file_record.data.get('storage_path')
        original_filename = file_record.data.get('original_filename')
        
        print(f"DEBUG: Looking for file at path: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found on disk: {file_path}")
        
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.get("/audio/{file_id}")
async def serve_audio(file_id: str):
    """Serve audio file from Supabase storage"""
    try:
        print(f"DEBUG: Audio request for file_id: {file_id}")
        
        # Get file info from Supabase
        file_record = supabase.table('files').select("*").eq('id', file_id).single().execute()
        print(f"DEBUG: File record query result: {file_record.data}")
        
        if not file_record.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        storage_path = file_record.data.get('storage_path')
        mime_type = file_record.data.get('mime_type', 'audio/mpeg')
        
        if not storage_path:
            raise HTTPException(status_code=404, detail="Audio file path not found")
            
        print(f"DEBUG: Getting signed URL for storage path: {storage_path}")
        
        # Get a signed URL from Supabase storage
        try:
            # Create a signed URL that expires in 24 hours
            signed_url_response = supabase.storage.from_('construction_files').create_signed_url(storage_path, 86400)
            signed_url = signed_url_response.get('signedURL')
            
            if signed_url:
                print(f"DEBUG: Generated signed URL: {signed_url}")
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=signed_url)
            else:
                print(f"DEBUG: No signed URL generated, trying direct download")
                # Fallback to direct download
                file_data = supabase.storage.from_('construction_files').download(storage_path)
                print(f"DEBUG: Successfully downloaded {len(file_data)} bytes")
                
                from fastapi.responses import Response
                return Response(
                    content=file_data,
                    media_type=mime_type,
                    headers={
                        "Accept-Ranges": "bytes",
                        "Content-Length": str(len(file_data)),
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            
        except Exception as storage_error:
            print(f"DEBUG: Storage error: {str(storage_error)}")
            raise HTTPException(status_code=404, detail=f"Audio file not accessible: {str(storage_error)}")
        
    except Exception as e:
        print(f"DEBUG: Audio endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving audio: {str(e)}")

@app.get("/image/{file_id}")
async def serve_image(file_id: str):
    """Serve image file from Supabase storage"""
    try:
        print(f"DEBUG: Image request for file_id: {file_id}")
        
        # Get file info from Supabase
        file_record = supabase.table('files').select("*").eq('id', file_id).single().execute()
        print(f"DEBUG: File record query result: {file_record.data}")
        
        if not file_record.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        storage_path = file_record.data.get('storage_path')
        mime_type = file_record.data.get('mime_type', 'image/jpeg')
        
        if not storage_path:
            raise HTTPException(status_code=404, detail="Image file path not found")
            
        print(f"DEBUG: Getting signed URL for storage path: {storage_path}")
        
        # Get a signed URL from Supabase storage
        try:
            # Create a signed URL that expires in 24 hours
            signed_url_response = supabase.storage.from_('construction_files').create_signed_url(storage_path, 86400)
            signed_url = signed_url_response.get('signedURL')
            
            if signed_url:
                print(f"DEBUG: Generated signed URL: {signed_url}")
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=signed_url)
            else:
                print(f"DEBUG: No signed URL generated, trying direct download")
                # Fallback to direct download
                file_data = supabase.storage.from_('construction_files').download(storage_path)
                print(f"DEBUG: Successfully downloaded {len(file_data)} bytes")
                
                from fastapi.responses import Response
                return Response(
                    content=file_data,
                    media_type=mime_type,
                    headers={
                        "Content-Length": str(len(file_data)),
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            
        except Exception as storage_error:
            print(f"DEBUG: Storage error: {str(storage_error)}")
            raise HTTPException(status_code=404, detail=f"Image file not accessible: {str(storage_error)}")
        
    except Exception as e:
        print(f"DEBUG: Image endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")

@app.get("/case/{case_id}/tasks")
async def get_case_tasks(case_id: str):
    """Get all tasks for a case"""
    
    tasks = supabase.table('tasks')\
        .select("*")\
        .eq('case_id', case_id)\
        .order('priority')\
        .execute()
    
    return {
        "case_id": case_id,
        "total_tasks": len(tasks.data),
        "tasks": tasks.data
    }

@app.get("/tasks")
async def get_all_tasks(
    priority: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
):
    """Get all tasks with optional filters"""
    
    query = supabase.table('tasks').select("*")
    
    if priority:
        query = query.eq('priority', priority)
    if category:
        query = query.eq('category', category)
    
    tasks = query.order('created_at', desc=True).limit(limit).execute()
    
    return {
        "total_tasks": len(tasks.data),
        "tasks": tasks.data
    }
    
@app.get("/search/")
async def search(query: str):
    """Search across all case documents and return structured response"""
    try:
        print(f"DEBUG: Search query: {query}")
        
        # Get embeddings and search
        output = text_embedding.get_query(query)
        processed_text = vectordb_output_processing(output)
        result = text_embedding.llm_processing(processed_text, query)
        
        # Structure the response for chat interface
        return {
            "response": result,
            "query": query,
            "sources": processed_text.get("sources", []) if isinstance(processed_text, dict) else [],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"DEBUG: Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


   
# @app.delete("/task/{task_id}")
# async def delete_task(task_id: str):
#     """Delete a specific task"""
    
#     result = supabase.table('tasks').delete().eq('id', task_id).execute()
    
#     if not result.data:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     return {"message": "Task deleted successfully"}

# @app.post("/uploadfiles/")
# async def create_upload_files(files: Annotated[List[UploadFile], File(description="Multiple files as UploadFile")]):
#     results = []
#     for upload_file in files:
#         result = await process_single_file(upload_file)
#         results.append(result)
#     return {"ingested": results}

# @app.post("/uploadaudio/")
# async def upload_audio(file_path):
#     speech_conversion = audio_process.speech_to_text(file_path)
#     cleaned_audio = audio_process.clean_audio(speech_conversion)
#     embedded_audio = text_embedding.embed_text(cleaned_audio)
    

