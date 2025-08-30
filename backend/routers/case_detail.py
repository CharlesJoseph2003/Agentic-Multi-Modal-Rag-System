"""
Router for case detail functionality.
Handles endpoints related to viewing case details and serving media files.
"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, Response
from supabase import create_client, Client
from ..functions.utils import get_case_content_from_chromadb

router = APIRouter(tags=["case_detail"])

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.get("/case/{case_id}")
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
                        file_info['content'] = full_content[:10000] + "..." if len(full_content) > 10000 else full_content
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
                        file_info['content'] = full_content[:10000] + "..." if len(full_content) > 10000 else full_content
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

@router.get("/audio/{file_id}")
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
                return RedirectResponse(url=signed_url)
            else:
                # Fallback to direct download
                file_data = supabase.storage.from_('construction_files').download(storage_path)                
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

@router.get("/image/{file_id}")
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
                return RedirectResponse(url=signed_url)
            else:
                # Fallback to direct download
                file_data = supabase.storage.from_('construction_files').download(storage_path)
                
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
