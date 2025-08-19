import os
import json
from typing import Dict, List
from openai import OpenAI
from .chroma_db import VectorDB
from dotenv import load_dotenv
from supabase import create_client, Client
from .text_embedding import Embeddings

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API")
client = OpenAI(api_key = OPENAI_API_KEY)

vector_db = VectorDB()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

text_embedding = Embeddings()


async def generate_tasks_with_ai(case_content: Dict[str, List[Dict]], case_id: str) -> List[Dict]:
    """Use AI to analyze case content and generate tasks"""
    
    print(f"DEBUG: Starting task generation for case {case_id}")
    print(f"DEBUG: Case content keys: {list(case_content.keys())}")
    print(f"DEBUG: Content counts - docs: {len(case_content.get('documents', []))}, audio: {len(case_content.get('audio_transcriptions', []))}, images: {len(case_content.get('image_descriptions', []))}")
    
    # Check if we have any content to work with
    total_content = len(case_content.get('documents', [])) + len(case_content.get('audio_transcriptions', [])) + len(case_content.get('image_descriptions', []))
    if total_content == 0:
        print(f"DEBUG: No content found for case {case_id}, skipping task generation")
        return []
    
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

Based on this content, generate 2-5 specific actionable tasks. Focus on:
1. Safety issues requiring immediate attention
2. Compliance or regulatory requirements
3. Repairs or maintenance needed
4. Required documentation or reports
5. Follow-up actions needed

CRITICAL: You must respond with ONLY valid JSON in this exact format. Do not include any explanatory text before or after the JSON:

{{
    "tasks": [
        {{
            "title": "Inspect structural integrity",
            "description": "Detailed description of what needs to be done",
            "priority": "high",
            "category": "safety",
            "reasoning": "Why this task is important"
        }}
    ]
}}

Priority must be: "high", "medium", or "low"
Category must be: "safety", "compliance", "maintenance", "documentation", or "general"
"""

    # Call OpenAI with temperature for more consistent results
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a construction site safety and compliance expert. You MUST respond with valid JSON only. No explanations, no markdown, just pure JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower temperature for more consistent outputs
        max_tokens=1000
    )

    # Parse response
    try:
        response_text = response.choices[0].message.content
        print(f"DEBUG: Raw AI response: {response_text}")
        
        # Clean up response if needed (remove markdown code blocks)
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "")
        
        # Remove any leading/trailing whitespace
        response_text = response_text.strip()
        
        # Try to find JSON in the response if it's mixed with other text
        if not response_text.startswith('{'):
            # Look for JSON object in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
        
        print(f"DEBUG: Cleaned response: {response_text}")
        
        tasks_data = json.loads(response_text)
        
        # Get the list of tasks
        if isinstance(tasks_data, list):
            tasks = tasks_data
        elif isinstance(tasks_data, dict) and 'tasks' in tasks_data:
            tasks = tasks_data['tasks']
        else:
            print(f"DEBUG: Unexpected tasks_data format: {type(tasks_data)}")
            tasks = []
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response was: {response.choices[0].message.content}")
        tasks = []
    except Exception as e:
        print(f"Unexpected error parsing tasks: {e}")
        tasks = []
    
    # Add case_id and source chunks to each task
    for task in tasks:
        task['case_id'] = case_id
        task['source_chunks'] = [item['chunk_id'] for content_list in case_content.values() 
                                for item in content_list if item['chunk_id']]
    
    return tasks
    
async def store_tasks_in_supabase(tasks: List[Dict], case_id: str) -> List[Dict]:
    """Store generated tasks in Supabase AND ChromaDB"""
    
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
    
    # Insert into Supabase
    result = supabase.table('tasks').insert(db_tasks).execute()
    
    # Now add tasks to ChromaDB for searchability
    task_ids = []
    task_texts = []
    task_embeddings = []
    task_metadatas = []
    
    for i, task in enumerate(result.data):
        # Create searchable text from task
        task_text = f"Task: {task['title']}\nDescription: {task['description']}\nPriority: {task['priority']}\nCategory: {task['category']}\nReasoning: {task['ai_reasoning']}"
        
        # Generate embedding
        embedding = text_embedding.embed_text(task_text)
        
        # Create unique ID for task in ChromaDB
        task_chromadb_id = f"{case_id}_task_{task['id'][:8]}"
        
        task_ids.append(task_chromadb_id)
        task_texts.append(task_text)
        task_embeddings.append(embedding)
        
        # Metadata for the task
        metadata = {
            'case_id': case_id,
            'task_id': task['id'],
            'doc_type': 'task',
            'title': task['title'],
            'priority': task['priority'],
            'category': task['category']
        }
        task_metadatas.append(metadata)
    
    # Store in ChromaDB
    if task_ids:
        vector_db.collection.add(
            ids=task_ids,
            documents=task_texts,
            embeddings=task_embeddings,
            metadatas=task_metadatas
        )
    
    return result.data
