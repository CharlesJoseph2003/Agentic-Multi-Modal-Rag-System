import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .functions.text_embedding import Embeddings
from .functions.audio_processing import Audio
from .functions.image_processing import ImageProcessing
from .functions.chroma_db import VectorDB

# Import routers
from .routers import cases_list, case_detail, case_upload, chat_interface

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://agentic-multi-modal-rag-system.vercel.app",
        "https://agentic-multi-modal-rag-system-g1657j32y.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize shared services
vector_db = VectorDB()
text_embedding = Embeddings()
audio_process = Audio()
image_process = ImageProcessing()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

# Include routers
app.include_router(cases_list.router)
app.include_router(case_detail.router)
app.include_router(case_upload.router)
app.include_router(chat_interface.router)