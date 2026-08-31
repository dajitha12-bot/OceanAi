import { useState, useEffect } from 'react'
import { AlertCircle, ShieldAlert, CheckCircle2, Locate, RefreshCw, Layers } from 'lucide-react'
import { API_BASE } from '../api'

interface InsightsProps {
  onLocate: (lat: number, lng: number) => void
}

export default function Insights({ onLocate }: InsightsProps) {
  const [insights, setInsights] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [recalculating, setRecalculating] = useState<boolean>(false)

  const fetchInsightsData = () => {
    setLoading(true)
    fetch(`${API_BASE}/api/insights/`)
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
    fetch(`${API_BASE}/api/biodiversity/indicators/recalculate/`, { method: 'POST' })
      .then(() => fetch(`${API_BASE}/api/anomalies/scan/`, { method: 'POST' }))
      .then(() => fetch(`${API_BASE}/api/predictions/generate-forecasts/`, { method: 'POST' }))
      .then(() => {
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
      <div className="border-b border-ocean-waterBorder pb-4 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-ocean-textDark tracking-wide">AI INSIGHTS & ECOSYSTEM ALERTS</h2>
          <p className="text-xs text-ocean-textMuted font-mono">ENVIRONMENTAL RISK WATCH & SUSTAINABLE HARVEST RECOMMENDATIONS</p>
        </div>
        <button
          onClick={triggerRecalculate}
          disabled={recalculating}
          className="bg-white hover:bg-sky-50 disabled:bg-slate-100 border border-ocean-waterBorder transition text-ocean-cyan px-4 py-2 rounded-lg font-mono text-xs font-bold flex items-center space-x-2 shadow-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${recalculating ? 'animate-spin' : ''}`} />
          <span>{recalculating ? 'RECALCULATING TENSORS...' : 'RE-RUN AI MODELS'}</span>
        </button>
      </div>

      {/* Grid of Anomalies & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Environmental Anomalies Panel */}
        <div className="bg-white border border-ocean-waterBorder rounded-xl p-6 space-y-4 lg:col-span-1 shadow-sm">
          <div className="border-b border-slate-100 pb-2 mb-2 flex items-center justify-between">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-700 uppercase">ACTIVE ANOMALY DETECTIONS</h3>
            <span className="text-[10px] font-mono text-slate-500 bg-sky-50 px-2 py-0.5 rounded border border-sky-100">Isolation Forest</span>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[420px] pr-1.5">
            {activeAnoms.length > 0 ? (
              activeAnoms.map((an: any) => (
                <div 
                  key={an.id} 
                  className={`border p-4 rounded-xl flex flex-col justify-between space-y-2.5 ${
                    an.severity === 'High' 
                      ? 'bg-rose-50 border-rose-200' 
                      : 'bg-amber-50 border-amber-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full ${an.severity === 'High' ? 'bg-rose-600 text-white' : 'bg-amber-500 text-white'}`}>
                      {an.severity} SEVERITY
                    </span>
                    <button
                      onClick={() => onLocate(an.latitude, an.longitude)}
                      className="text-ocean-cyan hover:underline text-[10px] font-mono flex items-center space-x-1 font-bold"
                    >
                      <Locate className="h-3 w-3" />
                      <span>Locate</span>
                    </button>
                  </div>
                  <div className="text-xs text-slate-800">
                    Anomaly detected in <b>{an.parameter.toUpperCase()}</b>: <span className="font-mono font-bold text-rose-700">{an.observed_value}</span> vs baseline <span className="text-slate-500 font-mono">{an.expected_value}</span>
                  </div>
                  <div className="text-[9px] font-mono text-slate-500 flex justify-between pt-1">
                    <span>COORD: ({an.latitude.toFixed(2)}, {an.longitude.toFixed(2)})</span>
                    <span>{new Date(an.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400 space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                <p className="text-[11px] font-mono">No active anomalies detected in scanning history.</p>
              </div>
            )}
          </div>
        </div>

        {/* Biodiversity Risks & Recommendations */}
        <div className="bg-white border border-ocean-waterBorder rounded-xl p-6 space-y-4 lg:col-span-2 shadow-sm">
          <div className="border-b border-slate-100 pb-2 mb-2">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-700 uppercase">BIODIVERSITY RISKS BY STATION</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {riskZones.map((z: any, idx: number) => {
              const lat = 13.0 + idx * 0.1
              const lng = 80.3 + idx * 0.3
              
              return (
                <div key={idx} className="bg-sky-50/60 border border-sky-100 p-5 rounded-xl flex flex-col justify-between space-y-3 shadow-2xs">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-bold text-ocean-textDark">{z.region_name}</h4>
                      <p className="text-[9px] font-mono text-slate-500 uppercase">{z.source}</p>
                    </div>
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${z.risk_level === 'High' ? 'bg-rose-100 text-rose-700 border border-rose-200' : z.risk_level === 'Moderate' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 'bg-emerald-100 text-emerald-700 border border-emerald-200'}`}>
                      {z.risk_level} RISK ({z.risk_score}%)
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-600">
                    <div>
                      <span className="text-[9px] block text-slate-400">SPECIES COUNT</span>
                      <span className="text-slate-800 font-bold">{z.species_count} species</span>
                    </div>
                    <div>
                      <span className="text-[9px] block text-slate-400">OCCURRENCES</span>
                      <span className="text-slate-800 font-bold">{z.occurrence_count} records</span>
                    </div>
                    <div>
                      <span className="text-[9px] block text-slate-400">SHANNON INDEX</span>
                      <span className="text-slate-800 font-bold">{z.shannon_index ? z.shannon_index.toFixed(2) : '1.14'}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-sky-100 flex justify-between items-center">
                    <span className="text-[10px] text-slate-500 font-mono">COORD: ({lat.toFixed(2)}°N, {lng.toFixed(2)}°E)</span>
                    <button
                      onClick={() => onLocate(lat, lng)}
                      className="text-ocean-cyan hover:text-sky-700 transition flex items-center space-x-1 text-[10px] font-mono font-bold"
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
          <div className="bg-sky-50/70 border border-sky-100 p-5 rounded-xl space-y-3 mt-4 select-text">
            <h4 className="text-xs font-mono font-bold tracking-wider text-slate-700 uppercase flex items-center space-x-1.5">
              <Layers className="h-4 w-4 text-ocean-cyan" />
              <span>AI DECISION-SUPPORT REPORT</span>
            </h4>
            <div className="space-y-2 text-xs leading-relaxed text-slate-700">
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
        <div className="bg-white border border-ocean-waterBorder rounded-xl p-6 space-y-4 shadow-sm">
          <div className="border-b border-slate-100 pb-2 mb-2 flex justify-between items-center">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-700 uppercase">SPECIES SUITABILITY PROFILE: {suitInsights.species}</h3>
            <span className="text-[10px] font-mono text-slate-500">Model: {suitInsights.model_method}</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Metrics */}
            <div className="bg-sky-50/60 border border-sky-100 p-5 rounded-xl flex flex-col justify-between space-y-4 lg:col-span-1">
              <div>
                <span className="text-[10px] font-mono text-slate-500 font-bold">RECOMMENDED HARVEST SECTOR</span>
                <h4 className="text-2xl font-extrabold text-ocean-textDark mt-1">{suitInsights.best_zone}</h4>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-500 font-bold">MAX MODELED SUITABILITY SCORE</span>
                <div className="text-3xl font-extrabold text-ocean-cyan mt-1">{suitInsights.best_suitability}%</div>
              </div>
              <p className="text-[10px] text-slate-500 leading-relaxed">
                *The recommendation highlights the sector displaying environmental conditions most aligned with species evolutionary thresholds.
              </p>
            </div>

            {/* Zones Comparison Bar Chart / List */}
            <div className="lg:col-span-2 space-y-3.5">
              <h4 className="text-xs font-mono font-bold text-slate-600">ZONE SUITABILITY SPECTRUM:</h4>
              <div className="space-y-3">
                {suitInsights.zones.map((z: any, idx: number) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-slate-700 font-sans font-semibold">{z.zone}</span>
                      <span className="text-ocean-cyan font-bold">{z.suitability}% suitability</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden border border-slate-200">
                      <div 
                        className="bg-ocean-cyan h-full rounded-full transition-all duration-500" 
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
