"""
Router for chat interface functionality.
Handles endpoints related to intelligent queries and search.
"""
import os
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from smolagents import Tool, ToolCallingAgent, HfApiModel, LiteLLMModel
from ..functions.agents import SearchDocumentsTool, CaseDetailsTool, TaskAnalysisTool, ListCasesTool

router = APIRouter(tags=["chat_interface"])

# Initialize tools
case_details_tool = CaseDetailsTool()
search_tool = SearchDocumentsTool()
list_cases_tool = ListCasesTool()
task_tool = TaskAnalysisTool()

# Initialize model and agent
model = LiteLLMModel(model_id="gpt-4", api_key=os.getenv("OPENAI_API"))
agent = ToolCallingAgent(
    tools=[case_details_tool, search_tool, list_cases_tool, task_tool],
    model=model,
)

class QueryRequest(BaseModel):
    query: str

@router.post("/search")
async def intelligent_query(request: QueryRequest):
    """Single endpoint that handles all queries intelligently"""
    try:
        # Let the agent handle everything
        result = agent.run(request.query)
        
        return {
            "query": request.query,
            "response": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}
