import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import MapView from './components/Map'
import Assistant from './components/Assistant'
import Simulation from './components/Simulation'
import Insights from './components/Insights'
import { API_BASE } from './api'

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'map' | 'assistant' | 'simulation' | 'insights'>('dashboard')
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(true)
  
  // Coordinates synced from assistant to map
  const [mapCenter, setMapCenter] = useState<[number, number]>([13.1, 80.6]) // default Chennai Zone B
  const [mapZoom, setMapZoom] = useState<number>(9)

  useEffect(() => {
    // Check backend connection and mode
    fetch(`${API_BASE}/api/insights/`)
      .then((res) => res.json())
      .then((data) => {
        // If data is received, check if it indicates demo or live
        // In this case, we determine based on settings or api response
        setIsDemoMode(true) // Default to true, or parse from backend if sent
        setLoading(false)
      })
      .catch(() => {
        // Fallback to offline demo mode
        setIsDemoMode(true)
        setLoading(false)
      })
  }, [])

  const handleLocateOnMap = (lat: number, lng: number) => {
    setMapCenter([lat, lng])
    setMapZoom(11)
    setActiveTab('map')
  }

  return (
    <Layout 
      activeTab={activeTab} 
      setActiveTab={setActiveTab} 
      isDemoMode={isDemoMode}
      loading={loading}
    >
      {activeTab === 'dashboard' && (
        <Dashboard onLocate={handleLocateOnMap} />
      )}
      {activeTab === 'map' && (
        <MapView center={mapCenter} zoom={mapZoom} onLocationChange={setMapCenter} />
      )}
      {activeTab === 'assistant' && (
        <Assistant onLocate={handleLocateOnMap} />
      )}
      {activeTab === 'simulation' && (
        <Simulation />
      )}
      {activeTab === 'insights' && (
        <Insights onLocate={handleLocateOnMap} />
      )}
    </Layout>
  )
}

export default App
