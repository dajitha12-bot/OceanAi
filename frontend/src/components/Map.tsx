import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap } from 'react-leaflet'
import { AlertCircle, Eye, EyeOff } from 'lucide-react'

// Import Leaflet styles
import 'leaflet/dist/leaflet.css'

interface MapViewProps {
  center: [number, number]
  zoom: number
  onLocationChange: (center: [number, number]) => void
}

// Map controller to dynamically update view when props change
function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom, { animate: true })
  }, [center, zoom, map])
  return null
}

export default function MapView({ center, zoom, onLocationChange }: MapViewProps) {
  const [layersData, setLayersData] = useState<any>(null)
  const [selectedLayer, setSelectedLayer] = useState<'temp' | 'sal' | 'chlor' | 'suitability' | 'risk'>('suitability')
  const [showAnomalies, setShowAnomalies] = useState<boolean>(true)
  const [loading, setLoading] = useState<boolean>(true)
  
  const geoJsonRef = useRef<any>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/map/`)
      .then((res) => res.json())
      .then((data) => {
        setLayersData(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error("Error loading map GeoJSON", err)
        setLoading(false)
      })
  }, [])

  // Force re-render of GeoJSON layer when selectedLayer changes
  useEffect(() => {
    if (geoJsonRef.current) {
      geoJsonRef.current.clearLayers()
      if (layersData?.regions) {
        geoJsonRef.current.addData(layersData.regions)
      }
    }
  }, [selectedLayer, layersData])

  // Science color grading function
  const getColor = (value: number, type: string) => {
    if (type === 'temp') {
      // Temp scale: 25C (blue) to 32C (red)
      if (value > 30.5) return '#f43f5e' // red
      if (value > 29.0) return '#fb923c' // orange
      if (value > 27.5) return '#facc15' // yellow
      if (value > 26.0) return '#22d3ee' // cyan
      return '#3b82f6' // blue
    }
    if (type === 'sal') {
      // Salinity scale: 30 PSU (light green) to 36 PSU (deep blue)
      if (value > 35.0) return '#1d4ed8'
      if (value > 34.2) return '#3b82f6'
      if (value > 33.5) return '#60a5fa'
      if (value > 32.0) return '#34d399'
      return '#a7f3d0'
    }
    if (type === 'chlor') {
      // Chlorophyll scale: 0.1 mg/m3 (clear blue) to 5.0 mg/m3 (algal bloom green)
      if (value > 3.0) return '#15803d'
      if (value > 2.0) return '#22c55e'
      if (value > 1.0) return '#86efac'
      if (value > 0.4) return '#a7f3d0'
      return '#e0f2fe'
    }
    if (type === 'suitability') {
      // Tuna suitability: 0% (grey) to 100% (bright cyan-blue)
      if (value > 80) return '#00b4d8'
      if (value > 65) return '#0077b6'
      if (value > 45) return '#03045e'
      if (value > 20) return '#1e1b4b'
      return '#475569'
    }
    if (type === 'risk') {
      // Biodiversity Risk: 0% (green) to 100% (red)
      if (value > 70) return '#b91c1c' // high risk red
      if (value > 45) return '#d97706' // mod risk amber
      if (value > 25) return '#eab308' // yellow
      return '#16a34a' // low risk green
    }
    return '#cbd5e1'
  }

  // Styles GeoJSON features based on currently active visualization filter
  const styleFeature = (feature: any) => {
    let value = 0
    const props = feature.properties
    
    if (selectedLayer === 'temp') value = props.temperature
    else if (selectedLayer === 'sal') value = props.salinity
    else if (selectedLayer === 'chlor') value = props.chlorophyll
    else if (selectedLayer === 'suitability') value = props.tuna_suitability
    else if (selectedLayer === 'risk') value = props.biodiversity_risk

    const fillColor = getColor(value, selectedLayer)

    return {
      fillColor: fillColor,
      weight: 1.5,
      opacity: 0.8,
      color: '#3a506b', // Border slate
      dashArray: '3',
      fillOpacity: 0.45
    }
  }

  const onEachFeature = (feature: any, layer: any) => {
    const props = feature.properties
    
    // Custom tooltips on hover
    layer.bindTooltip(`
      <div class="font-sans text-[11px]">
        <b class="text-white">${props.name}</b><br/>
        Tuna Suitability: <b>${props.tuna_suitability}%</b><br/>
        Biodiversity Risk: <b>${props.biodiversity_risk}% (${props.risk_level})</b>
      </div>
    `, { sticky: true })

    // Zoom/center on click
    layer.on({
      click: (e: any) => {
        const bounds = e.target.getBounds()
        onLocationChange([bounds.getCenter().lat, bounds.getCenter().lng])
      }
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-ocean-cyan"></div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col relative">
      {/* Map Control Floating Bar */}
      <div className="absolute top-4 right-4 z-[1000] bg-ocean-dark/90 backdrop-blur border border-ocean-light p-3.5 rounded shadow-2xl w-60 select-none text-xs">
        <div className="border-b border-ocean-light/50 pb-1.5 mb-2">
          <h4 className="font-mono font-bold tracking-wider text-slate-400 uppercase">LAYER CONTROL PANEL</h4>
        </div>
        
        {/* Layer Selector */}
        <div className="space-y-1">
          {[
            { id: 'suitability', label: '🐟 Fisheries Suitability' },
            { id: 'risk', label: '🪸 Biodiversity Risk' },
            { id: 'temp', label: '🌡️ Temperature (SST)' },
            { id: 'sal', label: '🧂 Salinity (PSU)' },
            { id: 'chlor', label: '🌿 Chlorophyll (mg/m³)' },
          ].map((layer) => (
            <button
              key={layer.id}
              onClick={() => setSelectedLayer(layer.id as any)}
              className={`w-full text-left px-2.5 py-1.5 rounded transition ${
                selectedLayer === layer.id
                  ? 'bg-ocean-medium text-white font-semibold border-l-2 border-ocean-cyan'
                  : 'text-slate-400 hover:bg-ocean-medium/55 hover:text-slate-200'
              }`}
            >
              {layer.label}
            </button>
          ))}
        </div>

        {/* Anomaly Toggle */}
        <div className="mt-4 pt-3 border-t border-ocean-light/50 flex items-center justify-between">
          <span className="text-slate-400 flex items-center space-x-1">
            <AlertCircle className="h-3.5 w-3.5 text-rose-500" />
            <span>Show Anomalies</span>
          </span>
          <button
            onClick={() => setShowAnomalies(!showAnomalies)}
            className="text-slate-400 hover:text-white"
          >
            {showAnomalies ? <Eye className="h-4 w-4 text-ocean-cyan" /> : <EyeOff className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Floating Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-ocean-dark/95 backdrop-blur border border-ocean-light p-3 rounded shadow-2xl text-[10px] font-mono select-none">
        <h5 className="font-bold mb-1.5 text-slate-400 uppercase tracking-wide">
          {selectedLayer === 'temp' && 'Temperature (°C)'}
          {selectedLayer === 'sal' && 'Salinity (PSU)'}
          {selectedLayer === 'chlor' && 'Chlorophyll (mg/m³)'}
          {selectedLayer === 'suitability' && 'Tuna Suitability (%)'}
          {selectedLayer === 'risk' && 'Biodiversity Risk (%)'}
        </h5>
        
        <div className="flex items-center space-x-1">
          {selectedLayer === 'temp' && (
            <>
              <div className="w-4 h-3 bg-[#3b82f6]"></div><span>&lt;26</span>
              <div className="w-4 h-3 bg-[#22d3ee]"></div><span>27</span>
              <div className="w-4 h-3 bg-[#facc15]"></div><span>28</span>
              <div className="w-4 h-3 bg-[#fb923c]"></div><span>30</span>
              <div className="w-4 h-3 bg-[#f43f5e]"></div><span>31+</span>
            </>
          )}
          {selectedLayer === 'sal' && (
            <>
              <div className="w-4 h-3 bg-[#a7f3d0]"></div><span>&lt;32</span>
              <div className="w-4 h-3 bg-[#34d399]"></div><span>33</span>
              <div className="w-4 h-3 bg-[#60a5fa]"></div><span>34</span>
              <div className="w-4 h-3 bg-[#3b82f6]"></div><span>35</span>
              <div className="w-4 h-3 bg-[#1d4ed8]"></div><span>35.5+</span>
            </>
          )}
          {selectedLayer === 'chlor' && (
            <>
              <div className="w-4 h-3 bg-[#e0f2fe]"></div><span>&lt;0.4</span>
              <div className="w-4 h-3 bg-[#a7f3d0]"></div><span>1.0</span>
              <div className="w-4 h-3 bg-[#86efac]"></div><span>2.0</span>
              <div className="w-4 h-3 bg-[#22c55e]"></div><span>3.0</span>
              <div className="w-4 h-3 bg-[#15803d]"></div><span>3.5+</span>
            </>
          )}
          {selectedLayer === 'suitability' && (
            <>
              <div className="w-4 h-3 bg-[#475569]"></div><span>&lt;20</span>
              <div className="w-4 h-3 bg-[#1e1b4b]"></div><span>40</span>
              <div className="w-4 h-3 bg-[#03045e]"></div><span>60</span>
              <div className="w-4 h-3 bg-[#0077b6]"></div><span>80</span>
              <div className="w-4 h-3 bg-[#00b4d8]"></div><span>90+</span>
            </>
          )}
          {selectedLayer === 'risk' && (
            <>
              <div className="w-4 h-3 bg-[#16a34a]"></div><span>Low (&lt;25)</span>
              <div className="w-4 h-3 bg-[#eab308]"></div><span>Mod (35)</span>
              <div className="w-4 h-3 bg-[#d97706]"></div><span>High (50)</span>
              <div className="w-4 h-3 bg-[#b91c1c]"></div><span>Crit (70+)</span>
            </>
          )}
        </div>
      </div>

      {/* Leaflet Map Container */}
      <div className="flex-1 rounded overflow-hidden border border-ocean-light z-0">
        <MapContainer
          center={center}
          zoom={zoom}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <MapController center={center} zoom={zoom} />
          
          {/* ESRI World Ocean Basemap */}
          <TileLayer
            attribution='Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
            maxZoom={13}
          />

          {/* Region Polygons layer */}
          {layersData?.regions && (
            <GeoJSON
              ref={geoJsonRef}
              data={layersData.regions}
              style={styleFeature}
              onEachFeature={onEachFeature}
            />
          )}

          {/* Anomaly Point Overlays */}
          {showAnomalies && layersData?.anomalies?.features?.map((feat: any) => {
            const [lng, lat] = feat.geometry.coordinates
            const props = feat.properties
            return (
              <CircleMarker
                key={props.id}
                center={[lat, lng]}
                radius={8}
                pathOptions={{
                  fillColor: '#ef4444',
                  fillOpacity: 0.6,
                  weight: 2,
                  color: '#ef4444'
                }}
              >
                <Popup>
                  <div className="font-sans text-[11px] leading-relaxed">
                    <h5 className="font-bold text-rose-400 flex items-center space-x-1 uppercase mb-1">
                      <span>⚠️ {props.severity} severity Anomaly</span>
                    </h5>
                    Variable: <b>{props.parameter.toUpperCase()}</b><br/>
                    Observed Value: <span className="font-mono">{props.observed_value}</span><br/>
                    Baseline Expected: <span className="font-mono">{props.expected_value}</span><br/>
                    Coordinates: <span className="font-mono">({lat.toFixed(3)}°N, {lng.toFixed(3)}°E)</span><br/>
                    Timestamp: <span>{props.timestamp}</span><br/>
                    Algorithm: <span>{props.model_method}</span>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>
    </div>
  )
}
