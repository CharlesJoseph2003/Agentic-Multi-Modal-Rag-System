# main.py
from typing import Annotated, List
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from chroma_db import VectorDB
from utils import process_single_file

app = FastAPI()

CHUNK_DIR = Path("uploads/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[List[UploadFile], File(description="Multiple files as UploadFile")]
):
    """
    Endpoint to upload and process multiple files.
    
    Args:
        files: List of uploaded files
        
    Returns:
        Dictionary with ingestion results for all files
    """
    results = []
    
    for upload_file in files:
        result = await process_single_file(upload_file)
        results.append(result)
    
    return {"ingested": results}
