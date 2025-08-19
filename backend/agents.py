
import os
from smolagents import Tool, ToolCallingAgent, LiteLLMModel
from .text_embedding import Embeddings
from .audio_processing import Audio
from .image_processing import ImageProcessing
from .chroma_db import VectorDB
from supabase import create_client, Client
from .utils import vectordb_output_processing

vector_db = VectorDB()
text_embedding = Embeddings()
audio_process = Audio()
image_process = ImageProcessing()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class CaseDetailsTool(Tool):
    name = "get_case_details"
    description = "Get comprehensive details about a specific construction case including files, tasks, and content"
    inputs = {"case_id": {"type": "string", "description": "The case ID to get details for"}}
    output_type = "string"
    
    def forward(self, case_id: str) -> str:
        # Get all chunks for this case from ChromaDB
        case_results = vector_db.collection.get(
            where={"case_id": case_id},
            include=["documents", "metadatas"]
        )
        
        if not case_results['ids']:
            return f"Case {case_id} not found"
        
        # Get tasks and files from Supabase
        tasks = supabase.table('tasks').select("*").eq('case_id', case_id).execute()
        files = supabase.table('files').select("*").eq('case_id', case_id).execute()
        
        # Organize content by type
        doc_count = 0
        audio_transcriptions = []
        image_descriptions = []
        documents = []
        
        for i, metadata in enumerate(case_results['metadatas']):
            doc_type = metadata.get('doc_type', 'document')
            content = case_results['documents'][i]
            
            if doc_type == 'audio_transcription':
                audio_transcriptions.append(content)
            elif doc_type == 'image':
                image_descriptions.append(content)
            elif doc_type == 'document':
                documents.append(content)
                doc_count += 1
        
        # Build comprehensive summary
        summary = f"""Case {case_id} Details:
- Documents: {doc_count} files
- Tasks: {len(tasks.data)} (High: {len([t for t in tasks.data if t.get('priority') == 'high'])})
- Audio files: {len([f for f in files.data if f.get('file_type') == 'audio'])}
- Images: {len([f for f in files.data if f.get('file_type') == 'image'])}"""
        
        # Add audio transcriptions if available
        if audio_transcriptions:
            summary += f"\n\nAudio Transcriptions:\n"
            for i, transcription in enumerate(audio_transcriptions[:3]):  # First 3
                summary += f"{i+1}. {transcription[:300]}...\n"
        
        # Add image descriptions if available
        if image_descriptions:
            summary += f"\n\nImage Descriptions:\n"
            for i, description in enumerate(image_descriptions[:3]):  # First 3
                summary += f"{i+1}. {description[:200]}...\n"
        
        # Add document content
        if documents:
            summary += f"\n\nDocument Content:\n{documents[0][:300]}..."
        
        return summary

class SearchDocumentsTool(Tool):
    name = "search_documents"
    description = "Search across all construction documents, tasks, and content"
    inputs = {"query": {"type": "string", "description": "Search query"}}
    output_type = "string"
    
    def forward(self, query: str) -> str:
        # Use existing search logic
        output = text_embedding.get_query(query)
        processed = vectordb_output_processing(output)
        result = text_embedding.llm_processing(processed, query)
        
        return result

class ListCasesTool(Tool):
    name = "list_all_cases"
    description = "List all available construction cases"
    inputs = {}
    output_type = "string"
    
    def forward(self) -> str:
        cases = supabase.table('cases').select("id, created_at").execute()
        case_list = [f"- {c['id']} (created: {c['created_at']})" for c in cases.data]
        return f"Available cases ({len(cases.data)} total):\n" + "\n".join(case_list)

class TaskAnalysisTool(Tool):
    name = "analyze_tasks"
    description = "Get task analysis across cases or for a specific case"
    inputs = {
        "case_id": {"type": "string", "description": "Optional case ID to filter tasks", "nullable": True}
    }
    output_type = "string"
    
    def forward(self, case_id: str = None) -> str:
        query = supabase.table('tasks').select("*")
        if case_id:
            query = query.eq('case_id', case_id)
        
        tasks = query.execute()
        
        if not tasks.data:
            return "No tasks found"
        
        # Analyze tasks
        by_priority = {"high": [], "medium": [], "low": []}
        for task in tasks.data:
            priority = task.get('priority', 'low')
            by_priority[priority].append(task)
        
        summary = f"Task Analysis:\n"
        summary += f"Total tasks: {len(tasks.data)}\n"
        summary += f"- High priority: {len(by_priority['high'])}\n"
        summary += f"- Medium priority: {len(by_priority['medium'])}\n"
        summary += f"- Low priority: {len(by_priority['low'])}\n\n"
        
        # Show high priority tasks
        if by_priority['high']:
            summary += "High Priority Tasks:\n"
            for task in by_priority['high'][:5]:
                summary += f"- {task.get('title', 'Untitled')}: {task.get('description', '')[:100]}\n"
        
        return summary

