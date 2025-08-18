import os
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from .text_embedding import Embeddings
from .audio_processing import Audio
from .image_processing import ImageProcessing
from .database import create_case_in_supabase
from .utils import create_case_id, process_single_file_with_case, save_uploaded_file_to_temp, process_audio_for_case, \
cleanup_temp_file, vectordb_output_processing, process_image_for_case, get_case_content_from_chromadb
from .tasks import generate_tasks_with_ai, store_tasks_in_supabase
from supabase import create_client, Client


app = FastAPI()
text_embedding = Embeddings()
audio_process = Audio()
image_process = ImageProcessing()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
        .select("*, files(count)")\
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
    """Get case details with all files"""
    case = supabase.table('cases').select("*").eq('id', case_id).single().execute()
    if not case.data:
        raise HTTPException(status_code=404, detail="Case not found")
    
    files = supabase.table('files').select("*").eq('case_id', case_id).execute()
    tasks = supabase.table('tasks').select("*").eq('case_id', case_id).execute()
    
    # Organize files by type
    organized_files = {
        "documents": [f for f in files.data if f['file_type'] == 'document'],
        "audio": [f for f in files.data if f['file_type'] == 'audio'],
        "images": [f for f in files.data if f['file_type'] == 'image']
    }
    
    return {
        "case": case.data,
        "files": organized_files,
        "tasks": tasks.data
    }

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
async def search(query):
    output = text_embedding.get_query(query)
    processed_text = vectordb_output_processing(output)
    result = text_embedding.llm_processing(processed_text, query)
    return result


   
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
    

