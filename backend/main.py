import os
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .text_embedding import Embeddings
from .audio_processing import Audio
from .image_processing import ImageProcessing
from .chroma_db import VectorDB
from .agents import SearchDocumentsTool, CaseDetailsTool, TaskAnalysisTool, ListCasesTool
from .database import create_case_in_supabase
from .utils import create_case_id, process_single_file_with_case, save_uploaded_file_to_temp, process_audio_for_case, \
cleanup_temp_file, process_image_for_case, get_case_content_from_chromadb, delete_case_completely
from .tasks import generate_tasks_with_ai, store_tasks_in_supabase
from supabase import create_client, Client
from pydantic import BaseModel  
from smolagents import Tool, ToolCallingAgent, HfApiModel, LiteLLMModel


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
vector_db = VectorDB()
text_embedding = Embeddings()
audio_process = Audio()
image_process = ImageProcessing()

case_details_tool = CaseDetailsTool()
search_tool = SearchDocumentsTool()
list_cases_tool = ListCasesTool()
task_tool = TaskAnalysisTool()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class QueryRequest(BaseModel):
    query: str

#creating agent
# model = HfApiModel(model_id=""meta-llama/Llama-3.3-70B-Instruct"")  
model = LiteLLMModel(model_id="gpt-4", api_key=os.getenv("OPENAI_API"))
agent = ToolCallingAgent(
    tools=[case_details_tool, search_tool, list_cases_tool, task_tool],
    model=model,

)


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
        results["tasks"] = {
            "error": "Failed to generate tasks",
            "message": str(e)
        }
    
    return results
    
@app.get("/cases")  # Enhanced case listing with file counts
async def list_cases(limit: int = 10, offset: int = 0):
    """Case listing with file and task counts"""
    cases = supabase.table('cases')\
        .select("id, created_at")\
        .order('created_at', desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    # Enhance each case with file and task counts
    enhanced_cases = []
    for case in cases.data:
        case_id = case['id']
        
        # Get files for this case
        files = supabase.table('files').select("file_type").eq('case_id', case_id).execute()
        
        # Get tasks for this case
        tasks = supabase.table('tasks').select("id").eq('case_id', case_id).execute()
        
        # Add file and task information
        case['files'] = files.data
        case['tasks'] = tasks.data
        enhanced_cases.append(case)
    
    return {"cases": enhanced_cases, "total": len(enhanced_cases)}

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
        # Get all tasks for this case
        tasks = supabase.table('tasks').select("*").eq('case_id', case_id).order('priority').execute()
        
        # Get document content from ChromaDB for this case
        case_content = await get_case_content_from_chromadb(case_id)
        # Organize files by type with enhanced info
        organized_files = {
            "document": [],
            "audio": [],
            "image": []
        }
        
        for file_record in files.data:
            file_type = file_record['file_type']
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
                    if matching_content:
                        # Combine all chunks for this file
                        full_content = "\n\n".join([chunk['text'] for chunk in matching_content])
                        file_info['content'] = full_content[:2000] + "..." if len(full_content) > 2000 else full_content
                        file_info['total_chunks'] = len(matching_content)
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


@app.get("/audio/{file_id}")
async def serve_audio(file_id: str):
    """Serve audio file from Supabase storage"""
    try:
        
        # Get file info from Supabase
        file_record = supabase.table('files').select("*").eq('id', file_id).single().execute()        
        if not file_record.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        storage_path = file_record.data.get('storage_path')
        mime_type = file_record.data.get('mime_type', 'audio/mpeg')
        
        if not storage_path:
            raise HTTPException(status_code=404, detail="Audio file path not found")        
        # Get a signed URL from Supabase storage
        try:
            # Create a signed URL that expires in 24 hours
            signed_url_response = supabase.storage.from_('construction_files').create_signed_url(storage_path, 86400)
            signed_url = signed_url_response.get('signedURL')
            
            if signed_url:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=signed_url)
            else:
                # Fallback to direct download
                file_data = supabase.storage.from_('construction_files').download(storage_path)                
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
            raise HTTPException(status_code=404, detail=f"Audio file not accessible: {str(storage_error)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving audio: {str(e)}")

@app.get("/image/{file_id}")
async def serve_image(file_id: str):
    """Serve image file from Supabase storage"""
    try:        
        # Get file info from Supabase
        file_record = supabase.table('files').select("*").eq('id', file_id).single().execute()        
        if not file_record.data:
            raise HTTPException(status_code=404, detail="File not found")
        
        storage_path = file_record.data.get('storage_path')
        mime_type = file_record.data.get('mime_type', 'image/jpeg')
        
        if not storage_path:
            raise HTTPException(status_code=404, detail="Image file path not found")
                    
        # Get a signed URL from Supabase storage
        try:
            # Create a signed URL that expires in 24 hours
            signed_url_response = supabase.storage.from_('construction_files').create_signed_url(storage_path, 86400)
            signed_url = signed_url_response.get('signedURL')
            
            if signed_url:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=signed_url)
            else:
                # Fallback to direct download
                file_data = supabase.storage.from_('construction_files').download(storage_path)
                
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
            raise HTTPException(status_code=404, detail=f"Image file not accessible: {str(storage_error)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


   
@app.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    """Delete a case and all its associated data from both ChromaDB and Supabase"""
    try:
        success = await delete_case_completely(case_id)
        
        if success:
            return {"message": f"Case {case_id} deleted successfully from all databases"}
        else:
            raise HTTPException(status_code=500, detail="Failed to completely delete case")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting case: {str(e)}")

# Single smart endpoint
@app.post("/search")
async def intelligent_query(request: QueryRequest):
    """Single endpoint that handles all queries intelligently"""
    try:
        # Let the agent handle everything
        result = agent.run(request.query)
        
        return {
            "query": request.query,
            "response": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}