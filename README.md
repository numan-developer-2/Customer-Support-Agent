# 🤖 AI Customer Support Agent

A complete AI-powered customer support system with voice and text chat capabilities, built with FastAPI, Next.js, MongoDB, Gemini AI, and ElevenLabs.

## ✨ Features

- 💬 **Text Chat** - Type messages and get instant AI responses
- 🎤 **Voice Chat** - Speak naturally and hear AI responses back
- 🗃️ **Conversation History** - All chats stored in MongoDB
- 👤 **User Management** - Track users and conversation context
- 🔊 **Audio Playback** - Listen to AI responses
- 📱 **Responsive UI** - Works on desktop and mobile
- 🚀 **Production Ready** - Docker setup included

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - Document database for conversations
- **Gemini AI** - Google's AI reasoning and responses
- **ElevenLabs** - Speech-to-Text and Text-to-Speech
- **Motor** - Async MongoDB driver

### Frontend  
- **Next.js** - React framework
- **TailwindCSS** - Utility-first CSS
- **Web Audio API** - Voice recording

## 📋 Prerequisites

1. **API Keys Required:**
   - Gemini API key ([Get here](https://makersuite.google.com/app/apikey))
   - ElevenLabs API key ([Get here](https://elevenlabs.io/))

2. **Database:**
   - MongoDB (local or MongoDB Atlas)

3. **Development Environment:**
   - Python 3.11+
   - Node.js 18+
   - npm or yarn

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (or create the files manually)
mkdir ai-customer-support
cd ai-customer-support

# Create backend directory
mkdir backend
mkdir frontend
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Edit `.env` file with your API keys:
```env
GEMINI_API_KEY=your-gemini-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=customer_support
```

### 3. Start MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB locally and start
mongod
```

**Option B: Docker MongoDB**
```bash
docker run -d \
  --name ai_support_mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:7.0
```

**Option C: MongoDB Atlas**
- Create account at [MongoDB Atlas](https://cloud.mongodb.com/)
- Create cluster and get connection string
- Update MONGODB_URL in .env

### 4. Start Backend

```bash
# In backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 5. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## 🐳 Docker Deployment

### 1. Create Directory Structure
```
ai-customer-support/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── pages/
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

### 2. Deploy with Docker

```bash
# Create .env file in root directory
cp .env.example .env
# Edit with your API keys

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- MongoDB: localhost:27017

## 🔧 API Endpoints

### Backend API Documentation

- **GET /** - API info
- **POST /api/chat** - Send text message
- **POST /api/voice** - Send voice message  
- **GET /api/audio/{conversation_id}** - Get audio response
- **GET /api/conversations** - Get chat history
- **GET /api/health** - Health check

### Example API Usage

**Text Chat:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my order",
    "user_email": "customer@example.com"
  }'
```

**Voice Chat:**
```bash
curl -X POST "http://localhost:8000/api/voice" \
  -F "audio=@recording.wav" \
  -F "user_email=customer@example.com"
```

## 📱 Frontend Usage

1. **Text Chat:**
   - Type message in input field
   - Press Enter or click Send
   - AI responds with text and audio

2. **Voice Chat:**
   - Click microphone button to start recording
   - Speak your question
   - Click stop button
   - AI processes speech and responds

3. **Audio Playback:**
   - Click speaker icon on AI messages
   - Audio plays automatically for voice queries

## 🔐 Environment Variables

### Backend (.env)
```env
# Required
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Optional
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=customer_support

# Production (Phase 2)
HUBSPOT_API_KEY=your_hubspot_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🧪 Testing

### Test Backend
```bash
# Health check
curl http://localhost:8000/api/health

# Test chat
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

### Test Frontend
1. Open http://localhost:3000
2. Try text chat
3. Try voice recording (allow microphone permission)
4. Check audio playback

## 📈 Phase 2 Enhancements

### CRM Integration (HubSpot)
```python
# Add to backend/main.py
async def sync_to_hubspot(user_email: str, conversation: dict):
    # Implementation for HubSpot API integration
    pass
```

### Cloud Storage (AWS S3)
```python
# Replace local file storage with S3
import boto3

s3_client = boto3.client('s3')

async def upload_to_s3(audio_data: bytes, filename: str):
    s3_client.put_object(
        Bucket=AWS_S3_BUCKET,
        Key=filename,
        Body=audio_data,
        ContentType='audio/mpeg'
    )
```

### Analytics Dashboard
- Add `/api/analytics` endpoint
- Track response times, user satisfaction
- Create admin dashboard component

## 🚨 Troubleshooting

### Common Issues

**1. CORS Errors**
- Ensure backend CORS is configured for frontend URL
- Check if both services are running

**2. Voice Recording Not Working**
- Grant microphone permissions in browser
- Use HTTPS in production for audio API access

**3. MongoDB Connection Issues**
- Check MongoDB is running: `mongosh`
- Verify connection string in .env
- For Atlas: check network access and credentials

**4. API Key Errors**
- Verify OpenAI API key has credits
- Check ElevenLabs API key is valid
- Ensure .env file is in correct location

**5. Audio Playback Issues**
- Check audio files are generated in `/audio_files`
- Verify ElevenLabs TTS is working
- Browser may block audio autoplay

### Logs and Debugging

```bash
# Backend logs
docker-compose logs backend

# Frontend logs  
docker-compose logs frontend

# Database logs
docker-compose logs mongodb

# Check audio files
ls backend/audio_files/
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes and test
4. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check troubleshooting section
2. Review API documentation
3. Check logs for specific errors
4. Create GitHub issue with details

## 🎯 Roadmap

- ✅ Phase 1: MVP with voice/text chat
- 🔄 Phase 2: CRM integration, cloud storage
- 📅 Phase 3: Multi-language, analytics, scaling