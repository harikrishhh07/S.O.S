import { useState, useEffect } from 'react'
import { analyticsAPI, reportsAPI } from '../api/client'
import { Spinner, EmptyState } from '../components/UI'
import toast from 'react-hot-toast'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, FunnelChart, Funnel, LabelList
} from 'recharts'

const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6']

const KPICard = ({ label, value, sub, color = 'text-gray-900' }) => (
  <div className="card text-center">
    <p className="text-xs text-gray-500 font-medium">{label}</p>
    <p className={`text-3xl font-bold mt-1 ${color}`}>{value ?? '—'}</p>
    {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
  </div>
)

export default function AdminDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [seedLoading, setSeedLoading] = useState(false)
  const [hyping, setHyping] = useState(false)
  const [allReports, setAllReports] = useState([])
  const [tab, setTab] = useState('overview')

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      analyticsAPI.summary(),
      reportsAPI.list({ page_size: 100, sort: 'priority' }),
    ])
      .then(([analytics, reports]) => {
        setData(analytics.data)
        setAllReports(reports.data.items)
      })
      .catch(() => toast.error('Failed to load analytics'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const seedDemo = async () => {
    setSeedLoading(true)
    try {
      const r = await fetch('http://localhost:8000/admin/demo-seed', { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('sos_token')}` } })
      if (r.ok) { toast.success('Demo data refreshed!'); fetchData() }
      else toast.error('Seed endpoint not available')
    } catch { toast.error('Backend not reachable') }
    finally { setSeedLoading(false) }
  }

  const simulateHypeSurge = async () => {
    setHyping(true)
    try {
      // Hype the top 5 open reports from different users via API
      const openReports = allReports.filter(r => r.status !== 'resolved').slice(0, 5)
      await Promise.all(openReports.map(r => reportsAPI.hype(r.id).catch(() => {})))
      toast.success('Hype surge simulated on top 5 reports!')
      fetchData()
    } finally { setHyping(false) }
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (!data) return <EmptyState icon="📊" title="No analytics yet" description="Seed some data first." />

  const statusFunnel = Object.entries(data.by_status).map(([name, value]) => ({ name, value }))
  const categoryData = Object.entries(data.by_category).map(([name, value]) => ({ name, value }))
  const flaggedReports = allReports.filter(r => r.status === 'pending_confirmation')

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="flex gap-2">
          <button onClick={simulateHypeSurge} disabled={hyping} className="btn-secondary text-xs py-1.5 px-3">
            {hyping ? <Spinner size="sm" /> : '🔥 Simulate Hype Surge'}
          </button>
          <button onClick={seedDemo} disabled={seedLoading} className="btn-primary text-xs py-1.5 px-3">
            {seedLoading ? <Spinner size="sm" /> : '🌱 Refresh Demo Data'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 w-fit">
        {['overview', 'hotspots', 'recurring', 'flagged', 'hype'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${tab === t ? 'bg-white shadow text-gray-900' : 'text-gray-500'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            <KPICard label="Total Reports" value={data.total_reports} />
            <KPICard label="Open" value={data.open_reports} color="text-orange-600" />
            <KPICard label="Resolved" value={data.resolved_reports} color="text-green-600" />
            <KPICard label="Avg Resolution" value={data.avg_resolution_hours ? `${data.avg_resolution_hours}h` : '—'} />
            <KPICard label="% Duplicates" value={`${data.duplicate_percentage}%`} />
            <KPICard label="Critical Open" value={data.critical_open} color={data.critical_open > 0 ? 'text-red-600' : 'text-green-600'} />
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Reports per day */}
            <div className="card">
              <p className="text-sm font-semibold text-gray-700 mb-3">Reports per Day (last 30 days)</p>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={data.reports_per_day}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#ef4444" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Category split donut */}
            <div className="card">
              <p className="text-sm font-semibold text-gray-700 mb-3">Category Split</p>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={categoryData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={40} outerRadius={70} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false} fontSize={11}>
                    {categoryData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Resolution by department */}
            <div className="card">
              <p className="text-sm font-semibold text-gray-700 mb-3">Avg Resolution Time by Dept (hours)</p>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={data.resolution_by_department}>
                  <XAxis dataKey="department" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="avg_hours" fill="#f97316" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Status funnel */}
            <div className="card">
              <p className="text-sm font-semibold text-gray-700 mb-3">Status Distribution</p>
              <div className="space-y-1.5">
                {statusFunnel.map((s, i) => (
                  <div key={s.name} className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-28 truncate">{s.name.replace(/_/g, ' ')}</span>
                    <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${(s.value / data.total_reports) * 100}%`, backgroundColor: COLORS[i % COLORS.length] }} />
                    </div>
                    <span className="text-xs font-bold text-gray-600 w-6 text-right">{s.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {tab === 'hotspots' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Top buildings table */}
          <div className="card">
            <p className="text-sm font-semibold text-gray-700 mb-3">Top 5 Hotspot Buildings</p>
            <table className="w-full text-xs">
              <thead><tr className="text-gray-400 border-b"><th className="text-left pb-2">Building</th><th className="text-right pb-2">Reports</th></tr></thead>
              <tbody>
                {data.top_buildings.map((b, i) => (
                  <tr key={b.building} className="border-b border-gray-50">
                    <td className="py-2 font-medium">{i + 1}. {b.building}</td>
                    <td className="py-2 text-right text-red-600 font-bold">{b.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Campus heat grid */}
          <div className="card">
            <p className="text-sm font-semibold text-gray-700 mb-3">Campus Heat Grid</p>
            <div className="grid grid-cols-3 gap-2">
              {data.top_buildings.concat(
                Array.from({ length: Math.max(0, 9 - data.top_buildings.length) }, (_, i) => ({ building: `Block ${String.fromCharCode(65 + i)}`, count: 0 }))
              ).slice(0, 9).map((b, i) => {
                const max = data.top_buildings[0]?.count || 1
                const intensity = b.count / max
                const bg = intensity > 0.7 ? 'bg-red-500' : intensity > 0.4 ? 'bg-orange-400' : intensity > 0.1 ? 'bg-amber-300' : 'bg-gray-100'
                return (
                  <div key={i} className={`${bg} rounded-lg p-2 text-center`}>
                    <p className={`text-xs font-semibold ${intensity > 0.4 ? 'text-white' : 'text-gray-700'} leading-tight`}>{b.building.split(' ').slice(0, 2).join(' ')}</p>
                    <p className={`text-lg font-bold ${intensity > 0.4 ? 'text-white' : 'text-gray-800'}`}>{b.count}</p>
                  </div>
                )
              })}
            </div>
            <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
              <span className="w-3 h-3 bg-gray-100 rounded" /> Low
              <span className="w-3 h-3 bg-amber-300 rounded" /> Medium
              <span className="w-3 h-3 bg-orange-400 rounded" /> High
              <span className="w-3 h-3 bg-red-500 rounded" /> Critical
            </div>
          </div>
        </div>
      )}

      {tab === 'recurring' && (
        <div className="card">
          <p className="text-sm font-semibold text-gray-700 mb-3">Recurring Issues</p>
          {data.recurring_issues.length === 0
            ? <EmptyState icon="🔁" title="No recurring issues" />
            : <table className="w-full text-xs">
              <thead><tr className="text-gray-400 border-b">
                <th className="text-left pb-2">Title</th>
                <th className="text-left pb-2">Building</th>
                <th className="text-right pb-2">Recurrences</th>
              </tr></thead>
              <tbody>
                {data.recurring_issues.map(r => (
                  <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 font-medium">{r.title}</td>
                    <td className="py-2 text-gray-500">{r.building}</td>
                    <td className="py-2 text-right text-purple-600 font-bold">×{r.recurrence_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        </div>
      )}

      {tab === 'flagged' && (
        <div className="card">
          <p className="text-sm font-semibold text-gray-700 mb-3">Flagged for Review (pending confirmation)</p>
          {flaggedReports.length === 0
            ? <EmptyState icon="✅" title="Nothing flagged" />
            : <div className="space-y-2">
              {flaggedReports.map(r => (
                <div key={r.id} className="flex items-center justify-between p-3 border border-orange-200 rounded-lg bg-orange-50">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{r.title}</p>
                    <p className="text-xs text-gray-500">{r.building} · Awaiting reporter</p>
                  </div>
                  <a href={`/reports/${r.id}`} className="text-xs text-red-600 hover:underline">View →</a>
                </div>
              ))}
            </div>
          }
        </div>
      )}

      {tab === 'hype' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card">
            <p className="text-sm font-semibold text-gray-700 mb-3">Hype Leaderboard (by building)</p>
            {data.hype_leaderboard.map((h, i) => (
              <div key={h.building} className="flex items-center justify-between py-2 border-b border-gray-50">
                <span className="text-sm">{i + 1}. {h.building}</span>
                <span className="text-sm font-bold text-red-500">🔥 {h.total_hypes}</span>
              </div>
            ))}
          </div>
          <div className="card">
            <p className="text-sm font-semibold text-gray-700 mb-3">Top Hyped Reports</p>
            {allReports.sort((a, b) => b.hype_count - a.hype_count).slice(0, 8).map(r => (
              <div key={r.id} className="flex items-center justify-between py-2 border-b border-gray-50">
                <span className="text-xs text-gray-700 truncate pr-2">{r.title}</span>
                <span className="text-xs font-bold text-red-500 flex-shrink-0">🔥 {r.hype_count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
