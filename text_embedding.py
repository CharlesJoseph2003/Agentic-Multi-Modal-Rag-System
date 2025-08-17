import os
from dotenv import load_dotenv
from openai import OpenAI
client = OpenAI()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API")

class Embeddings:
    def __init__(self):
        pass
    
    def embed_text(self, text):
        client = OpenAI(api_key = OPENAI_API_KEY)
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
