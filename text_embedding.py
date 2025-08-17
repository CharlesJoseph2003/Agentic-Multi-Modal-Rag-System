import os
from dotenv import load_dotenv
from openai import OpenAI
from chroma_db import VectorDB
from typing import List, Dict, Any

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API")

vector_db = VectorDB()
client = OpenAI(api_key = OPENAI_API_KEY)

class Embeddings:
    def __init__(self):
        pass
    
    def embed_text(self, text):
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def get_query(self, query: str) -> str:
    # Create embedding using the SAME model as ingestion
        query_embedding = self.embed_text(query)
        results = vector_db.collection.query(
            query_embeddings=[query_embedding],  # Pass the embedding directly
            n_results=5
        )
        return results

    def llm_processing(self, query_result: List[Dict[str, Any]], user_question: str) -> str:
        documents, metadata = query_result
        context_parts = []
        for i, (doc, meta) in enumerate(zip(documents, metadata)):
            source_info = f"[Source {i+1}: {meta['original_filename']}, Chunk {meta['chunk_index']}]"
            context_parts.append(f"{source_info}\n{doc}")
        context = "\n\n".join(context_parts)
        prompt = f"""Based on the following context, please answer the user's question. When you use information from the context, \
            cite it using the source number (e.g., [Source 1], [Source 2]). If the answer cannot be found in the context, \
            say "I cannot find that information in the provided documents."Context:{context} Question: {user_question} Answer:"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based solely on the provided context.\
                Always cite your sources using [Source X] format when referencing information."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
