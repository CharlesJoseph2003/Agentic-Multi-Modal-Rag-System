import os, uuid, json, tempfile
from typing import List, Tuple, Any, Dict
from pathlib import Path
from fastapi import  UploadFile
from text_processing import TextProcessing
from text_embedding import Embeddings
from chroma_db import VectorDB

CHUNK_DIR = Path("uploads/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

text_embedding = Embeddings()
vector_db = VectorDB()


async def save_uploaded_file_to_temp(upload_file: UploadFile) -> Path:
    # Reset file pointer to beginning
    await upload_file.seek(0)
    
    suffix = Path(upload_file.filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = Path(tmp.name)
        # Stream copy upload to temp
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk: 
                break
            tmp.write(chunk)
    return tmp_path

def process_chunks_for_storage(chunks: List[Any], doc_id: str, filename: str) -> Tuple[List[str], List[str], List[List[float]], List[Dict[str, Any]]]:
    """
    Process chunks to prepare them for ChromaDB storage.
    
    Args:
        chunks: List of chunks (can be dicts or strings)
        doc_id: Document ID
        filename: Original filename
        
    Returns:
        Tuple of (chunk_ids, chunk_texts, embeddings, metadatas)
    """
    chunk_ids = []
    chunk_texts = []
    chunk_embeddings = []
    chunk_metadatas = []
    
    for i, chunk in enumerate(chunks):
        # Extract text from chunk
        if isinstance(chunk, dict):
            chunk_text = chunk.get('text', str(chunk))
        else:
            chunk_text = str(chunk)
        
        # Generate embedding
        embedding = text_embedding.embed_text(chunk_text)
        
        # Prepare data for ChromaDB
        chunk_ids.append(f"{doc_id}_chunk_{i}")
        chunk_texts.append(chunk_text)
        chunk_embeddings.append(embedding)
        
        # Create metadata for this chunk
        metadata = {
            'doc_id': doc_id,
            'original_filename': filename,
            'chunk_index': i,
            'total_chunks': len(chunks)
        }
        
        # If chunk is a dict with additional metadata, add it
        if isinstance(chunk, dict):
            for key, value in chunk.items():
                if key != 'text':  # Don't duplicate the text
                    metadata[key] = value
        
        chunk_metadatas.append(metadata)
    
    return chunk_ids, chunk_texts, chunk_embeddings, chunk_metadatas


def save_chunks_to_jsonl(chunks: List[Any], doc_id: str) -> Path:
    """
    Save chunks to a JSONL file for backup/reference.
    
    Args:
        chunks: List of chunks to save
        doc_id: Document ID for filename
        
    Returns:
        Path to the saved JSONL file
    """
    out_path = CHUNK_DIR / f"{doc_id}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return out_path


def cleanup_temp_file(file_path: Path) -> None:
    """
    Safely remove temporary file.
    
    Args:
        file_path: Path to file to remove
    """
    try:
        os.remove(file_path)
    except OSError:
        pass  # File might already be deleted or inaccessible


async def process_single_file(upload_file: UploadFile) -> Dict[str, Any]:
    """
    Process a single uploaded file through the entire pipeline.
    
    Args:
        upload_file: The uploaded file to process
        
    Returns:
        Dictionary with processing results
    """
    # Save to temp file
    tmp_path = await save_uploaded_file_to_temp(upload_file)
    
    try:
        # Generate document ID and chunk the document
        doc_id = uuid.uuid4().hex
        tp = TextProcessing(str(tmp_path))
        chunks = tp.pdf_to_chunks()
        
        # Process chunks for storage
        chunk_ids, chunk_texts, embeddings, metadatas = process_chunks_for_storage(
            chunks, doc_id, upload_file.filename
        )
        
        # Store in ChromaDB
        vector_db.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        # Save chunks to JSONL file
        out_path = save_chunks_to_jsonl(chunks, doc_id)
        
        return {
            "original_filename": upload_file.filename,
            "doc_id": doc_id,
            "chunks_path": str(out_path),
            "num_chunks": len(chunks),
        }
        
    finally:
        # Always cleanup temp file
        cleanup_temp_file(tmp_path)


