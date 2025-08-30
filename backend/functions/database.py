import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def create_case_in_supabase(case_id: str) -> dict:
    """Create a new case record in Supabase"""
    case_data = {"id": case_id}
    result = supabase.table('cases').insert(case_data).execute()
    return result.data[0]

async def upload_file_to_supabase(
    file_path: str, 
    case_id: str, 
    file_type: str,
    original_filename: str
) -> dict:
    """Upload file to Supabase storage and save metadata"""
    
    # Determine MIME type
    mime_types = {
        '.pdf': 'application/pdf',
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    
    file_ext = Path(original_filename).suffix.lower()
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    # Create storage path
    storage_path = f"cases/{case_id}/{file_type}s/{original_filename}"
    
    # Upload to storage bucket
    with open(file_path, 'rb') as f:
        file_data = f.read()
        file_size = len(file_data)
        
        # Upload file
        storage_response = supabase.storage.from_('construction_files').upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": mime_type}
        )
        
        # Check if upload was successful
        if hasattr(storage_response, 'error') and storage_response.error:
            raise Exception(f"Failed to upload file to Supabase: {storage_response.error}")
    
    # Get public URL (if bucket is public)
    file_url = supabase.storage.from_('construction_files').get_public_url(storage_path)
    
    # Save metadata to database
    file_metadata = {
        "case_id": case_id,
        "file_type": file_type,
        "original_filename": original_filename,
        "storage_path": storage_path,
        "file_url": file_url,
        "file_size": file_size,
        "mime_type": mime_type
    }
    
    db_result = supabase.table('files').insert(file_metadata).execute()
    
    # Check database insert was successful
    if not db_result.data:
        raise Exception("Failed to save file metadata to database")
    
    return db_result.data[0]

async def delete_case_from_supabase(case_id: str) -> bool:
    """Delete a case and all its associated data from Supabase"""
    try:
        # Get all files associated with this case
        files_result = supabase.table('files').select('storage_path').eq('case_id', case_id).execute()
        
        # Delete files from storage
        if files_result.data:
            for file_record in files_result.data:
                storage_path = file_record['storage_path']
                try:
                    supabase.storage.from_('construction_files').remove([storage_path])
                except Exception as e:
                    print(f"Warning: Could not delete file {storage_path}: {e}")
        
        # Delete from database tables in order (respecting foreign key constraints)
        # Delete tasks first
        supabase.table('tasks').delete().eq('case_id', case_id).execute()
        
        # Delete files metadata
        supabase.table('files').delete().eq('case_id', case_id).execute()
        
        # Delete the case itself
        result = supabase.table('cases').delete().eq('id', case_id).execute()
        
        return True
        
    except Exception as e:
        print(f"Error deleting case from Supabase: {e}")
        return False
