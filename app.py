import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
