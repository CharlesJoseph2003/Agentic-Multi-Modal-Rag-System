# pip install chromadb sentence-transformers python-dotenv
import os
import chromadb
from dotenv import load_dotenv
import uuid

load_dotenv()

CHROMA_KEY = os.getenv("CHROMA_API_KEY")

client = chromadb.HttpClient(
    ssl=True,
  host='api.trychroma.com',
  tenant='5f4e69d6-09e0-4a7f-891f-0252553b86d4',
  database='Rag',
  headers={
    'x-chroma-token': CHROMA_KEY
  }
)

collection = client.get_or_create_collection(name="Rag")
with open("resume.txt", "r", encoding="utf-8") as f:
    File_input: list[str] = f.read().splitlines()

collection.add(
    ids = [str(uuid.uuid4())for _ in File_input],
    documents = File_input,
    metadatas = [{'line': line}for line in range(len(File_input))]
)

# results = collection.query(
#     query_texts=[
#         "What university did charles attend?",
#         "What year is he graduating in?"
#     ],
#     n_results=5
# )

# for i, query_results in enumerate(results["documents"]):
#     print(f"\nQuery {i}")
#     print("\n".join(query_results))
    

# print(collection.peek())
