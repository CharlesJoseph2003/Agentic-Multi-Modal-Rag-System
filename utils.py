import os, uuid, json, tempfile
from typing import List, Tuple, Any, Dict
from pathlib import Path
from fastapi import  UploadFile
from text_processing import TextProcessing
from text_embedding import Embeddings
from chroma_db import VectorDB
from audio_processing import Audio
from image_processing import ImageProcessing
from database import upload_file_to_supabase

CHUNK_DIR = Path("uploads/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

text_embedding = Embeddings()
vector_db = VectorDB()
audio_process = Audio()
image_process = ImageProcessing()

def create_case_id() -> str:
    """Generate a unique case ID that will be shared across all related files"""
    return f"case_{uuid.uuid4().hex[:12]}"

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

async def process_audio_for_case(file_path: str, case_id: str, audio_filename: str) -> Dict[str, Any]:
    """Process audio file and store in ChromaDB with case ID."""
    
    # Upload raw audio to Supabase FIRST
    supabase_file = await upload_file_to_supabase(
        file_path=file_path,
        case_id=case_id,
        file_type="audio",
        original_filename=audio_filename
    )
    
    # Process audio
    speech_conversion = audio_process.speech_to_text(file_path)
    cleaned_audio = audio_process.clean_audio(speech_conversion)
    
    # Generate embedding
    embedding = text_embedding.embed_text(cleaned_audio)
    
    # Create unique ID for this audio chunk
    audio_id = f"{case_id}_audio_{uuid.uuid4().hex[:8]}"
    
    # Prepare metadata
    metadata = {
        'case_id': case_id,
        'doc_type': 'audio_transcription',
        'original_filename': audio_filename,
        'supabase_file_id': supabase_file['id'],
        'chunk_index': 0,
        'total_chunks': 1
    }
    
    # Store in ChromaDB
    vector_db.collection.add(
        ids=[audio_id],
        documents=[cleaned_audio],
        embeddings=[embedding],
        metadatas=[metadata]
    )
    
    return {
        "case_id": case_id,
        "audio_filename": audio_filename,
        "supabase_file_id": supabase_file['id'],
        "storage_url": supabase_file['file_url'],
        "transcription_length": len(cleaned_audio),
        "doc_type": "audio_transcription"
    }


async def process_image_for_case(file_path: str, case_id: str, image_filename: str) -> Dict[str, Any]:
    """Process image file and store in ChromaDB with case ID."""
    
    # Upload raw image to Supabase FIRST
    supabase_file = await upload_file_to_supabase(
        file_path=file_path,
        case_id=case_id,
        file_type="image",
        original_filename=image_filename
    )
    
    # Process image
    image_to_text = image_process.image_description(file_path)
    
    # Generate embedding
    embedding = text_embedding.embed_text(image_to_text)
    
    # Create unique ID for this image chunk
    image_id = f"{case_id}_image_{uuid.uuid4().hex[:8]}"
    
    # Prepare metadata
    metadata = {
        'case_id': case_id,
        'doc_type': 'image',
        'original_filename': image_filename,
        'supabase_file_id': supabase_file['id'],
        'chunk_index': 0,
        'total_chunks': 1
    }
    
    # Store in ChromaDB
    vector_db.collection.add(
        ids=[image_id],
        documents=[image_to_text],
        embeddings=[embedding],
        metadatas=[metadata]
    )
    
    return {
        "case_id": case_id,
        "image_filename": image_filename,
        "supabase_file_id": supabase_file['id'],
        "storage_url": supabase_file['file_url'],
        "description_length": len(image_to_text),
        "doc_type": "image"
    }


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

async def process_single_file_with_case(upload_file: UploadFile, case_id: str) -> Dict[str, Any]:
    """Process a single uploaded file with a specific case ID."""

    tmp_path = await save_uploaded_file_to_temp(upload_file)
    
    try:
        # Upload raw file to Supabase FIRST
        supabase_file = await upload_file_to_supabase(
            file_path=str(tmp_path),
            case_id=case_id,
            file_type="document",
            original_filename=upload_file.filename
        )
        
        # Then process for ChromaDB
        doc_id = uuid.uuid4().hex
        tp = TextProcessing(str(tmp_path))
        chunks = tp.pdf_to_chunks()
        
        # Process chunks for ChromaDB
        chunk_ids = []
        chunk_texts = []
        chunk_embeddings = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk if isinstance(chunk, str) else chunk.get('text', str(chunk))
            embedding = text_embedding.embed_text(chunk_text)
            
            chunk_ids.append(f"{doc_id}_chunk_{i}")
            chunk_texts.append(chunk_text)
            chunk_embeddings.append(embedding)
            
            metadata = {
                'case_id': case_id,
                'doc_id': doc_id,
                'doc_type': 'document',
                'original_filename': upload_file.filename,
                'supabase_file_id': supabase_file['id'],  # Link to Supabase
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            chunk_metadatas.append(metadata)
        
        # Store in ChromaDB
        vector_db.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=chunk_embeddings,
            metadatas=chunk_metadatas
        )
        
        # Save chunks to JSONL
        out_path = save_chunks_to_jsonl(chunks, doc_id)
        
        return {
            "case_id": case_id,
            "original_filename": upload_file.filename,
            "doc_id": doc_id,
            "supabase_file_id": supabase_file['id'],
            "storage_url": supabase_file['file_url'],
            "chunks_path": str(out_path),
            "num_chunks": len(chunks),
            "doc_type": "document"
        }
        
    finally:
        cleanup_temp_file(tmp_path)

def vectordb_output_processing(query_result):
    documents = query_result['documents'][0]
    metadatas = query_result['metadatas'][0]
    return documents, metadatas
