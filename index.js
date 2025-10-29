import { useState, useRef, useEffect } from 'react'
import Head from 'next/head'

export default function Home() {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [userEmail, setUserEmail] = useState('')
  const [userId, setUserId] = useState('')
  
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize user session
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId')
    const storedUserEmail = localStorage.getItem('userEmail')
    
    if (storedUserId) setUserId(storedUserId)
    if (storedUserEmail) setUserEmail(storedUserEmail)
    
    // Generate userId if not exists
    if (!storedUserId) {
      const newUserId = 'user_' + Math.random().toString(36).substr(2, 9)
      setUserId(newUserId)
      localStorage.setItem('userId', newUserId)
    }
  }, [])

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return

    const userMessage = { 
      text: messageText, 
      type: 'user', 
      timestamp: new Date().toISOString() 
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          user_id: userId,
          user_email: userEmail || undefined
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()
      
      const aiMessage = {
        text: data.response,
        type: 'ai',
        timestamp: new Date().toISOString(),
        audioUrl: data.audio_url ? `http://localhost:8000${data.audio_url}` : null,
        conversationId: data.conversation_id
      }
      
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        text: 'क्षमा करें, मुझे एक त्रुटि आई। कृपया फिर से कोशिश करें।',
        type: 'ai',
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        await handleVoiceMessage(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('माइक्रोफोन तक पहुंच नहीं मिल सकी। कृपया अनुमतियों की जांच करें।')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const handleVoiceMessage = async (audioBlob) => {
    setIsLoading(true)
    
    const userMessage = { 
      text: '🎤 Voice message', 
      type: 'user', 
      timestamp: new Date().toISOString(),
      isVoice: true
    }
    
    setMessages(prev => [...prev, userMessage])

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'audio.wav')
      if (userId) formData.append('user_id', userId)
      if (userEmail) formData.append('user_email', userEmail)

      const response = await fetch('http://localhost:8000/api/voice', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to process voice message')
      }

      const data = await response.json()
      
      const aiMessage = {
        text: data.response,
        type: 'ai',
        timestamp: new Date().toISOString(),
        audioUrl: data.audio_url ? `http://localhost:8000${data.audio_url}` : null,
        conversationId: data.conversation_id,
        originalUserText: data.response // In voice mode, we show the transcribed text
      }
      
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error processing voice message:', error)
      const errorMessage = {
        text: 'क्षमा करें, मैं आपका वॉइस संदेश प्रोसेस नहीं कर सका। कृपया फिर से कोशिश करें।',
        type: 'ai',
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const playAudio = (audioUrl) => {
    const audio = new Audio(audioUrl)
    audio.play().catch(error => {
      console.error('Error playing audio:', error)
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSendMessage(inputText)
  }

  const updateUserEmail = () => {
    const email = prompt('बेहतर सहायता के लिए अपना ईमेल दर्ज करें:', userEmail)
    if (email && email.includes('@')) {
      setUserEmail(email)
      localStorage.setItem('userEmail', email)
    }
  }


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Head>
        <title>AI Customer Support</title>
        <meta name="description" content="AI-powered customer support with voice and text chat" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">
              🤖 AI Customer Support
            </h1>
            <p className="text-lg text-gray-600 mb-4">
              टेक्स्ट या वॉइस चैट के माध्यम से तुरंत मदद पाएं
            </p>
            <div className="flex justify-center items-center space-x-4 text-sm">
              <span className="text-gray-500">User ID: {userId}</span>
              <button 
                onClick={updateUserEmail}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
              >
                {userEmail ? userEmail : '+ ईमेल जोड़ें'}
              </button>
            </div>
            
          </div>

          {/* Chat Container */}
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Chat Messages */}
            <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-16">
                  <div className="text-6xl mb-4">💬</div>
                  <p className="text-xl">बातचीत शुरू करें!</p>
                  <p className="text-sm mt-2">संदेश टाइप करें या बोलने के लिए माइक्रोफोन पर क्लिक करें</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-sm lg:max-w-md px-4 py-3 rounded-2xl ${
                      message.type === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : message.isError
                        ? 'bg-red-100 text-red-700 border border-red-200'
                        : 'bg-white text-gray-800 shadow-sm border border-gray-200'
                    }`}>
                      <p className="text-sm">{message.text}</p>
                      {message.audioUrl && (
                        <button
                          onClick={() => playAudio(message.audioUrl)}
                          className="mt-2 flex items-center space-x-2 text-xs text-blue-600 hover:text-blue-800"
                        >
                          <span>🔊</span>
                          <span>Play Audio</span>
                        </button>
                      )}
                      <div className="text-xs opacity-70 mt-1">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white text-gray-800 px-4 py-3 rounded-2xl shadow-sm border border-gray-200">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-6 bg-white border-t border-gray-200">
              <form onSubmit={handleSubmit} className="flex items-end space-x-4">
                <div className="flex-1">
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="अपना संदेश यहाँ टाइप करें..."
                    rows="2"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSubmit(e)
                      }
                    }}
                  />
                </div>
                
                <div className="flex space-x-2">
                  {/* Voice Button */}
                  <button
                    type="button"
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isLoading}
                    className={`p-3 rounded-lg transition-all duration-200 ${
                      isRecording 
                        ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                    } disabled:opacity-50`}
                  >
                    {isRecording ? '⏹️' : '🎤'}
                  </button>
                  
                  {/* Send Button */}
                  <button
                    type="submit"
                    disabled={!inputText.trim() || isLoading}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    भेजें
                  </button>
                </div>
              </form>
              
              <div className="mt-3 text-xs text-gray-500 text-center">
                {isRecording ? (
                  <span className="text-red-500">🔴 रिकॉर्डिंग... समाप्त होने पर रोकें</span>
                ) : (
                  <span>भेजने के लिए Enter दबाएं, नई लाइन के लिए Shift+Enter</span>
                )}
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="mt-8 grid md:grid-cols-3 gap-6 text-center">
            <div className="p-6 bg-white rounded-lg shadow-sm">
              <div className="text-3xl mb-3">💬</div>
              <h3 className="font-semibold text-gray-800 mb-2">टेक्स्ट चैट</h3>
              <p className="text-sm text-gray-600">सवाल टाइप करें और तुरंत जवाब पाएं</p>
            </div>
            <div className="p-6 bg-white rounded-lg shadow-sm">
              <div className="text-3xl mb-3">🎤</div>
              <h3 className="font-semibold text-gray-800 mb-2">वॉइस चैट</h3>
              <p className="text-sm text-gray-600">स्वाभाविक रूप से बोलें और जवाब सुनें</p>
            </div>
            <div className="p-6 bg-white rounded-lg shadow-sm">
              <div className="text-3xl mb-3">🤖</div>
              <h3 className="font-semibold text-gray-800 mb-2">AI पावर्ड</h3>
              <p className="text-sm text-gray-600">उन्नत Gemini AI समझता है और मददगार जवाब देता है</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
