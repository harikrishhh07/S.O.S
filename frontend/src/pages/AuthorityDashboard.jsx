import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { reportsAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { SeverityBadge, StatusBadge, CriticalBanner, Spinner, EmptyState } from '../components/UI'
import toast from 'react-hot-toast'
import { List, LayoutGrid, Upload, ChevronRight } from 'lucide-react'

const KANBAN_COLS = [
  { status: 'assigned', label: 'Assigned', color: 'border-purple-400' },
  { status: 'in_progress', label: 'In Progress', color: 'border-yellow-400' },
  { status: 'pending_confirmation', label: 'Pending Confirm', color: 'border-orange-400' },
]

export default function AuthorityDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('kanban')
  const [selected, setSelected] = useState(null)
  const [statusNote, setStatusNote] = useState('')
  const [newStatus, setNewStatus] = useState('')
  const [afterImage, setAfterImage] = useState(null)
  const [resolveNote, setResolveNote] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const fetchReports = () => {
    setLoading(true)
    reportsAPI.list({ department: user?.department, page_size: 100, sort: 'priority' })
      .then(r => setReports(r.data.items))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchReports() }, [])

  const handleStatusUpdate = async () => {
    if (!selected || !newStatus) return
    setActionLoading(true)
    try {
      await reportsAPI.updateStatus(selected.id, { status: newStatus, note: statusNote })
      toast.success('Status updated')
      setSelected(null)
      setStatusNote('')
      setNewStatus('')
      fetchReports()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update status')
    } finally {
      setActionLoading(false)
    }
  }

  const handleResolve = async () => {
    if (!selected || !afterImage || !resolveNote) {
      toast.error('After photo and note are required')
      return
    }
    setActionLoading(true)
    try {
      const fd = new FormData()
      fd.append('note', resolveNote)
      fd.append('after_image', afterImage)
      const r = await reportsAPI.resolve(selected.id, fd)
      toast.success('Resolution submitted! Awaiting reporter confirmation.')
      if (r.data.flagged_for_review) {
        toast('⚠️ Flagged for admin review — AI match confidence is low', { icon: '🔍' })
      }
      setSelected(null)
      setAfterImage(null)
      setResolveNote('')
      fetchReports()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit resolution')
    } finally {
      setActionLoading(false)
    }
  }

  const criticalReports = reports.filter(r => r.is_safety_critical && r.status !== 'resolved')
  const byStatus = (status) => reports.filter(r => r.status === status)

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Authority Queue</h1>
          <p className="text-sm text-gray-500">{user?.department} Department · {reports.length} reports</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setView('kanban')} className={`p-2 rounded-lg border ${view === 'kanban' ? 'bg-red-50 border-red-200 text-red-600' : 'text-gray-500'}`}>
            <LayoutGrid size={16} />
          </button>
          <button onClick={() => setView('list')} className={`p-2 rounded-lg border ${view === 'list' ? 'bg-red-50 border-red-200 text-red-600' : 'text-gray-500'}`}>
            <List size={16} />
          </button>
        </div>
      </div>

      {/* Safety critical pinned */}
      {criticalReports.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-xs font-bold text-red-700 mb-2">🚨 SAFETY CRITICAL — Immediate Action Required</p>
          <div className="space-y-2">
            {criticalReports.map(r => (
              <button key={r.id} onClick={() => { setSelected(r); setNewStatus('') }}
                className="w-full text-left flex items-center justify-between p-2 bg-white rounded-lg border border-red-200 hover:border-red-400 transition-colors">
                <div>
                  <span className="text-sm font-semibold text-red-800">{r.title}</span>
                  <span className="text-xs text-gray-500 ml-2">{r.building}</span>
                </div>
                <ChevronRight size={14} className="text-red-400" />
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-4">
        {/* Main view */}
        <div className="flex-1">
          {view === 'kanban' ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {KANBAN_COLS.map(col => (
                <div key={col.status} className={`bg-gray-50 rounded-xl p-3 border-t-4 ${col.color}`}>
                  <h3 className="font-semibold text-sm text-gray-700 mb-3">
                    {col.label} <span className="text-gray-400">({byStatus(col.status).length})</span>
                  </h3>
                  <div className="space-y-2">
                    {byStatus(col.status).length === 0
                      ? <p className="text-xs text-gray-400 text-center py-4">Empty</p>
                      : byStatus(col.status).map(r => (
                        <button
                          key={r.id}
                          onClick={() => { setSelected(r); setNewStatus('') }}
                          className={`w-full text-left p-3 bg-white rounded-lg border transition-all ${selected?.id === r.id ? 'border-red-400 shadow-sm' : 'border-gray-200 hover:border-gray-300'}`}
                        >
                          <div className="flex items-start gap-2">
                            {r.is_safety_critical && <span className="text-red-500 text-xs">🚨</span>}
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-semibold text-gray-900 truncate">{r.title}</p>
                              <p className="text-xs text-gray-500 mt-0.5">{r.building}</p>
                              <div className="flex gap-1 mt-1">
                                <SeverityBadge severity={r.severity} />
                              </div>
                            </div>
                          </div>
                        </button>
                      ))
                    }
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {reports.length === 0
                ? <EmptyState icon="✅" title="No reports assigned" description="All clear in your department." />
                : reports.map(r => (
                  <button
                    key={r.id}
                    onClick={() => { setSelected(r); setNewStatus('') }}
                    className={`w-full text-left p-3 bg-white rounded-xl border transition-all ${selected?.id === r.id ? 'border-red-400' : 'border-gray-200 hover:border-gray-300'}`}
                  >
                    <div className="flex items-center gap-3">
                      {r.image_path && <img src={`http://localhost:8000/${r.image_path}`} alt="" className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {r.is_safety_critical && <span className="text-red-500">🚨</span>}
                          <p className="font-semibold text-sm text-gray-900 truncate">{r.title}</p>
                        </div>
                        <p className="text-xs text-gray-500">{r.building}{r.zone ? ` · ${r.zone}` : ''}</p>
                        <div className="flex gap-1.5 mt-1">
                          <SeverityBadge severity={r.severity} />
                          <StatusBadge status={r.status} />
                        </div>
                      </div>
                      <span className="text-xs font-bold text-gray-400">{Math.round(r.priority_score)}</span>
                    </div>
                  </button>
                ))
              }
            </div>
          )}
        </div>

        {/* Action panel */}
        {selected && (
          <div className="w-72 flex-shrink-0">
            <div className="card sticky top-20 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-gray-900 truncate pr-2">{selected.title}</h3>
                <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
              </div>

              <button onClick={() => navigate(`/reports/${selected.id}`)} className="text-xs text-red-600 hover:underline">
                View full report →
              </button>

              {/* Status update */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Change Status</label>
                <select className="input text-xs" value={newStatus} onChange={e => setNewStatus(e.target.value)}>
                  <option value="">Select new status</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="pending_confirmation">Pending Confirmation</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Note</label>
                <textarea className="input text-xs resize-none" rows={2} value={statusNote} onChange={e => setStatusNote(e.target.value)} placeholder="Add a note..." />
              </div>
              <button onClick={handleStatusUpdate} disabled={!newStatus || actionLoading} className="btn-primary w-full text-xs py-1.5">
                {actionLoading ? <Spinner size="sm" /> : 'Update Status'}
              </button>

              {/* Resolve with after photo */}
              <div className="border-t pt-3">
                <p className="text-xs font-semibold text-gray-700 mb-2">Mark as Resolved</p>
                <label className="block text-xs font-medium text-gray-600 mb-1">After photo *</label>
                <input type="file" accept="image/*" onChange={e => setAfterImage(e.target.files[0])} className="text-xs w-full" />
                {afterImage && <p className="text-xs text-green-600 mt-0.5">✓ {afterImage.name}</p>}
                <textarea
                  className="input text-xs resize-none mt-2"
                  rows={2}
                  value={resolveNote}
                  onChange={e => setResolveNote(e.target.value)}
                  placeholder="Describe what was fixed..."
                />
                <button onClick={handleResolve} disabled={actionLoading} className="mt-2 w-full flex items-center justify-center gap-1.5 bg-green-600 hover:bg-green-700 text-white text-xs py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-50">
                  <Upload size={12} />
                  Submit Resolution
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
