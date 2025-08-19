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
    
    def delete_case_from_chromadb(self, case_id: str) -> bool:
        """Delete all documents associated with a case from ChromaDB"""
        try:
            # Get all documents for this case
            results = self.collection.get(
                where={"case_id": case_id}
            )
            
            if results['ids']:
                # Delete all documents with this case_id
                self.collection.delete(
                    where={"case_id": case_id}
                )
                print(f"Deleted {len(results['ids'])} documents from ChromaDB for case {case_id}")
            
            return True
            
        except Exception as e:
            print(f"Error deleting case from ChromaDB: {e}")
            return False
