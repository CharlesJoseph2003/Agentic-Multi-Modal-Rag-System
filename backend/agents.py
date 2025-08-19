from smolagents import Tool, ToolCallingAgent, HfApiModel
from datetime import datetime
from pydantic import BaseModel
from .utils import vectordb_output_processing

# Define Tools
class CaseDetailsTool(Tool):
    name = "get_case_details"
    description = "Get comprehensive details about a specific construction case including files, tasks, and content"
    inputs = {"case_id": {"type": "string", "description": "The case ID to get details for"}}
    output_type = "string"
    
    def __init__(self, vector_db, supabase, client):
        super().__init__()
        self.vector_db = vector_db
        self.supabase = supabase
        self.client = client
    
    def forward(self, case_id: str) -> str:
        # Get all chunks for this case from ChromaDB
        case_results = self.vector_db.collection.get(
            where={"case_id": case_id},
            include=["documents", "metadatas"]
        )
        
        if not case_results['ids']:
            return f"Case {case_id} not found"
        
        # Get tasks from Supabase
        tasks = self.supabase.table('tasks').select("*").eq('case_id', case_id).execute()
        
        # Get files from Supabase
        files = self.supabase.table('files').select("*").eq('case_id', case_id).execute()
        
        # Organize content
        doc_count = len([m for m in case_results['metadatas'] if m.get('doc_type') == 'document'])
        task_count = len(tasks.data)
        audio_count = len([f for f in files.data if f.get('file_type') == 'audio'])
        image_count = len([f for f in files.data if f.get('file_type') == 'image'])
        
        # Build summary
        summary = f"""Case {case_id} Summary:
- Documents: {doc_count} files
- Tasks: {task_count} (High: {len([t for t in tasks.data if t.get('priority') == 'high'])})
- Audio files: {audio_count}
- Images: {image_count}
- Created: {files.data[0]['created_at'] if files.data else 'Unknown'}

Key content: {case_results['documents'][0][:200] if case_results['documents'] else 'No content'}..."""
        
        return summary

class SearchDocumentsTool(Tool):
    name = "search_documents"
    description = "Search across all construction documents, tasks, and content"
    inputs = {"query": {"type": "string", "description": "Search query"}}
    output_type = "string"
    
    def __init__(self, text_embedding):
        super().__init__()
        self.text_embedding = text_embedding
    
    def forward(self, query: str) -> str:
        # Use existing search logic
        output = self.text_embedding.get_query(query)
        processed = vectordb_output_processing(output)
        result = self.text_embedding.llm_processing(processed, query)
        
        return result

class ListCasesTool(Tool):
    name = "list_all_cases"
    description = "List all available construction cases"
    inputs = {}
    output_type = "string"
    
    def __init__(self, supabase):
        super().__init__()
        self.supabase = supabase
    
    def forward(self) -> str:
        cases = self.supabase.table('cases').select("id, created_at").execute()
        case_list = [f"- {c['id']} (created: {c['created_at']})" for c in cases.data]
        return f"Available cases ({len(cases.data)} total):\n" + "\n".join(case_list)

class TaskAnalysisTool(Tool):
    name = "analyze_tasks"
    description = "Get task analysis across cases or for a specific case"
    inputs = {
        "case_id": {"type": "string", "description": "Optional case ID to filter tasks", "default": None}
    }
    output_type = "string"
    
    def __init__(self, supabase):
        super().__init__()
        self.supabase = supabase
    
    def forward(self, case_id: str = None) -> str:
        query = self.supabase.table('tasks').select("*")
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

# Initialize tools
case_details_tool = CaseDetailsTool(vector_db, supabase, client)
search_tool = SearchDocumentsTool(text_embedding)
list_cases_tool = ListCasesTool(supabase)
task_tool = TaskAnalysisTool(supabase)

# Create the agent
model = HfApiModel(model_id="meta-llama/Llama-3.3-70B-Instruct")
agent = ToolCallingAgent(
    tools=[case_details_tool, search_tool, list_cases_tool, task_tool],
    model=model,
    system_prompt="""You are a construction project assistant. Help users find information about their cases.
    
When users ask about:
- Specific cases → use get_case_details
- Searching for content → use search_documents  
- What cases exist → use list_all_cases
- Tasks or priorities → use analyze_tasks

You can use multiple tools to answer complex questions."""
)

# Single smart endpoint
@app.post("/query")
async def intelligent_query(request: dict):
    """Single endpoint that handles all queries intelligently"""
    query = request.get("query", "")
    
    try:
        # Let the agent handle everything
        result = agent.run(query)
        
        return {
            "query": query,
            "response": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}