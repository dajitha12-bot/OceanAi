import { useState, useEffect, useRef } from 'react'
import { Send, User, Compass, HelpCircle, Locate, CheckCircle } from 'lucide-react'
import { API_BASE } from '../api'

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

    fetch(`${API_BASE}/api/assistant/chat/`, {
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

  function jsonStringify(obj: any) {
    return JSON.stringify(obj)
  }

  const renderMessageText = (text: string) => {
    const lines = text.split('\n')
    let locateButtons: React.ReactNode[] = []
    
    if (text.includes("Zone B") || text.includes("Zone B (Shelf)")) {
      locateButtons.push(
        <button
          key="loc-b"
          onClick={() => onLocate(13.1, 80.6)}
          className="mt-2 text-[10px] font-mono border border-ocean-cyan text-ocean-cyan bg-sky-50 hover:bg-sky-100 px-3 py-1 rounded-md flex items-center space-x-1 font-semibold"
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
          className="mt-2 text-[10px] font-mono border border-ocean-cyan text-ocean-cyan bg-sky-50 hover:bg-sky-100 px-3 py-1 rounded-md flex items-center space-x-1 font-semibold"
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
          className="mt-2 text-[10px] font-mono border border-ocean-cyan text-ocean-cyan bg-sky-50 hover:bg-sky-100 px-3 py-1 rounded-md flex items-center space-x-1 font-semibold"
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

          const parts = cleaned.split(/\*\*([^*]+)\*\*/g)
          const content = parts.map((part, i) => (i % 2 === 1 ? <strong key={i} className="text-ocean-textDark font-bold">{part}</strong> : part))

          if (isHeader) return <h3 key={idx} className="text-sm font-bold text-ocean-textDark uppercase tracking-wider mt-3 mb-1.5">{content}</h3>
          if (isSubHeader) return <h4 key={idx} className="text-xs font-bold text-ocean-cyan font-mono mt-2.5 mb-1">{content}</h4>
          if (isBullet) return <div key={idx} className="pl-4 text-[12px] text-slate-700 leading-relaxed flex items-start space-x-1.5"><span className="text-ocean-cyan mt-0.5 font-bold">•</span><span>{content}</span></div>

          return <p key={idx} className="text-[12px] text-slate-700 leading-relaxed">{content}</p>
        })}
        {locateButtons.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-slate-200">
            {locateButtons}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col max-w-[1000px] mx-auto bg-white border border-ocean-waterBorder rounded-xl shadow-sm overflow-hidden">
      {/* Chat Header */}
      <div className="p-4 bg-sky-50/80 border-b border-ocean-waterBorder flex items-center justify-between select-none">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white rounded-lg shadow-xs text-ocean-cyan">
            <Compass className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-xs font-mono font-bold tracking-wider text-ocean-textDark uppercase">AI OCEAN INTELLIGENCE ASSISTANT</h3>
            <p className="text-[10px] text-slate-500 font-mono">Grounded via Copernicus & OBIS RAG Pipelines</p>
          </div>
        </div>
        <div className="flex items-center space-x-1.5 text-[10px] font-mono text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full font-semibold border border-emerald-200">
          <CheckCircle className="h-3.5 w-3.5" />
          <span>Active RAG Context Loaded</span>
        </div>
      </div>

      {/* Suggestion Prompts */}
      {messages.length === 1 && (
        <div className="p-5 bg-sky-50/40 border-b border-ocean-waterBorder select-none">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-2.5 flex items-center space-x-1 font-bold">
            <HelpCircle className="h-3.5 w-3.5 text-ocean-cyan" />
            <span>Suggested Questions:</span>
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(p)}
                className="text-left text-[11px] bg-white hover:bg-sky-50 text-slate-700 hover:text-ocean-cyan px-3.5 py-2.5 rounded-lg border border-sky-200 transition duration-150 shadow-2xs font-medium"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-ocean-waterLight/40">
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
                className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 shadow-xs ${
                  isAssistant ? 'bg-white border border-sky-200 text-ocean-cyan' : 'bg-ocean-cyan text-white'
                }`}
              >
                {isAssistant ? <Compass className="h-4.5 w-4.5" /> : <User className="h-4.5 w-4.5" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`p-4 rounded-xl border text-xs leading-relaxed shadow-2xs ${
                  isAssistant
                    ? 'bg-white border-ocean-waterBorder text-ocean-textDark'
                    : 'bg-ocean-cyan border-ocean-cyan text-white font-medium shadow-sm'
                }`}
              >
                {typeof m.text === 'string' ? renderMessageText(m.text) : m.text}
                <div className={`text-[9px] font-mono mt-2 text-right ${isAssistant ? 'text-slate-400' : 'text-sky-100'}`}>
                  {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          )
        })}

        {sending && (
          <div className="flex items-center space-x-2 text-xs font-mono text-ocean-cyan pl-4 animate-pulse font-semibold">
            <div className="animate-spin rounded-full h-3.5 w-3.5 border-t-2 border-b-2 border-ocean-cyan"></div>
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
        className="p-4 border-t border-ocean-waterBorder flex items-center space-x-3 bg-white"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about Tuna suitability near Chennai or active temperature anomalies..."
          className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 text-xs text-ocean-textDark placeholder-slate-400 focus:outline-none focus:border-ocean-cyan focus:bg-white font-sans transition"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          className="bg-ocean-cyan hover:bg-sky-600 disabled:bg-slate-200 disabled:text-slate-400 text-white font-semibold px-4 py-2.5 rounded-lg transition flex items-center space-x-1 shrink-0 shadow-sm"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}
