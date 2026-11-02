import uvicorn
import sys
import os

# Fix stdout encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("🚀 Starting FindMyCampus (Sarvam Campus '26)...")
    print("📍 URL: http://127.0.0.1:8000")
    uvicorn.run("server.app:app", host="127.0.0.1", port=8000, reload=True)

