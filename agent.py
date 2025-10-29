from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import httpx
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import io
import base64
import google.generativeai as genai

app = FastAPI(title="AI Customer Support Agent", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - Use environment variables in production
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "your-elevenlabs-api-key")
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "customer_support"

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# MongoDB setup
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]
conversations_collection = db.conversations
users_collection = db.users

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    audio_url: Optional[str] = None
    conversation_id: str

class ConversationLog(BaseModel):
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    user_message: str
    ai_response: str
    timestamp: datetime
    audio_path: Optional[str] = None

# MongoDB operations
async def save_conversation(conversation_id: str, user_id: Optional[str], user_email: Optional[str], 
                           user_message: str, ai_response: str, audio_path: Optional[str] = None):
    """Save conversation to MongoDB"""
    conversation_doc = {
        "_id": conversation_id,
        "user_id": user_id,
        "user_email": user_email,
        "user_message": user_message,
        "ai_response": ai_response,
        "timestamp": datetime.utcnow(),
        "audio_path": audio_path
    }
    
    await conversations_collection.insert_one(conversation_doc)
    
    # Update user's last active time if user exists
    if user_email:
        await users_collection.update_one(
            {"email": user_email},
            {
                "$set": {"last_active": datetime.utcnow()},
                "$setOnInsert": {
                    "email": user_email,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

async def get_conversation_history(user_id: Optional[str] = None, user_email: Optional[str] = None, limit: int = 10):
    """Get conversation history from MongoDB"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    elif user_email:
        query["user_email"] = user_email
    
    cursor = conversations_collection.find(query).sort("timestamp", -1).limit(limit)
    conversations = await cursor.to_list(length=limit)
    return conversations

# Gemini AI Integration
async def get_ai_response(message: str, context: List[dict] = None) -> str:
    """Get response from Gemini AI model"""
    
    # Build conversation context
    system_prompt = """आप एक मददगार AI customer support agent हैं। आपको चाहिए:
    1. दोस्ताना, पेशेवर और सहानुभूतिपूर्ण रहें
    2. स्पष्ट और संक्षिप्त जवाब दें
    3. जरूरत पड़ने पर स्पष्टीकरण के सवाल पूछें
    4. अगर कुछ नहीं पता तो ईमानदारी से कहें
    5. ग्राहक की समस्याओं को कुशलता से हल करने की कोशिश करें
    6. जवाब बातचीत के लिए प्राकृतिक रखें
    7. उपयोगकर्ता की भाषा में जवाब दें (हिंदी/अंग्रेजी)"""
    
    # Add conversation history for context
    conversation_history = ""
    if context:
        for item in context[-3:]:  # Last 3 conversations for context
            conversation_history += f"User: {item.get('user_message', '')}\n"
            conversation_history += f"Assistant: {item.get('ai_response', '')}\n\n"
    
    full_prompt = f"{system_prompt}\n\nPrevious conversation:\n{conversation_history}\nCurrent user message: {message}"
    
    try:
        # Use Gemini Pro model
        response = model.generate_content(full_prompt)
        return response.text
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Gemini AI: {str(e)}")

# ElevenLabs STT Integration
async def speech_to_text(audio_file: bytes) -> str:
    """Convert speech to text using ElevenLabs"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"audio": ("audio.wav", audio_file, "audio/wav")}
            headers = {"xi-api-key": ELEVENLABS_API_KEY}
            
            response = await client.post(
                "https://api.elevenlabs.io/v1/speech-to-text",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                raise HTTPException(status_code=500, detail="Failed to convert speech to text")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in speech-to-text: {str(e)}")

# ElevenLabs TTS Integration
async def text_to_speech(text: str) -> bytes:
    """Convert text to speech using ElevenLabs"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
                headers={
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": ELEVENLABS_API_KEY,
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
            )
            
            if response.status_code == 200:
                return response.content
            else:
                raise HTTPException(status_code=500, detail="Failed to convert text to speech")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in text-to-speech: {str(e)}")

# API Endpoints

@app.get("/")
async def root():
    return {"message": "AI Customer Support Agent API", "version": "1.0.0"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Handle text-based chat messages"""
    try:
        conversation_id = str(uuid.uuid4())
        
        # Get conversation history for context
        context = await get_conversation_history(
            user_id=message.user_id, 
            user_email=message.user_email, 
            limit=5
        )
        
        # Get AI response
        ai_response = await get_ai_response(message.message, context)
        
        # Generate audio response
        audio_bytes = await text_to_speech(ai_response)
        
        # Save audio file (in production, use cloud storage)
        audio_filename = f"audio_{conversation_id}.mp3"
        audio_path = f"./audio_files/{audio_filename}"
        
        # Create audio directory if it doesn't exist
        os.makedirs("./audio_files", exist_ok=True)
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Save conversation to database
        await save_conversation(
            conversation_id=conversation_id,
            user_id=message.user_id,
            user_email=message.user_email,
            user_message=message.message,
            ai_response=ai_response,
            audio_path=audio_path
        )
        
        return ChatResponse(
            response=ai_response,
            audio_url=f"/api/audio/{conversation_id}",
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/api/voice", response_model=ChatResponse)
async def voice_endpoint(audio: UploadFile = File(...), user_id: Optional[str] = None, user_email: Optional[str] = None):
    """Handle voice-based queries"""
    try:
        conversation_id = str(uuid.uuid4())
        
        # Read audio file
        audio_bytes = await audio.read()
        
        # Convert speech to text
        user_message = await speech_to_text(audio_bytes)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Could not understand the audio")
        
        # Get conversation history for context
        context = await get_conversation_history(
            user_id=user_id, 
            user_email=user_email, 
            limit=5
        )
        
        # Get AI response
        ai_response = await get_ai_response(user_message, context)
        
        # Generate audio response
        response_audio_bytes = await text_to_speech(ai_response)
        
        # Save audio files
        os.makedirs("./audio_files", exist_ok=True)
        audio_filename = f"response_{conversation_id}.mp3"
        audio_path = f"./audio_files/{audio_filename}"
        
        with open(audio_path, "wb") as f:
            f.write(response_audio_bytes)
        
        # Save conversation to database
        await save_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            user_email=user_email,
            user_message=user_message,
            ai_response=ai_response,
            audio_path=audio_path
        )
        
        return ChatResponse(
            response=ai_response,
            audio_url=f"/api/audio/{conversation_id}",
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice: {str(e)}")

@app.get("/api/audio/{conversation_id}")
async def get_audio(conversation_id: str):
    """Serve audio files"""
    try:
        audio_path = f"./audio_files/response_{conversation_id}.mp3"
        if not os.path.exists(audio_path):
            audio_path = f"./audio_files/audio_{conversation_id}.mp3"
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        def iterfile():
            with open(audio_path, mode="rb") as f:
                yield from f
        
        return StreamingResponse(iterfile(), media_type="audio/mpeg")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving audio: {str(e)}")

@app.get("/api/conversations")
async def get_conversations(user_id: Optional[str] = None, user_email: Optional[str] = None, limit: int = 20):
    """Get conversation history"""
    try:
        conversations = await get_conversation_history(user_id, user_email, limit)
        
        # Convert MongoDB documents to JSON-serializable format
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "id": conv["_id"],
                "user_id": conv.get("user_id"),
                "user_email": conv.get("user_email"),
                "user_message": conv["user_message"],
                "ai_response": conv["ai_response"],
                "timestamp": conv["timestamp"].isoformat(),
                "audio_path": conv.get("audio_path")
            })
        
        return {"conversations": formatted_conversations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)