import os
import json
from typing import Dict, List  # Add this
from openai import OpenAI  # Change from 'import openai as OpenAI'
from chroma_db import VectorDB
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API")
client = OpenAI(api_key = OPENAI_API_KEY)

vector_db = VectorDB()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_case_content_from_chromadb(case_id: str) -> Dict[str, List[Dict]]:
    """Retrieve all content for a case from ChromaDB"""
    
    # Get all chunks for this case
    results = vector_db.collection.get(
        where={"case_id": case_id},
        include=["documents", "metadatas"]
    )
    
    # Organize by document type
    organized_content = {
        "documents": [],
        "audio_transcriptions": [],
        "image_descriptions": []
    }
    
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        content_item = {
            "text": doc,
            "metadata": metadata,
            "chunk_id": results['ids'][i] if 'ids' in results else None
        }
        
        doc_type = metadata.get('doc_type', 'document')
        if doc_type == 'audio_transcription':
            organized_content['audio_transcriptions'].append(content_item)
        elif doc_type == 'image':
            organized_content['image_descriptions'].append(content_item)
        else:
            organized_content['documents'].append(content_item)
    
    return organized_content
async def generate_tasks_with_ai(case_content: Dict[str, List[Dict]], case_id: str) -> List[Dict]:
    """Use AI to analyze case content and generate tasks"""
    
    # Build context for LLM
    context = "Analyze this construction case and generate actionable tasks:\n\n"
    
    # Add documents
    if case_content['documents']:
        context += "DOCUMENTS:\n"
        for doc in case_content['documents']:
            context += f"- {doc['metadata'].get('original_filename', 'Document')}: {doc['text']}\n"
    
    # Add audio transcriptions
    if case_content['audio_transcriptions']:
        context += "\nAUDIO TRANSCRIPTIONS:\n"
        for audio in case_content['audio_transcriptions']:
            context += f"- {audio['metadata'].get('original_filename', 'Audio')}: {audio['text']}\n"
    
    # Add image descriptions
    if case_content['image_descriptions']:
        context += "\nIMAGE DESCRIPTIONS:\n"
        for img in case_content['image_descriptions']:
            context += f"- {img['metadata'].get('original_filename', 'Image')}: {img['text']}\n"
    
    # Create prompt with explicit JSON instruction
    prompt = f"""{context}

Based on this content, generate specific actionable tasks. Focus on:
1. Safety issues requiring immediate attention
2. Compliance or regulatory requirements
3. Repairs or maintenance needed
4. Required documentation or reports
5. Follow-up actions needed

Return ONLY a valid JSON object with a 'tasks' array. No other text.
Example format:
{{
    "tasks": [
        {{
            "title": "Task title",
            "description": "Task description",
            "priority": "high",
            "category": "safety",
            "reasoning": "Why this task is needed"
        }}
    ]
}}"""

    # Call OpenAI without response_format
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a construction site safety and compliance expert. Generate actionable tasks from case documentation. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        # Removed response_format parameter
    )

    # Parse response
    try:
        response_text = response.choices[0].message.content
        # Clean up response if needed (remove markdown code blocks)
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "")
        
        tasks_data = json.loads(response_text.strip())
        
        # Get the list of tasks
        if isinstance(tasks_data, list):
            tasks = tasks_data
        elif isinstance(tasks_data, dict) and 'tasks' in tasks_data:
            tasks = tasks_data['tasks']
        else:
            tasks = []
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response was: {response.choices[0].message.content}")
        tasks = []
    
    # Add case_id and source chunks to each task
    for task in tasks:
        task['case_id'] = case_id
        task['source_chunks'] = [item['chunk_id'] for content_list in case_content.values() 
                                for item in content_list if item['chunk_id']]
    
    return tasks['tasks']

async def store_tasks_in_supabase(tasks: List[Dict]) -> List[Dict]:
    """Store generated tasks in Supabase"""
    
    # Prepare tasks for database
    db_tasks = []
    for task in tasks:
        db_task = {
            "case_id": task['case_id'],
            "title": task['title'],
            "description": task.get('description', ''),
            "priority": task.get('priority', 'medium'),
            "category": task.get('category', 'general'),
            "source_chunks": task.get('source_chunks', []),
            "ai_reasoning": task.get('reasoning', '')
        }
        db_tasks.append(db_task)
    
    # Insert all tasks
    result = supabase.table('tasks').insert(db_tasks).execute()
    return result.data