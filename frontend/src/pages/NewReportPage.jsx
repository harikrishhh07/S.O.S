import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { reportsAPI, locationsAPI, locationInferenceAPI } from '../api/client'
import { Spinner, SeverityBadge } from '../components/UI'
import toast from 'react-hot-toast'
import { Camera, ImagePlus, MapPin, CheckCircle, AlertTriangle, Flame, ChevronDown } from 'lucide-react'
import apiClient from '../api/client'

const STEPS = ['Photo & Description', 'Location & Category', 'Review & Submit']

export default function NewReportPage() {
  const navigate = useNavigate()
  const fileRef = useRef(null)
  const cameraRef = useRef(null)
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [locations, setLocations] = useState([])
  const [taxonomy, setTaxonomy] = useState([])   // [{id, label, services:[{id,label}]}]
  const [form, setForm] = useState({
    title: '', description: '', image: null, imagePreview: null,
    building: '', zone: '', lat: '', lng: '', is_anonymous: false,
    department_id: '', service_id: '',
  })
  const [aiResult, setAiResult] = useState(null)
  const [dupCheck, setDupCheck] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    locationsAPI.list().then(r => setLocations(r.data)).catch(() => {})
    // Fetch taxonomy from backend
    apiClient.get('/taxonomy').then(r => setTaxonomy(r.data.departments || [])).catch(() => {})
  }, [])

  const set = (k) => (e) => setForm(f => ({
    ...f,
    [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
    // Reset sub-service when department changes
    ...(k === 'department_id' ? { service_id: '' } : {}),
  }))

  const handleImage = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setForm(f => ({ ...f, image: file, imagePreview: URL.createObjectURL(file) }))
    // Feature 2: auto-infer building from the uploaded photo
    inferLocationFromImage(file)
  }

  // Feature 2: Location inference — auto-detect building from uploaded image
  const [inferringLocation, setInferringLocation] = useState(false)
  const [inferredLocation, setInferredLocation] = useState(null)

  const inferLocationFromImage = async (file) => {
    if (!file) return
    setInferringLocation(true)
    try {
      const res = await locationInferenceAPI.inferFromImage(file)
      const data = res.data
      if (data.building && data.confidence >= 0.6) {
        setInferredLocation(data)
        setForm(f => ({
          ...f,
          building: data.building,
          zone: data.zone || f.zone,
        }))
        toast.success(`📍 AI identified: ${data.building}`)
      } else if (data.building) {
        setInferredLocation(data)
        toast(`📍 Possible match: ${data.building} (low confidence — please verify)`, { icon: '🤔' })
      }
    } catch (e) {
      // silent — location inference is optional enhancement
    } finally {
      setInferringLocation(false)
    }
  }

  const handleGPS = () => {
    navigator.geolocation?.getCurrentPosition(
      pos => setForm(f => ({ ...f, lat: pos.coords.latitude.toFixed(6), lng: pos.coords.longitude.toFixed(6) })),
      () => toast.error('GPS unavailable')
    )
  }

  const buildings = [...new Set(locations.map(l => l.building))]
  const zonesForBuilding = locations.filter(l => l.building === form.building).map(l => l.zone).filter(Boolean)
  const selectedDept = taxonomy.find(d => d.id === form.department_id)

  const nextStep = () => {
    if (step === 0 && !form.description && !form.image) {
      toast.error('Please add a photo or description')
      return
    }
    if (step === 1 && !form.building) {
      toast.error('Please select a building')
      return
    }
    if (step === 1) {
      analyzePreview()
    }
    setStep(s => s + 1)
  }

  const analyzePreview = async () => {
    setAnalyzing(true)
    try {
      const fd = new FormData()
      fd.append('title', form.title || form.description?.slice(0, 50) || 'Hazard report')
      fd.append('description', form.description || '')
      fd.append('building', form.building)
      if (form.zone) fd.append('zone', form.zone)
      if (form.lat) fd.append('lat', form.lat)
      if (form.lng) fd.append('lng', form.lng)
      fd.append('is_anonymous', form.is_anonymous)
      if (form.image) fd.append('image', form.image)
      // Pass user-selected category if provided (overrides AI)
      if (form.department_id) fd.append('category', form.department_id)
      if (form.service_id) fd.append('service_id', form.service_id)

      const r = await reportsAPI.create(fd)
      setAiResult(r.data.ai_result)
      setDupCheck(r.data.duplicate_check)
      setForm(f => ({ ...f, _createdId: r.data.report.id }))
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (form._createdId) {
      toast.success('Report submitted successfully!')
      navigate(`/reports/${form._createdId}`)
    }
  }

  // Department label for display
  const deptLabel = selectedDept?.label || null
  const svcLabel = selectedDept?.services?.find(s => s.id === form.service_id)?.label || null

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Report a Hazard</h1>

      {/* Stepper */}
      <div className="flex items-center mb-8">
        {STEPS.map((s, i) => (
          <div key={i} className="flex items-center flex-1">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-all shrink-0 ${
              i < step ? 'bg-green-500 text-white' : i === step ? 'bg-red-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              {i < step ? <CheckCircle size={16} /> : i + 1}
            </div>
            <span className={`ml-2 text-xs font-medium hidden sm:block ${i === step ? 'text-red-600' : 'text-gray-400'}`}>
              {s}
            </span>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-px mx-3 ${i < step ? 'bg-green-500' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Photo & Description */}
        {step === 0 && (
          <div className="space-y-4">
            <div
              className={`relative border-2 border-dashed rounded-xl transition-all h-40 flex items-center justify-center ${
                form.imagePreview ? 'border-red-300' : 'border-gray-300 hover:border-red-400'
              }`}
            >
              {form.imagePreview ? (
                <img src={form.imagePreview} alt="preview" className="w-full h-full object-cover rounded-xl" />
              ) : (
                <div className="text-center text-gray-400">
                  <Camera size={32} className="mx-auto mb-2" />
                  <p className="text-sm font-medium">Add a photo of the hazard</p>
                  <p className="text-xs mt-0.5">JPEG, PNG, WebP</p>
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => cameraRef.current?.click()}
                className="btn-primary flex items-center justify-center gap-2 text-sm"
              >
                <Camera size={16} /> Take photo
              </button>
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="btn-secondary flex items-center justify-center gap-2 text-sm"
              >
                <ImagePlus size={16} /> Choose image
              </button>
            </div>
            <input ref={cameraRef} type="file" accept="image/*" capture="environment"
              className="hidden" onChange={handleImage} />
            <input ref={fileRef} type="file" accept="image/*"
              className="hidden" onChange={handleImage} />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
              <textarea
                className="input resize-none" rows={4}
                value={form.description} onChange={set('description')}
                placeholder="Describe the hazard clearly — what you saw, where exactly, how dangerous it looks..."
              />
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="anon" checked={form.is_anonymous} onChange={set('is_anonymous')} className="rounded" />
              <label htmlFor="anon" className="text-sm text-gray-600">Report anonymously</label>
            </div>
          </div>
        )}

        {/* Step 2: Location & Category */}
        {step === 1 && (
          <div className="space-y-4">
            {/* Building / zone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Building *
                {inferringLocation && (
                  <span className="ml-2 text-xs text-blue-500 animate-pulse">🔍 AI identifying location…</span>
                )}
              </label>
              <select className="input" value={form.building} onChange={set('building')} required>
                <option value="">Select building</option>
                {buildings.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
              {inferredLocation && inferredLocation.building && !inferringLocation && (
                <div className="mt-1.5 flex items-start gap-1.5 text-xs bg-blue-50 border border-blue-100 rounded-lg px-2 py-1.5">
                  <span>🤖</span>
                  <div>
                    <span className="font-medium text-blue-700">AI detected:</span>
                    <span className="text-blue-600"> {inferredLocation.building}</span>
                    <span className="text-gray-400"> ({Math.round(inferredLocation.confidence * 100)}% confident)</span>
                    {inferredLocation.landmark_clues && (
                      <p className="text-gray-400 mt-0.5 italic">"{inferredLocation.landmark_clues}"</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {zonesForBuilding.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Zone / Area</label>
                <select className="input" value={form.zone} onChange={set('zone')}>
                  <option value="">Select zone (optional)</option>
                  {zonesForBuilding.map(z => <option key={z} value={z}>{z}</option>)}
                </select>
              </div>
            )}

            <div>
              <button type="button" onClick={handleGPS} className="btn-secondary text-sm flex items-center gap-2">
                <MapPin size={14} />
                Use my GPS location
              </button>
              {form.lat && <p className="text-xs text-green-600 mt-1">📍 GPS: {form.lat}, {form.lng}</p>}
            </div>

            {/* Taxonomy — department + sub-service */}
            <div className="border-t border-gray-100 pt-4">
              <p className="text-sm font-semibold text-gray-800 mb-3 flex items-center gap-1">
                <ChevronDown size={14} className="text-red-500" />
                Service Category
                <span className="text-xs font-normal text-gray-400 ml-1">(optional — AI will auto-detect if skipped)</span>
              </p>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Department</label>
                <select className="input text-sm" value={form.department_id} onChange={set('department_id')}>
                  <option value="">— Let AI decide —</option>
                  {taxonomy.map(d => (
                    <option key={d.id} value={d.id}>{d.label}</option>
                  ))}
                </select>
              </div>

              {selectedDept && (
                <div className="mt-3">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Sub-service</label>
                  <select className="input text-sm" value={form.service_id} onChange={set('service_id')}>
                    <option value="">— Any service under {selectedDept.label} —</option>
                    {selectedDept.services.map(s => (
                      <option key={s.id} value={s.id}>{s.label}</option>
                    ))}
                  </select>
                </div>
              )}

              {deptLabel && (
                <p className="mt-2 text-xs text-blue-700 bg-blue-50 rounded px-2 py-1">
                  📂 {deptLabel}{svcLabel ? ` › ${svcLabel}` : ''}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Review */}
        {step === 2 && (
          <div className="space-y-4">
            {analyzing ? (
              <div className="text-center py-8">
                <Spinner size="lg" />
                <p className="text-sm text-gray-500 mt-3">AI is analyzing your report...</p>
              </div>
            ) : aiResult ? (
              <>
                {aiResult.hazard_type !== 'not_a_hazard' ? (
                  <div className="card border border-red-100 bg-red-50">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={16} className="text-red-600" />
                      <span className="font-semibold text-sm text-red-800">AI Analysis</span>
                      <span className="ml-auto text-xs text-gray-500">{Math.round((aiResult.confidence || 0) * 100)}% confident</span>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      <SeverityBadge severity={aiResult.severity} />
                      <span className="badge bg-yellow-100 text-yellow-800">{aiResult.hazard_type?.replace(/_/g, ' ')}</span>
                      {aiResult.is_safety_critical && (
                        <span className="badge bg-red-600 text-white animate-pulse">🚨 CRITICAL</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-700">{aiResult.reasoning}</p>
                  </div>
                ) : (
                  <div className="card border border-amber-200 bg-amber-50">
                    <p className="text-amber-800 text-sm font-medium">⚠️ This doesn't appear to be a campus hazard. Please upload a relevant photo or add more details.</p>
                  </div>
                )}

                {/* User-selected category display */}
                {deptLabel && (
                  <div className="card border border-blue-100 bg-blue-50">
                    <p className="text-blue-800 text-xs font-medium">
                      📂 You selected: <strong>{deptLabel}</strong>{svcLabel ? ` › ${svcLabel}` : ''}
                    </p>
                  </div>
                )}

                {dupCheck?.status === 'POSSIBLE_DUPLICATE' && dupCheck.suggestions?.length > 0 && (
                  <div className="card border border-amber-200 bg-amber-50">
                    <p className="text-amber-800 text-sm font-semibold mb-2">Similar issues already reported:</p>
                    {dupCheck.suggestions.map(s => (
                      <div key={s.id} className="flex items-center justify-between py-1.5 border-t border-amber-100">
                        <span className="text-xs text-gray-700">{s.title} — {s.building}</span>
                        <button type="button" onClick={() => navigate(`/reports/${s.id}`)}
                          className="flex items-center gap-1 text-xs text-amber-700 font-semibold hover:underline">
                          <Flame size={11} /> Hype instead
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {dupCheck?.status === 'DUPLICATE' && (
                  <div className="card border border-green-200 bg-green-50">
                    <p className="text-green-800 text-sm">✅ {dupCheck.message}</p>
                  </div>
                )}

                {dupCheck?.status === 'RECURRING' && (
                  <div className="card border border-purple-200 bg-purple-50">
                    <p className="text-purple-800 text-sm">🔁 {dupCheck.message}</p>
                  </div>
                )}

                <div className="pt-2">
                  <p className="text-sm text-gray-600">
                    Reporting at <strong>{form.building}</strong>{form.zone ? ` · ${form.zone}` : ''}
                    {form.is_anonymous ? ' (anonymously)' : ''}
                  </p>
                </div>
              </>
            ) : null}
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-6">
          {step > 0 && (
            <button type="button" onClick={() => setStep(s => s - 1)}
              className="btn-secondary flex-1" disabled={analyzing}>
              Back
            </button>
          )}
          {step < 2 ? (
            <button type="button" onClick={nextStep} className="btn-primary flex-1">
              {step === 1 ? 'Analyze & Review' : 'Next'}
            </button>
          ) : (
            <button type="submit" className="btn-primary flex-1"
              disabled={analyzing || !form._createdId}>
              {analyzing ? <Spinner size="sm" /> : form._createdId ? 'View Report →' : 'Submitting...'}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
