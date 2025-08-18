# main.py
from typing import List, Optional, Annotated
from fastapi import FastAPI, File, UploadFile
from utils import create_case_id, process_single_file_with_case, save_uploaded_file_to_temp, process_audio_for_case, cleanup_temp_file, vectordb_output_processing
from text_embedding import Embeddings
from audio_processing import Audio


app = FastAPI()
text_embedding = Embeddings()
audio_process = Audio()


@app.post("/create_case/")
async def create_new_case(files: List[UploadFile] = File(default=[]),
    audio_files: List[UploadFile] = File(default=[])):
    """
    Create a new case with documents and audio files.
    All files will share the same case_id.
    """
    if not files and not audio_files:
        return {"error": "At least one document or audio file must be provided"}
    
    # Generate case ID for all files
    case_id = create_case_id()
    results = {
        "case_id": case_id,
        "documents": [],
        "audio": []
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
    
    return results

    
@app.get("/search/")
async def search(query):
    output = text_embedding.get_query(query)
    processed_text = vectordb_output_processing(output)
    result = text_embedding.llm_processing(processed_text, query)
    return result
   


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
    


