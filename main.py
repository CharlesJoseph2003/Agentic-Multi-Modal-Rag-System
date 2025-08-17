# main.py
import os, uuid, json, tempfile
from typing import Annotated, List
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from utils import save_upload  # <- use the new helper
from text_processing import TextProcessing
from text_embedding import Embeddings
from chroma_db import VectorDB


app = FastAPI()
vector_db = VectorDB()

CHUNK_DIR = Path("uploads/chunks")
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[List[UploadFile], File(description="Multiple files as UploadFile")]
):
    results = []
    text_embedding = Embeddings()
    
    for uf in files:
        # 1) write to a temp file (so Docling has a path)
        suffix = Path(uf.filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)
            # stream copy upload to temp
            while True:
                chunk = await uf.read(1024 * 1024)
                if not chunk: break
                tmp.write(chunk)

        # 2) chunk
        doc_id = uuid.uuid4().hex
        tp = TextProcessing(str(tmp_path))
        chunks = tp.pdf_to_chunks()   # <-- make this return a list of chunk dicts or strings
        
        # Prepare lists for ChromaDB
        chunk_ids = []
        chunk_texts = []
        chunk_embeddings = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Extract text from chunk (handle both dict and string formats)
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
                'original_filename': uf.filename,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            # If chunk is a dict with additional metadata, add it
            if isinstance(chunk, dict):
                for key, value in chunk.items():
                    if key != 'text':  # Don't duplicate the text
                        metadata[key] = value
            
            chunk_metadatas.append(metadata)
        
        # Store in ChromaDB
        vector_db.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=chunk_embeddings,
            metadatas=chunk_metadatas
        )

        # 3) save ONLY chunks to project
        out_path = CHUNK_DIR / f"{doc_id}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for c in chunks:
                # c can be {"text": ..., "section": ..., "page": ...}
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

        # 4) remove the temp PDF
        try:
            os.remove(tmp_path)
        except OSError:
            pass

        results.append({
            "original_filename": uf.filename,
            "doc_id": doc_id,
            "chunks_path": str(out_path),
            "num_chunks": len(chunks),
        })

    return {"ingested": results}

# @app.post("/uploadfiles/")
# async def create_upload_files(files: List[UploadFile] = File(...)):
#     results = []
#     for f in files:
#         data = await f.read()                    # ✅ await the read
#         try:
#             text = data.decode("utf-8")          # decode bytes → string
#         except UnicodeDecodeError:
#             text = data.decode("latin-1", errors="replace")
#         results.append({"filename": f.filename, "text": text})
#     return {"files": results}