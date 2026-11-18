"""
RecipeMate AI Entry Point
Runs the FastAPI server with live chat interface on http://localhost:8000
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("  🍳 Starting RecipeMate AI Agent Server")
    print("  🌐 Web Interface: http://127.0.0.1:8000")
    print("  📚 API Docs:      http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
