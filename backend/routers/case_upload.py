"""
Router for case upload functionality.
Handles endpoints related to creating new cases and uploading files.
"""
import os
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException
from supabase import create_client, Client
from ..functions.utils import create_case_id, process_single_file_with_case, save_uploaded_file_to_temp, process_audio_for_case, \
    cleanup_temp_file, process_image_for_case, get_case_content_from_chromadb
from ..functions.database import create_case_in_supabase
from ..functions.tasks import generate_tasks_with_ai, store_tasks_in_supabase

router = APIRouter(tags=["case_upload"])

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.post("/create_case/")
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
