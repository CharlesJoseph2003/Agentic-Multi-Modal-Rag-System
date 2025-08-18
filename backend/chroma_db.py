import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_KEY = os.getenv("CHROMA_API_KEY")
class VectorDB:
    def __init__(self):
        self.client = chromadb.HttpClient(
            ssl=True,
            host='api.trychroma.com',
            tenant='5f4e69d6-09e0-4a7f-891f-0252553b86d4',
            database='Rag',
            headers={
                'x-chroma-token': CHROMA_KEY
            }
        )
        self.collection = self.client.get_or_create_collection(name="Rag")
