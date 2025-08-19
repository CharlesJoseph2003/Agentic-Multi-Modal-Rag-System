import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# if __name__ == "__main__":
#     uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    # Get port from environment variable (Railway provides this)
    port = int(os.environ.get("PORT", 8000))
    
    # Use 0.0.0.0 instead of 127.0.0.1 for Railway
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
