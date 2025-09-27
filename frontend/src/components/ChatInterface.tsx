import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import axios from 'axios'

interface Message {
  id: string
  text: string
  sender: 'user' | 'goddess'
  goddess?: string
  citations?: Citation[]
  timestamp: Date
}

interface Citation {
  title: string
  url: string
  source: string
  date?: string
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentGoddess, setCurrentGoddess] = useState<string>('athena')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)

    try {
      const response = await axios.post('/api/chat', {
        message: inputText,
        goddess: currentGoddess
      })

      const goddessMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response,
        sender: 'goddess',
        goddess: response.data.goddess,
        citations: response.data.citations,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, goddessMessage])
      setCurrentGoddess(response.data.goddess)
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'I apologize, but I encountered an error. Please try again.',
        sender: 'goddess',
        goddess: currentGoddess,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getGoddessInfo = (goddess: string) => {
    const goddessMap: Record<string, { name: string; color: string }> = {
      athena: { name: 'Athena', color: 'goddess-athena' },
      aphrodite: { name: 'Aphrodite', color: 'goddess-aphrodite' },
      hera: { name: 'Hera', color: 'goddess-hera' }
    }
    return goddessMap[goddess] || { name: 'Gaia', color: 'gray-500' }
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-200px)] flex flex-col">
      {/* Chat Header */}
      <div className="bg-white rounded-t-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 bg-${getGoddessInfo(currentGoddess).color} rounded-full flex items-center justify-center`}>
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">
              {getGoddessInfo(currentGoddess).name}
            </h2>
            <p className="text-sm text-gray-500">Your divine guide</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 bg-gray-50 border-x border-gray-200 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Start a conversation with your goddess guide!</p>
            <p className="text-sm mt-2">Ask about academics, well-being, career, or NJIT resources.</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`chat-message ${message.sender}`}
          >
            <div className="flex items-start space-x-3">
              {message.sender === 'goddess' ? (
                <div className={`w-8 h-8 bg-${getGoddessInfo(message.goddess || currentGoddess).color} rounded-full flex items-center justify-center flex-shrink-0`}>
                  <Bot className="w-5 h-5 text-white" />
                </div>
              ) : (
                <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
              
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">
                    {message.sender === 'goddess' 
                      ? getGoddessInfo(message.goddess || currentGoddess).name
                      : 'You'
                    }
                  </span>
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                
                <p className="text-gray-800 whitespace-pre-wrap">
                  {message.text}
                </p>
                
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-sm font-medium text-gray-600">Resources:</p>
                    <div className="flex flex-wrap gap-2">
                      {message.citations.map((citation, index) => (
                        <a
                          key={index}
                          href={citation.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="citation-chip"
                        >
                          {citation.title}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="chat-message goddess">
            <div className="flex items-start space-x-3">
              <div className={`w-8 h-8 bg-${getGoddessInfo(currentGoddess).color} rounded-full flex items-center justify-center flex-shrink-0`}>
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">
                    {getGoddessInfo(currentGoddess).name}
                  </span>
                </div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white rounded-b-lg border border-gray-200 p-4">
        <div className="flex space-x-3">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask your goddess guide anything..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-goddess-athena focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputText.trim() || isLoading}
            className="px-4 py-2 bg-goddess-athena text-white rounded-lg hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
