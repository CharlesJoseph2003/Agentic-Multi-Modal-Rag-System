# utils.py
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload(upload: UploadFile, dest_dir: Path = UPLOAD_DIR, filename: Optional[str] = None) -> Path:
    """
    Save an UploadFile to dest_dir. Returns the destination Path.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = filename or Path(upload.filename).name
    dest_path = dest_dir / name
    with dest_path.open("wb") as out:
        shutil.copyfileobj(upload.file, out)   # streams without loading whole file into RAM
    return dest_path
