import { useState, useEffect, useRef } from 'react'
import { Send, User, Compass, HelpCircle, Locate, CheckCircle } from 'lucide-react'

interface AssistantProps {
  onLocate: (lat: number, lng: number) => void
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  timestamp: Date
}

export default function Assistant({ onLocate }: AssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text: (
        "### 🌊 Welcome to the AI Ocean Assistant\n\n" +
        "I am an intelligent decision-support agent connected to live Copernicus ocean sensors, " +
        "OBIS biodiversity records, and localized environmental models.\n\n" +
        "You can ask me questions using natural language. Try selecting a suggested prompt below or type your query in the field."
      ),
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState<string>('')
  const [sessionId] = useState<string>(() => `session-${Math.random().toString(36).substring(2, 9)}`)
  const [sending, setSending] = useState<boolean>(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const samplePrompts = [
    "Which area near Chennai has the highest tuna suitability?",
    "Which areas have abnormal temperature?",
    "Why is biodiversity risk high near Chennai?",
    "What happens if temperature increases by 2°C?"
  ]

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = (textToSend: string) => {
    if (!textToSend.trim() || sending) return
    
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: textToSend,
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setSending(true)

    fetch('/api/assistant/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonStringify({ message: textToSend, session_id: sessionId })
    })
      .then((res) => res.json())
      .then((data) => {
        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          text: data.message,
          timestamp: new Date()
        }
        setMessages((prev) => [...prev, assistantMsg])
        setSending(false)
      })
      .catch((err) => {
        console.error("Chat error", err)
        const errorMsg: ChatMessage = {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          text: "⚠️ *Error connecting to LLM Assistant backend. Please check network connection and ensure Django server is running.*",
          timestamp: new Date()
        }
        setMessages((prev) => [...prev, errorMsg])
        setSending(false)
      })
  }

  // Small helper to avoid JSX curly bracket json serialization issues
  function jsonStringify(obj: any) {
    return JSON.stringify(obj)
  }

  // Helper to parse potential lat/lng coords and show a dynamic button
  const renderMessageText = (text: string) => {
    // Basic Markdown renderer parser
    const lines = text.split('\n')
    
    // Check if Chennai coordinates exist in message to render a Map Locate button
    let locateButtons: React.ReactNode[] = []
    
    if (text.includes("Zone B") || text.includes("Zone B (Shelf)")) {
      locateButtons.push(
        <button
          key="loc-b"
          onClick={() => onLocate(13.1, 80.6)}
          className="mt-2 text-[10px] font-mono border border-ocean-cyan text-ocean-cyan bg-ocean-cyan/5 hover:bg-ocean-cyan/15 px-2.5 py-1 rounded flex items-center space-x-1"
        >
          <Locate className="h-3 w-3" />
          <span>Sync Zone B Map Layer</span>
        </button>
      )
    }
    if (text.includes("Zone A")) {
      locateButtons.push(
        <button
          key="loc-a"
          onClick={() => onLocate(13.0, 80.3)}
          className="mt-2 text-[10px] font-mono border border-ocean-cyan text-ocean-cyan bg-ocean-cyan/5 hover:bg-ocean-cyan/15 px-2.5 py-1 rounded flex items-center space-x-1"
        >
          <Locate className="h-3 w-3" />
          <span>Sync Zone A Map Layer</span>
        </button>
      )
    }
    if (text.includes("Zone C")) {
      locateButtons.push(
        <button
          key="loc-c"
          onClick={() => onLocate(13.2, 81.0)}
          className="mt-2 text-[10px] font-mono border border-ocean-cyan text-ocean-cyan bg-ocean-cyan/5 hover:bg-ocean-cyan/15 px-2.5 py-1 rounded flex items-center space-x-1"
        >
          <Locate className="h-3 w-3" />
          <span>Sync Zone C Map Layer</span>
        </button>
      )
    }

    return (
      <div className="space-y-1">
        {lines.map((line, idx) => {
          let cleaned = line
          let isHeader = false
          let isSubHeader = false
          let isBullet = false

          if (line.startsWith('### ')) {
            cleaned = line.substring(4)
            isSubHeader = true
          } else if (line.startsWith('## ') || line.startsWith('# ')) {
            cleaned = line.replace(/^[#]+\s/, '')
            isHeader = true
          } else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            cleaned = line.trim().substring(2)
            isBullet = true
          }

          // Parse bold markdown **text**
          const parts = cleaned.split(/\*\*([^*]+)\*\*/g)
          const content = parts.map((part, i) => (i % 2 === 1 ? <strong key={i} className="text-white font-semibold">{part}</strong> : part))

          if (isHeader) return <h3 key={idx} className="text-sm font-bold text-white uppercase tracking-wider mt-3 mb-1.5">{content}</h3>
          if (isSubHeader) return <h4 key={idx} className="text-xs font-semibold text-ocean-cyan font-mono mt-2.5 mb-1">{content}</h4>
          if (isBullet) return <div key={idx} className="pl-4 text-[12px] text-slate-300 leading-relaxed flex items-start space-x-1.5"><span className="text-ocean-cyan mt-0.5">•</span><span>{content}</span></div>

          return <p key={idx} className="text-[12px] text-slate-300 leading-relaxed">{content}</p>
        })}
        {locateButtons.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-ocean-light/30">
            {locateButtons}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col max-w-[1000px] mx-auto bg-ocean-dark border border-ocean-light rounded">
      {/* Chat Header */}
      <div className="p-4 border-b border-ocean-light flex items-center justify-between select-none">
        <div className="flex items-center space-x-2.5">
          <Compass className="h-5 w-5 text-ocean-cyan" />
          <div>
            <h3 className="text-xs font-mono font-bold tracking-wider text-white uppercase">AI OCEAN INTELLIGENCE ASSISTANT</h3>
            <p className="text-[10px] text-slate-400 font-mono">Grounded via Copernicus & OBIS RAG Pipelines</p>
          </div>
        </div>
        <div className="flex items-center space-x-1 text-[10px] font-mono text-emerald-400 bg-emerald-950/45 px-2 py-0.5 rounded border border-emerald-900/50">
          <CheckCircle className="h-3 w-3" />
          <span>Active RAG context loaded</span>
        </div>
      </div>

      {/* Suggestion Prompts */}
      {messages.length === 1 && (
        <div className="p-4 bg-ocean-darkest/50 border-b border-ocean-light select-none">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-2 flex items-center space-x-1">
            <HelpCircle className="h-3.5 w-3.5" />
            <span>Suggested Questions:</span>
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p)}
                className="text-left text-[11px] bg-ocean-medium/30 hover:bg-ocean-medium/70 text-slate-300 px-3 py-2 rounded border border-ocean-light/50 transition duration-150"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => {
          const isAssistant = m.role === 'assistant'
          return (
            <div
              key={m.id}
              className={`flex items-start space-x-3 max-w-[85%] ${
                isAssistant ? '' : 'ml-auto flex-row-reverse space-x-reverse'
              }`}
            >
              {/* Avatar */}
              <div
                className={`h-8 w-8 rounded flex items-center justify-center shrink-0 text-white ${
                  isAssistant ? 'bg-ocean-medium border border-ocean-light' : 'bg-ocean-cyan'
                }`}
              >
                {isAssistant ? <Compass className="h-4.5 w-4.5 text-ocean-cyan" /> : <User className="h-4.5 w-4.5" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`p-4 rounded border text-xs leading-relaxed ${
                  isAssistant
                    ? 'bg-ocean-medium/15 border-ocean-light text-slate-200'
                    : 'bg-ocean-medium border-ocean-light text-white font-medium'
                }`}
              >
                {typeof m.text === 'string' ? renderMessageText(m.text) : m.text}
                <div className="text-[9px] text-slate-500 font-mono mt-2 text-right">
                  {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          )
        })}

        {sending && (
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 pl-4 animate-pulse">
            <div className="animate-spin rounded-full h-3.5 w-3.5 border-t border-b border-ocean-cyan"></div>
            <span>RAG database scan and model inference in progress...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Field Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleSend(input)
        }}
        className="p-4 border-t border-ocean-light flex items-center space-x-3 bg-ocean-darkest/45"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about Tuna suitability near Chennai or active temperature anomalies..."
          className="flex-1 bg-ocean-dark border border-ocean-light rounded px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-sans"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          className="bg-ocean-cyan hover:bg-ocean-teal disabled:bg-ocean-medium disabled:text-slate-500 text-white font-semibold px-4 py-2.5 rounded transition flex items-center space-x-1 shrink-0"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}
