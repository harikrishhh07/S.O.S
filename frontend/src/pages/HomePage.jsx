import { useState, useEffect, useCallback } from 'react'
import { reportsAPI, locationsAPI } from '../api/client'
import ReportCard from '../components/ReportCard'
import { ReportCardSkeleton, EmptyState } from '../components/UI'
import { Search, SlidersHorizontal, ChevronLeft, ChevronRight } from 'lucide-react'

const STATUSES = ['reported', 'assigned', 'in_progress', 'pending_confirmation', 'resolved', 'reopened']
const CATEGORIES = ['electrical', 'civil', 'security', 'other']
const SORTS = [
  { value: 'priority', label: '🔥 Priority' },
  { value: 'newest', label: '🕐 Newest' },
  { value: 'hype', label: '📣 Hype' },
]

export default function HomePage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({ status: '', category: '', building: '', sort: 'priority' })
  const [locations, setLocations] = useState([])
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    locationsAPI.list().then(r => setLocations(r.data)).catch(() => {})
  }, [])

  const fetchReports = useCallback(() => {
    setLoading(true)
    const params = { page, page_size: 15, sort: filters.sort }
    if (filters.status) params.status = filters.status
    if (filters.category) params.category = filters.category
    if (filters.building) params.building = filters.building

    reportsAPI.list(params)
      .then(r => {
        setReports(r.data.items)
        setTotal(r.data.total)
        setPages(r.data.pages)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [page, filters])

  useEffect(() => { fetchReports() }, [fetchReports])

  const setFilter = (k) => (v) => {
    setFilters(f => ({ ...f, [k]: v }))
    setPage(1)
  }

  const buildings = [...new Set(locations.map(l => l.building))]

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Campus Hazard Feed</h1>
          <p className="text-sm text-gray-500">{total} report{total !== 1 ? 's' : ''} found</p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border transition-colors ${
            showFilters ? 'bg-red-50 border-red-200 text-red-600' : 'border-gray-200 text-gray-600 hover:border-gray-300'
          }`}
        >
          <SlidersHorizontal size={14} />
          Filters
        </button>
      </div>

      {/* Sort pills */}
      <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
        {SORTS.map(s => (
          <button
            key={s.value}
            onClick={() => setFilter('sort')(s.value)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
              filters.sort === s.value
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card mb-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select className="input text-xs" value={filters.status} onChange={e => setFilter('status')(e.target.value)}>
              <option value="">All statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
            <select className="input text-xs" value={filters.category} onChange={e => setFilter('category')(e.target.value)}>
              <option value="">All categories</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Building</label>
            <select className="input text-xs" value={filters.building} onChange={e => setFilter('building')(e.target.value)}>
              <option value="">All buildings</option>
              {buildings.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>
          <div className="col-span-2 sm:col-span-3">
            <button className="text-xs text-red-600 hover:underline" onClick={() => {
              setFilters({ status: '', category: '', building: '', sort: 'priority' }); setPage(1)
            }}>
              Clear all filters
            </button>
          </div>
        </div>
      )}

      {/* Report list */}
      <div className="space-y-3">
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <ReportCardSkeleton key={i} />)
          : reports.length === 0
            ? <EmptyState icon="🏫" title="No reports found" description="Try changing your filters or be the first to report a hazard." />
            : reports.map(r => <ReportCard key={r.id} report={r} onHypeChange={fetchReports} />)
        }
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="p-2 rounded-lg border disabled:opacity-40 hover:bg-gray-50"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-gray-600">Page {page} of {pages}</span>
          <button
            disabled={page === pages}
            onClick={() => setPage(p => p + 1)}
            className="p-2 rounded-lg border disabled:opacity-40 hover:bg-gray-50"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
