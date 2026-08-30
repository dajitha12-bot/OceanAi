import React from 'react'
import { LayoutDashboard, Map, MessageSquare, Sliders, Lightbulb, Compass, AlertCircle } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
  activeTab: string
  setActiveTab: (tab: 'dashboard' | 'map' | 'assistant' | 'simulation' | 'insights') => void
  isDemoMode: boolean
  loading: boolean
}

export default function Layout({ children, activeTab, setActiveTab, isDemoMode, loading }: LayoutProps) {
  const menuItems = [
    { id: 'dashboard', label: 'AI Ocean Dashboard', icon: LayoutDashboard },
    { id: 'map', label: 'Ocean Intelligence Map', icon: Map },
    { id: 'assistant', label: 'AI Ocean Assistant', icon: MessageSquare },
    { id: 'simulation', label: 'Prediction & What-If', icon: Sliders },
    { id: 'insights', label: 'AI Insights', icon: Lightbulb },
  ]

  return (
    <div className="flex h-screen bg-ocean-darkest text-slate-200">
      {/* Sidebar */}
      <aside className="w-64 bg-ocean-dark border-r border-ocean-light flex flex-col justify-between select-none">
        <div>
          {/* Logo / Header */}
          <div className="p-5 border-b border-ocean-light flex items-center space-x-3">
            <Compass className="h-6 w-6 text-ocean-cyan animate-pulse" />
            <div>
              <h1 className="font-semibold text-white tracking-wider text-sm">OCEAN INTEL</h1>
              <p className="text-[10px] text-slate-400 font-mono">DECISION PLATFORM</p>
            </div>
          </div>
          
          {/* Nav Items */}
          <nav className="p-4 space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`flex items-center space-x-3 w-full px-4 py-3 rounded text-sm transition-all duration-150 text-left ${
                    isActive
                      ? 'bg-ocean-medium text-white border-l-2 border-ocean-cyan font-medium'
                      : 'text-slate-400 hover:bg-ocean-medium/50 hover:text-slate-200'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-ocean-cyan' : ''}`} />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Sidebar Footer / Connection Status */}
        <div className="p-4 border-t border-ocean-light bg-ocean-darkest/45">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`h-2.5 w-2.5 rounded-full ${isDemoMode ? 'bg-amber-500' : 'bg-emerald-500'} animate-ping`}></div>
              <span className="text-[11px] font-mono tracking-wider font-semibold">
                {isDemoMode ? 'DATA MODE: DEMO' : 'DATA MODE: LIVE'}
              </span>
            </div>
            {isDemoMode && (
              <div className="group relative">
                <AlertCircle className="h-4 w-4 text-amber-500 cursor-pointer" />
                <div className="absolute bottom-6 right-0 w-48 bg-ocean-medium border border-ocean-light text-[10px] p-2 rounded hidden group-hover:block z-50 shadow-xl">
                  Running on fallback datasets. Configure Copernicus & LLM keys in .env for live mode.
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Global Header */}
        <header className="h-16 bg-ocean-dark border-b border-ocean-light flex items-center justify-between px-6 z-10">
          <div className="flex items-center space-x-3">
            <span className="text-xl">🌊</span>
            <span className="font-semibold text-white tracking-wide text-md">
              AI Ocean Intelligence & Conversational Decision Platform
            </span>
          </div>
          <div className="flex items-center space-x-4 text-xs font-mono">
            <span className="text-slate-400">SYS_STATUS:</span>
            <span className="text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/50">
              OPERATIONAL
            </span>
          </div>
        </header>

        {/* Dynamic Tab Body */}
        <main className="flex-1 overflow-y-auto bg-ocean-darkest p-6 relative">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-ocean-darkest">
              <div className="flex flex-col items-center space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-ocean-cyan"></div>
                <p className="text-xs font-mono text-slate-400">Loading AI Insights and Map Data...</p>
              </div>
            </div>
          ) : (
            children
          )}
        </main>
      </div>
    </div>
  )
}
