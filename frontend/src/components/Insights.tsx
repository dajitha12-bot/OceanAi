import { useState, useEffect } from 'react'
import { AlertCircle, ShieldAlert, CheckCircle2, Locate, RefreshCw, Layers } from 'lucide-react'

interface InsightsProps {
  onLocate: (lat: number, lng: number) => void
}

export default function Insights({ onLocate }: InsightsProps) {
  const [insights, setInsights] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [recalculating, setRecalculating] = useState<boolean>(false)

  const fetchInsightsData = () => {
    setLoading(true)
    fetch('/api/insights/')
      .then(res => res.json())
      .then(data => {
        setInsights(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Error loading insights", err)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchInsightsData()
  }, [])

  const triggerRecalculate = () => {
    setRecalculating(true)
    // 1. Recalculate Biodiversity Risk Indicators in backend
    fetch('/api/biodiversity/indicators/recalculate/', { method: 'POST' })
      .then(() => {
        // 2. Scan recent observations for anomalies
        return fetch('/api/anomalies/scan/', { method: 'POST' })
      })
      .then(() => {
        // 3. Generate future predictions/forecasts
        return fetch('/api/predictions/generate-forecasts/', { method: 'POST' })
      })
      .then(() => {
        // Refresh insights
        fetchInsightsData()
        setRecalculating(false)
      })
      .catch((err) => {
        console.error("Recalculation error", err)
        setRecalculating(false)
      })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-ocean-cyan"></div>
      </div>
    )
  }

  const activeAnoms = insights?.anomalies ?? []
  const riskZones = insights?.biodiversity_risks ?? []
  const suitInsights = insights?.fisheries_suitability ?? {}

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto select-none">
      {/* Header */}
      <div className="border-b border-ocean-light pb-4 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">AI INSIGHTS & ECOSYSTEM ALERTS</h2>
          <p className="text-xs text-slate-400 font-mono">ENVIRONMENTAL RISK WATCH & HARVEST RECOMMENDATIONS</p>
        </div>
        <button
          onClick={triggerRecalculate}
          disabled={recalculating}
          className="bg-ocean-medium hover:bg-ocean-light disabled:bg-ocean-dark border border-ocean-light transition text-white px-3.5 py-1.5 rounded font-mono text-[10px] flex items-center space-x-1.5"
        >
          <RefreshCw className={`h-3 w-3 ${recalculating ? 'animate-spin' : ''}`} />
          <span>{recalculating ? 'RECALCULATING TENSORS...' : 'RE-RUN AI MODELS'}</span>
        </button>
      </div>

      {/* Grid of Anomalies & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Environmental Anomalies Panel */}
        <div className="bg-ocean-dark border border-ocean-light rounded p-5 space-y-4 lg:col-span-1">
          <div className="border-b border-ocean-light/50 pb-2 mb-2 flex items-center justify-between">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">ACTIVE ANOMALY DETECTIONS</h3>
            <span className="text-[10px] font-mono text-slate-500">Isolation Forest</span>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[420px] pr-1.5">
            {activeAnoms.length > 0 ? (
              activeAnoms.map((an: any) => (
                <div 
                  key={an.id} 
                  className={`border p-3.5 rounded flex flex-col justify-between space-y-2.5 ${
                    an.severity === 'High' 
                      ? 'bg-rose-950/15 border-rose-900/50' 
                      : 'bg-amber-950/15 border-amber-900/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${an.severity === 'High' ? 'bg-rose-500 text-white' : 'bg-amber-500 text-black'}`}>
                      {an.severity} SEVERITY
                    </span>
                    <button
                      onClick={() => onLocate(an.latitude, an.longitude)}
                      className="text-ocean-cyan hover:underline text-[10px] font-mono flex items-center space-x-1"
                    >
                      <Locate className="h-3 w-3" />
                      <span>Locate</span>
                    </button>
                  </div>
                  <div className="text-xs text-slate-300">
                    Anomaly detected in <b>{an.parameter.toUpperCase()}</b>: <span className="text-white font-mono font-semibold">{an.observed_value}</span> vs normal baseline <span className="text-slate-400 font-mono">{an.expected_value}</span>
                  </div>
                  <div className="text-[9px] font-mono text-slate-500 flex justify-between">
                    <span>COORD: ({an.latitude.toFixed(2)}, {an.longitude.toFixed(2)})</span>
                    <span>{new Date(an.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-slate-500 space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                <p className="text-[11px] font-mono">No active anomalies detected in scanning history.</p>
              </div>
            )}
          </div>
        </div>

        {/* Biodiversity Risks & Recommendations */}
        <div className="bg-ocean-dark border border-ocean-light rounded p-5 space-y-4 lg:col-span-2">
          <div className="border-b border-ocean-light/50 pb-2 mb-2">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">BIODIVERSITY RISKS BY STATION</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {riskZones.map((z: any, idx: number) => {
              // Standard coordinates for Zone A, B, C around Chennai
              const lat = 13.0 + idx * 0.1
              const lng = 80.3 + idx * 0.3
              
              return (
                <div key={idx} className="bg-ocean-medium/20 border border-ocean-light/40 p-4 rounded flex flex-col justify-between space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-xs font-bold text-white">{z.region_name}</h4>
                      <p className="text-[9px] font-mono text-slate-500 uppercase">{z.source}</p>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${z.risk_level === 'High' ? 'bg-rose-950/40 text-rose-400 border border-rose-900/40' : z.risk_level === 'Moderate' ? 'bg-amber-950/40 text-amber-400 border border-amber-900/40' : 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/40'}`}>
                      {z.risk_level} RISK ({z.risk_score}%)
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-400">
                    <div>
                      <span className="text-[9px] block text-slate-500">SPECIES COUNT</span>
                      <span className="text-white font-semibold">{z.species_count} species</span>
                    </div>
                    <div>
                      <span className="text-[9px] block text-slate-500">OCCURRENCES</span>
                      <span className="text-white font-semibold">{z.occurrence_count} records</span>
                    </div>
                    <div>
                      <span className="text-[9px] block text-slate-500">SHANNON INDEX</span>
                      <span className="text-white font-semibold">{z.shannon_index ? z.shannon_index.toFixed(2) : '1.14'}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-ocean-light/30 flex justify-between items-center">
                    <span className="text-[10px] text-slate-500 font-mono">COORD: ({lat.toFixed(2)}°N, {lng.toFixed(2)}°E)</span>
                    <button
                      onClick={() => onLocate(lat, lng)}
                      className="text-ocean-cyan hover:text-white transition flex items-center space-x-1 text-[10px] font-mono"
                    >
                      <Locate className="h-3.5 w-3.5" />
                      <span>Locate region</span>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* AI Decision Recommendations Report Card */}
          <div className="bg-ocean-medium/15 border border-ocean-light/45 p-4 rounded space-y-3 mt-4 select-text">
            <h4 className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase flex items-center space-x-1.5">
              <Layers className="h-4 w-4 text-ocean-cyan" />
              <span>AI DECISION-SUPPORT REPORT</span>
            </h4>
            <div className="space-y-2 text-xs leading-relaxed text-slate-300">
              {insights?.recommendations?.map((rec: string, idx: number) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-ocean-cyan font-bold">•</span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fisheries Suitability Analysis Card */}
      {suitInsights.zones && (
        <div className="bg-ocean-dark border border-ocean-light rounded p-5 space-y-4">
          <div className="border-b border-ocean-light/50 pb-2 mb-2 flex justify-between items-center">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">SPECIES SUITABILITY PROFILE: {suitInsights.species}</h3>
            <span className="text-[10px] font-mono text-slate-500">Model: {suitInsights.model_method}</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Metrics */}
            <div className="bg-ocean-medium/20 border border-ocean-light/40 p-4 rounded flex flex-col justify-between space-y-4 lg:col-span-1">
              <div>
                <span className="text-[10px] font-mono text-slate-500">RECOMMENDED HARVEST SECTOR</span>
                <h4 className="text-xl font-bold text-white mt-1">{suitInsights.best_zone}</h4>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-500">MAX MODELED SUITABILITY SCORE</span>
                <div className="text-2xl font-bold text-ocean-cyan mt-1">{suitInsights.best_suitability}%</div>
              </div>
              <p className="text-[10px] text-slate-500 leading-relaxed leading-normal">
                *The recommendation highlights the sector displaying conditions most aligned with species evolutionary thresholds.
              </p>
            </div>

            {/* Zones Comparison Bar Chart / List */}
            <div className="lg:col-span-2 space-y-3.5">
              <h4 className="text-xs font-mono text-slate-400">ZONE SUITABILITY SPECTRUM:</h4>
              <div className="space-y-3">
                {suitInsights.zones.map((z: any, idx: number) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-slate-300 font-sans font-medium">{z.zone}</span>
                      <span className="text-white font-semibold">{z.suitability}% suitability</span>
                    </div>
                    <div className="w-full bg-ocean-medium h-2 rounded overflow-hidden">
                      <div 
                        className="bg-ocean-cyan h-full transition-all duration-500" 
                        style={{width: `${z.suitability}%`}}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
