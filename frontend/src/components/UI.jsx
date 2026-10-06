// Shared UI components

// ── Severity Badge ────────────────────────────────────────────────────────────
export function SeverityBadge({ severity }) {
  const labels = { 1: 'Low', 2: 'Minor', 3: 'Moderate', 4: 'High', 5: 'Critical' }
  return (
    <span className={`badge severity-${severity}`}>
      S{severity} · {labels[severity] || 'Unknown'}
    </span>
  )
}

// ── Status Badge ──────────────────────────────────────────────────────────────
export function StatusBadge({ status }) {
  const label = status?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return <span className={`badge status-${status}`}>{label}</span>
}

// ── Category Badge ────────────────────────────────────────────────────────────
// Maps taxonomy department ids to display-friendly short labels + colors
const DEPT_DISPLAY = {
  electrical_services:       { label: 'Electrical',    cls: 'bg-yellow-100 text-yellow-800' },
  civil_plumbing_services:   { label: 'Civil',         cls: 'bg-blue-100 text-blue-800' },
  security_services:         { label: 'Security',      cls: 'bg-red-100 text-red-800' },
  fire_safety_services:      { label: 'Fire & Safety', cls: 'bg-orange-100 text-orange-800' },
  housekeeping_services:     { label: 'Housekeeping',  cls: 'bg-green-100 text-green-800' },
  hvac_ac_services:          { label: 'HVAC / AC',     cls: 'bg-cyan-100 text-cyan-800' },
  it_telecom_services:       { label: 'IT & Telecom',  cls: 'bg-indigo-100 text-indigo-800' },
  facility_services:         { label: 'Facility',      cls: 'bg-purple-100 text-purple-800' },
  hostel_services:           { label: 'Hostel',        cls: 'bg-pink-100 text-pink-800' },
  transport_services:        { label: 'Transport',     cls: 'bg-sky-100 text-sky-800' },
  medical_health_services:   { label: 'Medical',       cls: 'bg-rose-100 text-rose-800' },
  mess_food_services:        { label: 'Mess / Food',   cls: 'bg-lime-100 text-lime-800' },
  laundry_services:          { label: 'Laundry',       cls: 'bg-teal-100 text-teal-800' },
  waste_management:          { label: 'Waste Mgmt',    cls: 'bg-stone-100 text-stone-700' },
  landscaping_campus:              { label: 'Landscaping',   cls: 'bg-emerald-100 text-emerald-800' },
  landscaping_campus_maintenance:  { label: 'Landscaping',   cls: 'bg-emerald-100 text-emerald-800' },
  housekeeping:                    { label: 'Housekeeping',  cls: 'bg-green-100 text-green-800' },
  landscaping:                     { label: 'Landscaping',   cls: 'bg-emerald-100 text-emerald-800' },
  transport_parking:         { label: 'Parking',       cls: 'bg-sky-100 text-sky-800' },
  library_services:          { label: 'Library',       cls: 'bg-violet-100 text-violet-800' },
  sports_recreation:         { label: 'Sports',        cls: 'bg-fuchsia-100 text-fuchsia-800' },
  labs_technical:            { label: 'Labs',          cls: 'bg-amber-100 text-amber-800' },
  procurement_stores:        { label: 'Procurement',   cls: 'bg-zinc-100 text-zinc-700' },
  architect_services:        { label: 'Architect',     cls: 'bg-blue-100 text-blue-800' },
  environment_sustainability:{ label: 'Environment',   cls: 'bg-green-100 text-green-800' },
  events_campus_facilities:  { label: 'Events',        cls: 'bg-purple-100 text-purple-800' },
  student_admin_services:    { label: 'Admin',         cls: 'bg-gray-100 text-gray-800' },
  // Legacy 4-category fallback
  electrical: { label: 'Electrical', cls: 'bg-yellow-100 text-yellow-800' },
  civil:      { label: 'Civil',      cls: 'bg-blue-100 text-blue-800' },
  security:   { label: 'Security',   cls: 'bg-red-100 text-red-800' },
  other:      { label: 'Other',      cls: 'bg-gray-100 text-gray-800' },
}

export function CategoryBadge({ category, serviceLabel }) {
  const info = DEPT_DISPLAY[category]
  const label = serviceLabel || info?.label || (category ? category.replace(/_/g, ' ') : 'Other')
  const cls = info?.cls || 'bg-gray-100 text-gray-800'
  return <span className={`badge ${cls}`}>{label}</span>
}

// ── Skeleton ──────────────────────────────────────────────────────────────────
export function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`skeleton ${className}`} />
}

export function ReportCardSkeleton() {
  return (
    <div className="card space-y-3">
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
    </div>
  )
}

// ── Priority Bar ──────────────────────────────────────────────────────────────
export function PriorityBar({ score }) {
  const color = score >= 80 ? 'bg-red-500' : score >= 50 ? 'bg-orange-400' : score >= 30 ? 'bg-amber-400' : 'bg-green-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-bold text-gray-600">{Math.round(score)}</span>
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────────────────
export function EmptyState({ icon = '📭', title = 'Nothing here yet', description = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-5xl mb-3">{icon}</div>
      <h3 className="font-semibold text-gray-800 text-lg">{title}</h3>
      {description && <p className="text-gray-500 text-sm mt-1">{description}</p>}
    </div>
  )
}

// ── Loading Spinner ───────────────────────────────────────────────────────────
export function Spinner({ size = 'md' }) {
  const sz = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-8 w-8' : 'h-6 w-6'
  return (
    <div className={`${sz} border-2 border-red-500 border-t-transparent rounded-full animate-spin`} />
  )
}

// ── Safe Critical Banner ──────────────────────────────────────────────────────
export function CriticalBanner() {
  return (
    <div className="flex items-center gap-2 bg-red-600 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
      🚨 SAFETY CRITICAL
    </div>
  )
}
