#!/usr/bin/env python3
"""
Startup script for the AI Customer Support Backend
"""
import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['GEMINI_API_KEY', 'ELEVENLABS_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f'your-{var.lower().replace("_", "-")}-here':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment variables.")
        print("You can get API keys from:")
        print("   - Gemini: https://makersuite.google.com/app/apikey")
        print("   - ElevenLabs: https://elevenlabs.io/app/settings/api-keys")
        return False
    
    return True

def main():
    print("🚀 Starting AI Customer Support Backend...")
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠️  No .env file found. Creating a template...")
        with open('.env', 'w') as f:
            f.write("""# API Keys - Replace with your actual keys
GEMINI_API_KEY=your-gemini-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=customer_support

# Optional: ElevenLabs Voice ID
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
""")
        print("📝 Created .env file. Please update it with your API keys.")
        return
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not check_environment():
        return
    
    print("✅ Environment variables loaded")
    print("🌐 Starting server on http://localhost:8000")
    print("📚 API documentation available at http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start the FastAPI server
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
