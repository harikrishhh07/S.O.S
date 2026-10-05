import { useState, useEffect } from 'react'
import { reportsAPI } from '../api/client'
import ReportCard from '../components/ReportCard'
import { ReportCardSkeleton, EmptyState } from '../components/UI'
import { Link } from 'react-router-dom'

export default function MyReportsPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    reportsAPI.mine()
      .then(r => setReports(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">My Reports</h1>
        <Link to="/report/new" className="btn-primary text-sm py-1.5 px-3">+ New Report</Link>
      </div>

      <div className="space-y-3">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <ReportCardSkeleton key={i} />)
          : reports.length === 0
            ? <EmptyState icon="📋" title="No reports yet" description="Report a campus hazard to get started." />
            : reports.map(r => <ReportCard key={r.id} report={r} />)
        }
      </div>
    </div>
  )
}
