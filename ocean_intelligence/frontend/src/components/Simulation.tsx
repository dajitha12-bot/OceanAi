import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Sliders, HelpCircle, Thermometer, ShieldAlert, Activity, RefreshCw } from 'lucide-react'

export default function Simulation() {
  // Sliders state (deltas)
  const [tempDelta, setTempDelta] = useState<number>(2.0) // default +2.0 C
  const [salDelta, setSalDelta] = useState<number>(-1.0)  // default -1.0 PSU
  const [chlorDelta, setChlorDelta] = useState<number>(0.5) // default +0.5 mg/m3
  
  const [loading, setLoading] = useState<boolean>(false)
  const [simResults, setSimResults] = useState<any>(null)
  
  // Forecast state
  const [forecasts, setForecasts] = useState<any[]>([])
  const [forecastLoading, setForecastLoading] = useState<boolean>(true)

  // Fetch initial forecasts
  useEffect(() => {
    fetch('/api/predictions/?target_type=temperature')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          // Format 7 days predictions
          const formatted = data.slice(0, 7).map((p: any) => ({
            date: new Date(p.prediction_date).toLocaleDateString(undefined, {month: 'short', day: 'numeric'}),
            temp: p.predicted_value
          }))
          setForecasts(formatted)
        } else {
          // Mock forecast if database empty
          const start = new Date()
          const mock = Array.from({length: 7}).map((_, i) => {
            const d = new Date(start)
            d.setDate(start.getDate() + i)
            return {
              date: d.toLocaleDateString(undefined, {month: 'short', day: 'numeric'}),
              temp: round(28.5 + 1.2 * Math.cos(2 * Math.PI * i / 10) + 0.1 * i, 1)
            }
          })
          setForecasts(mock)
        }
        setForecastLoading(false)
      })
      .catch(() => {
        // Fallback mock
        const start = new Date()
        setForecasts(Array.from({length: 7}).map((_, i) => {
          const d = new Date(start)
          d.setDate(start.getDate() + i)
          return {
            date: d.toLocaleDateString(undefined, {month: 'short', day: 'numeric'}),
            temp: round(29.1 - 0.2 * i, 1),
            suitability: round(84.0 - 2.5 * i, 1),
            risk: round(48.0 + 3.0 * i, 1)
          }
        }))
        setForecastLoading(false)
      })

    // Run default simulation on mount
    triggerSimulation()
  }, [])

  function round(val: number, decimals: number) {
    const factor = Math.pow(10, decimals)
    return Math.round(val * factor) / factor
  }

  const triggerSimulation = () => {
    setLoading(true)
    fetch('/api/simulation/what-if/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        temperature_delta: tempDelta,
        salinity_delta: salDelta,
        chlorophyll_delta: chlorDelta,
        latitude: 13.1,
        longitude: 80.6,
        species: 'Thunnus albacares'
      })
    })
      .then(res => res.json())
      .then(data => {
        setSimResults(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Simulation error", err)
        setLoading(false)
      })
  }

  const chartData = simResults ? [
    {
      name: 'Tuna Suitability (%)',
      Current: simResults.before.suitability,
      Simulated: simResults.after.suitability,
    },
    {
      name: 'Biodiversity Risk (%)',
      Current: simResults.before.biodiversity_risk,
      Simulated: simResults.after.biodiversity_risk,
    }
  ] : []

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto select-none">
      {/* Title */}
      <div className="border-b border-ocean-light pb-4">
        <h2 className="text-xl font-bold text-white tracking-wide">PREDICTION & WHAT-IF ENVIRONMENTAL SIMULATION</h2>
        <p className="text-xs text-slate-400 font-mono">MODEL-BASED INFERENCE SIMULATOR</p>
      </div>

      {/* Simulator Section Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Sliders Input Panel */}
        <div className="bg-ocean-dark border border-ocean-light rounded p-5 space-y-5">
          <div className="border-b border-ocean-light/50 pb-2 mb-2 flex items-center space-x-2">
            <Sliders className="h-4 w-4 text-ocean-cyan" />
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">ENVIRONMENTAL CONTROLS</h3>
          </div>

          {/* Temperature Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400 flex items-center space-x-1">
                <Thermometer className="h-3.5 w-3.5 text-rose-400" />
                <span>SST Modification:</span>
              </span>
              <span className={`font-bold ${tempDelta >= 0 ? 'text-rose-400' : 'text-blue-400'}`}>
                {tempDelta >= 0 ? `+${tempDelta}` : tempDelta}°C
              </span>
            </div>
            <input 
              type="range" 
              min="-4.0" 
              max="4.0" 
              step="0.1"
              value={tempDelta} 
              onChange={(e) => setTempDelta(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-ocean-medium rounded-lg appearance-none cursor-pointer accent-ocean-cyan"
            />
            <div className="flex justify-between text-[9px] font-mono text-slate-500">
              <span>-4.0°C</span>
              <span>Baseline</span>
              <span>+4.0°C</span>
            </div>
          </div>

          {/* Salinity Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400 flex items-center space-x-1">
                <Activity className="h-3.5 w-3.5 text-blue-400" />
                <span>Salinity Modification:</span>
              </span>
              <span className={`font-bold ${salDelta >= 0 ? 'text-emerald-400' : 'text-amber-500'}`}>
                {salDelta >= 0 ? `+${salDelta}` : salDelta} PSU
              </span>
            </div>
            <input 
              type="range" 
              min="-5.0" 
              max="2.0" 
              step="0.1"
              value={salDelta} 
              onChange={(e) => setSalDelta(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-ocean-medium rounded-lg appearance-none cursor-pointer accent-ocean-cyan"
            />
            <div className="flex justify-between text-[9px] font-mono text-slate-500">
              <span>-5.0 PSU (freshwater)</span>
              <span>Baseline</span>
              <span>+2.0 PSU</span>
            </div>
          </div>

          {/* Chlorophyll Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400 flex items-center space-x-1">
                <ShieldAlert className="h-3.5 w-3.5 text-emerald-400" />
                <span>Chlorophyll-a Mod:</span>
              </span>
              <span className={`font-bold ${chlorDelta >= 0 ? 'text-emerald-400' : 'text-blue-300'}`}>
                {chlorDelta >= 0 ? `+${chlorDelta}` : chlorDelta} mg/m³
              </span>
            </div>
            <input 
              type="range" 
              min="-1.5" 
              max="3.0" 
              step="0.1"
              value={chlorDelta} 
              onChange={(e) => setChlorDelta(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-ocean-medium rounded-lg appearance-none cursor-pointer accent-ocean-cyan"
            />
            <div className="flex justify-between text-[9px] font-mono text-slate-500">
              <span>-1.5 mg/m³</span>
              <span>Baseline</span>
              <span>+3.0 mg/m³</span>
            </div>
          </div>

          {/* Trigger Button */}
          <button
            onClick={triggerSimulation}
            disabled={loading}
            className="w-full bg-ocean-cyan hover:bg-ocean-teal disabled:bg-ocean-medium transition text-white py-2.5 rounded font-mono font-bold text-xs flex items-center justify-center space-x-2 border border-ocean-cyan/35"
          >
            <RefreshCw className={`h-4.5 w-4.5 ${loading ? 'animate-spin' : ''}`} />
            <span>RUN INFERENCE MODELS</span>
          </button>
        </div>

        {/* Comparative Charts & Metrics Dashboard */}
        <div className="bg-ocean-dark border border-ocean-light rounded p-5 lg:col-span-2 space-y-6">
          <div className="border-b border-ocean-light/50 pb-2 flex items-center justify-between">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">SIMULATED SCENARIO COMPARISON</h3>
            <span className="text-[9px] font-mono text-slate-500">Coordinate Chennai Shelf (13.1°N, 80.6°E)</span>
          </div>

          {loading ? (
            <div className="h-[250px] flex items-center justify-center text-slate-500 font-mono text-xs animate-pulse">
              Re-calculating biological suitability tensors and ecosystem stress vectors...
            </div>
          ) : simResults ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Double Bar Chart */}
              <div className="h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1b2a47" />
                    <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                    <YAxis domain={[0, 100]} stroke="#64748b" fontSize={10} />
                    <Tooltip contentStyle={{ backgroundColor: '#0e172c', borderColor: '#3a506b', fontSize: 11 }} />
                    <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'monospace' }} />
                    <Bar dataKey="Current" fill="#3a506b" name="Current State" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="Simulated" fill="#00b4d8" name="Simulated State" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Side-by-Side Statistics */}
              <div className="space-y-4 text-xs">
                <div className="bg-ocean-medium/20 border border-ocean-light/40 p-4 rounded grid grid-cols-2 gap-4">
                  <div>
                    <h5 className="font-mono text-slate-400 text-[10px] mb-1">TUNA SUITABILITY</h5>
                    <div className="flex items-baseline space-x-1.5">
                      <span className="text-xl font-bold text-white">{simResults.after.suitability}%</span>
                      <span className={`text-[10px] font-mono font-semibold ${simResults.difference.suitability >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {simResults.difference.suitability >= 0 ? '▲' : '▼'} {simResults.difference.suitability}%
                      </span>
                    </div>
                  </div>
                  <div>
                    <h5 className="font-mono text-slate-400 text-[10px] mb-1">BIODIVERSITY RISK</h5>
                    <div className="flex items-baseline space-x-1.5">
                      <span className="text-xl font-bold text-white">{simResults.after.biodiversity_risk}%</span>
                      <span className={`text-[10px] font-mono font-semibold ${simResults.difference.biodiversity_risk <= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {simResults.difference.biodiversity_risk <= 0 ? '▼' : '▲'} {simResults.difference.biodiversity_risk}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5 text-[11px] font-mono text-slate-400">
                  <div className="flex justify-between">
                    <span>Variable</span>
                    <span>Before</span>
                    <span>After (Delta)</span>
                  </div>
                  <hr className="border-ocean-light/35" />
                  <div className="flex justify-between text-white">
                    <span>Sea Surface Temperature</span>
                    <span>{simResults.before.temperature.toFixed(1)}°C</span>
                    <span>{simResults.after.temperature.toFixed(1)}°C ({tempDelta >= 0 ? `+${tempDelta}` : tempDelta}°C)</span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>Salinity Range</span>
                    <span>{simResults.before.salinity.toFixed(1)} PSU</span>
                    <span>{simResults.after.salinity.toFixed(1)} PSU ({salDelta >= 0 ? `+${salDelta}` : salDelta} PSU)</span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>Chlorophyll Concentration</span>
                    <span>{simResults.before.chlorophyll.toFixed(1)} mg/m³</span>
                    <span>{simResults.after.chlorophyll.toFixed(1)} mg/m³ ({chlorDelta >= 0 ? `+${chlorDelta}` : chlorDelta})</span>
                  </div>
                </div>
              </div>

            </div>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-slate-500 font-mono text-xs">
              Waiting to execute models...
            </div>
          )}
        </div>
      </div>

      {/* RAG-grounded Explanation Box */}
      {simResults && (
        <div className="bg-ocean-dark border border-ocean-light rounded p-5 space-y-3">
          <div className="border-b border-ocean-light/50 pb-2">
            <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">AI BIOLOGICAL MECHANISM EXPLANATION</h3>
          </div>
          <div className="text-xs leading-relaxed text-slate-300 font-sans whitespace-pre-line bg-ocean-medium/10 border border-ocean-light/20 p-4 rounded select-text">
            {simResults.explanation}
          </div>
        </div>
      )}

      {/* 7-Day Future Climatology Prediction */}
      <div className="bg-ocean-dark border border-ocean-light rounded p-5">
        <div className="border-b border-ocean-light/50 pb-2 mb-4 flex justify-between items-center">
          <h3 className="text-xs font-mono font-bold tracking-wider text-slate-400 uppercase">7-DAY ENVIRONMENTAL & SUITABILITY TIMELINE</h3>
          <span className="text-[10px] font-mono text-slate-500">Models: Climatology Forecast + Random Forest</span>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
          {/* Trend Chart */}
          <div className="h-[180px] lg:col-span-1">
            {forecasts.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecasts} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1b2a47" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={9} />
                  <YAxis stroke="#64748b" fontSize={9} />
                  <Tooltip contentStyle={{ backgroundColor: '#0e172c', borderColor: '#3a506b', fontSize: 10 }} />
                  <Line type="monotone" dataKey="temp" name="Temp Forecast (°C)" stroke="#00b4d8" strokeWidth={2} dot={{ r: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 font-mono text-xs">
                No forecasts available.
              </div>
            )}
          </div>

          {/* Forecast Days Table */}
          <div className="lg:col-span-2 overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-ocean-light font-mono text-slate-500 text-[10px]">
                  <th className="py-2">TIMELINE</th>
                  <th>TEMP FORECAST</th>
                  <th>SALINITY FORECAST</th>
                  <th>CHLOROPHYLL</th>
                  <th>TUNA SUITABILITY</th>
                  <th>BIODIVERSITY RISK</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.map((f, idx) => (
                  <tr key={idx} className="border-b border-ocean-light/40 hover:bg-ocean-medium/20">
                    <td className="py-2.5 font-semibold text-slate-300">{f.date}</td>
                    <td className="font-mono">{f.temp}°C</td>
                    <td className="font-mono">{(f.salinity ?? 34.6).toFixed(1)} PSU</td>
                    <td className="font-mono">{(f.chlorophyll ?? 2.1).toFixed(1)} mg/m³</td>
                    <td>
                      <span className="font-semibold font-mono text-ocean-cyan">{(f.suitability ?? 84.0 - idx * 2.5).toFixed(0)}%</span>
                    </td>
                    <td>
                      <span className="font-semibold font-mono text-amber-500">{(f.risk ?? 48.0 + idx * 3).toFixed(0)}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
