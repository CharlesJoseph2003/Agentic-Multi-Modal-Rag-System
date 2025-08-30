"""
Router for cases listing functionality.
Handles endpoints related to listing and deleting cases.
"""
import os
from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
from ..functions.utils import delete_case_completely

router = APIRouter(tags=["cases_list"])

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.get("/cases")
async def list_cases(limit: int = 10, offset: int = 0):
    """Case listing with file and task counts"""
    cases = supabase.table('cases')\
        .select("id, created_at")\
        .order('created_at', desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    # Enhance each case with file and task counts
    enhanced_cases = []
    for case in cases.data:
        case_id = case['id']
        
        # Get files for this case
        files = supabase.table('files').select("file_type").eq('case_id', case_id).execute()
        
        # Get tasks for this case
        tasks = supabase.table('tasks').select("id").eq('case_id', case_id).execute()
        
        # Add file and task information
        case['files'] = files.data
        case['tasks'] = tasks.data
        enhanced_cases.append(case)
    
    return {"cases": enhanced_cases, "total": len(enhanced_cases)}

@router.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    """Delete a case and all its associated data from both ChromaDB and Supabase"""
    try:
        success = await delete_case_completely(case_id)
        
        if success:
            return {"message": f"Case {case_id} deleted successfully from all databases"}
        else:
            raise HTTPException(status_code=500, detail="Failed to completely delete case")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting case: {str(e)}")
