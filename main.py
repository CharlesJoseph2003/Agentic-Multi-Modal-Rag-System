# main.py
from typing import Annotated, List
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from chroma_db import VectorDB
from utils import process_single_file, vectordb_output_processing
from text_embedding import Embeddings

app = FastAPI()
text_embedding = Embeddings()

CHUNK_DIR = Path("uploads/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/uploadfiles/")
async def create_upload_files(files: Annotated[List[UploadFile], File(description="Multiple files as UploadFile")]):
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

@app.get("/search/")
async def search(query):
    output = text_embedding.get_query(query)
    processed_text = vectordb_output_processing(output)
    result = text_embedding.llm_processing(processed_text, query)
    return result
   