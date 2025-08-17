#get document upload
#chunking using docling 
#openai embeddings
from typing import Annotated, List

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from text_processing import TextProcessing

app = FastAPI()


@app.post("/uploadfiles/")
async def create_upload_files(files: Annotated[list[UploadFile], File(description="Multiple files as UploadFile")],
):
    return {"filenames": [file for file in files]}


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