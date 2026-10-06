import { useState } from 'react'
import { analyticsAPI } from '../api/client'
import { Download } from 'lucide-react'
import { jsPDF } from 'jspdf'

export default function WeeklyDigestCard() {
  const [digest, setDigest] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(false)

  const digestData = digest?.error ? { ...digest.stats, ...digest } : digest
  const renderDigest = digestData && (digestData.week_summary || digestData.stats)

  async function generate() {
    setLoading(true)
    setError(null)
    try {
      const response = await analyticsAPI.generateDigest()
      setDigest(response.data)
      setOpen(true)
    } catch {
      setError('Failed to generate digest. Check API connection.')
    } finally {
      setLoading(false)
    }
  }

  function downloadPdf() {
    if (!digestData) return

    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 16
    const contentWidth = pageWidth - margin * 2
    const generatedAt = new Date(digestData.generated_at)
    const generatedLabel = generatedAt.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
    let y = 118

    const ensureSpace = (height) => {
      if (y + height > pageHeight - 24) {
        doc.addPage()
        y = 20
      }
    }

    const addSection = (title, content, accent = [124, 58, 237]) => {
      const lines = doc.splitTextToSize(String(content || 'N/A'), contentWidth - 14)
      const height = 16 + lines.length * 5 + 10
      ensureSpace(height)
      doc.setFillColor(248, 250, 252)
      doc.setDrawColor(226, 232, 240)
      doc.roundedRect(margin, y - 5, contentWidth, height, 3, 3, 'FD')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(11)
      doc.setTextColor(...accent)
      doc.text(title, margin + 7, y + 3)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9.5)
      doc.setTextColor(55, 65, 81)
      doc.text(lines, margin + 7, y + 16)
      y += height + 7
    }

    doc.setFillColor(185, 28, 28)
    doc.rect(0, 0, pageWidth, 43, 'F')
    doc.setFillColor(239, 68, 68)
    doc.circle(pageWidth - 22, 14, 18, 'F')
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(20)
    doc.setTextColor(255, 255, 255)
    doc.text('S.O.S.', margin, 17)
    doc.setFontSize(11)
    doc.text('CAMPUS HEALTH REPORT', margin, 27)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.text('Weekly AI Digest', margin, 35)

    doc.setFillColor(254, 242, 242)
    doc.roundedRect(margin, 48, contentWidth, 25, 3, 3, 'F')
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(127, 29, 29)
    doc.text('REPORTING PERIOD', margin + 7, 58)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(55, 65, 81)
    doc.text(String(digestData.period || 'N/A'), margin + 7, 67)
    doc.setFontSize(8.5)
    doc.setTextColor(107, 114, 128)
    doc.text(`Generated on ${generatedLabel}`, pageWidth - margin - 7, 58, { align: 'right' })
    doc.text(`AI status: ${digestData.ai_available === false ? 'Fallback summary' : 'AI generated'}`, pageWidth - margin - 7, 67, { align: 'right' })

    const stats = digestData.stats || {}
    const metrics = [
      ['REPORTS', stats.total_reports ?? 0, [124, 58, 237]],
      ['RESOLVED', stats.resolved ?? 0, [22, 163, 74]],
      ['OPEN', stats.open ?? 0, [217, 119, 6]],
      ['CRITICAL', stats.safety_critical ?? 0, [220, 38, 38]],
    ]
    const gap = 3
    const metricWidth = (contentWidth - gap * 3) / 4
    metrics.forEach(([label, value, color], index) => {
      const x = margin + index * (metricWidth + gap)
      doc.setFillColor(255, 255, 255)
      doc.setDrawColor(226, 232, 240)
      doc.roundedRect(x, 80, metricWidth, 24, 3, 3, 'FD')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(16)
      doc.setTextColor(...color)
      doc.text(String(value), x + 6, 92)
      doc.setFontSize(7)
      doc.setTextColor(107, 114, 128)
      doc.text(label, x + 6, 99)
    })

    addSection('Executive Summary', digestData.week_summary)
    addSection('Resolution Performance', `Average resolution time: ${stats.avg_resolution_hours ?? 'N/A'} hours\nOpen reports requiring attention: ${stats.open ?? 0}`, [37, 99, 235])
    if (digestData.top_issue) addSection('Top Issue', `${digestData.top_issue.title}: ${digestData.top_issue.detail}`, [234, 88, 12])
    if (digestData.hotspot_building) addSection('Hotspot Building', `${digestData.hotspot_building.name} (${digestData.hotspot_building.count} reports)\nMain issue: ${digestData.hotspot_building.main_issue?.replace(/_/g, ' ') || 'N/A'}`, [220, 38, 38])
    if (digestData.department_spotlight) addSection('Department Spotlight', `Fastest: ${digestData.department_spotlight.fastest}\nNeeds attention: ${digestData.department_spotlight.needs_attention}`, [37, 99, 235])
    if (digestData.pattern_to_watch) addSection('Pattern to Watch', digestData.pattern_to_watch, [202, 138, 4])
    if (digestData.positive_highlight) addSection('Positive Highlight', digestData.positive_highlight, [22, 163, 74])
    if (digestData.recommendations?.length) addSection('Recommendations', digestData.recommendations.map((item, index) => `${index + 1}. ${item}`).join('\n'))

    const pageCount = doc.getNumberOfPages()
    for (let page = 1; page <= pageCount; page += 1) {
      doc.setPage(page)
      doc.setDrawColor(226, 232, 240)
      doc.line(margin, pageHeight - 17, pageWidth - margin, pageHeight - 17)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(8)
      doc.setTextColor(107, 114, 128)
      doc.text('S.O.S. Campus Hazard Reporting', margin, pageHeight - 9)
      doc.text(`Generated ${generatedLabel}`, pageWidth / 2, pageHeight - 9, { align: 'center' })
      doc.text(`Page ${page} of ${pageCount}`, pageWidth - margin, pageHeight - 9, { align: 'right' })
    }
    doc.save(`sos-weekly-digest-${new Date().toISOString().slice(0, 10)}.pdf`)
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📋</span>
          <div>
            <h3 className="font-semibold text-gray-900 text-sm">Weekly AI Digest</h3>
            <p className="text-xs text-gray-400">Gemini-generated campus health summary</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {renderDigest && <button onClick={downloadPdf} title="Download digest as PDF" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-medium transition"><Download size={14} /> PDF</button>}
          <button onClick={generate} disabled={loading} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white text-xs font-medium transition">
            {loading ? <><span className="animate-spin">⚙️</span> Generating…</> : <><span>✨</span> Generate</>}
          </button>
        </div>
      </div>
      {error && <div className="px-5 py-3 text-red-600 text-sm bg-red-50">{error}</div>}
      {renderDigest && open && (
        <div className="p-5 space-y-4">
          <div className="flex flex-wrap gap-3">
            <span className="text-xs bg-violet-50 text-violet-700 px-2 py-1 rounded-full font-medium">📅 {digestData.period}</span>
            {digestData.department_scope && <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full font-medium">🏢 {digestData.department_scope}</span>}
            {digestData.stats && <>
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{digestData.stats.total_reports} reports</span>
              <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full">✅ {digestData.stats.resolved} resolved</span>
              <span className="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full">🔓 {digestData.stats.open} open</span>
              {digestData.stats.safety_critical > 0 && <span className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded-full font-semibold">🚨 {digestData.stats.safety_critical} critical</span>}
            </>}
          </div>
          <div className="bg-violet-50 rounded-xl p-3"><p className="text-sm text-violet-900 leading-relaxed">{digestData.week_summary}</p></div>
          {digestData.top_issue && <div className="flex gap-3 items-start p-3 bg-orange-50 rounded-xl"><span className="text-xl">🔥</span><div><p className="text-sm font-semibold text-orange-800">{digestData.top_issue.title}</p><p className="text-xs text-orange-700 mt-0.5">{digestData.top_issue.detail}</p></div></div>}
          <div className="grid grid-cols-2 gap-3">
            {digestData.hotspot_building && <div className="p-3 bg-red-50 rounded-xl"><p className="text-xs text-red-500 font-medium mb-1">🗺️ HOTSPOT BUILDING</p><p className="text-sm font-bold text-red-800">{digestData.hotspot_building.name}</p><p className="text-xs text-red-600">{digestData.hotspot_building.count} reports · {digestData.hotspot_building.main_issue?.replace(/_/g, ' ')}</p></div>}
            {digestData.department_spotlight && <div className="p-3 bg-blue-50 rounded-xl"><p className="text-xs text-blue-500 font-medium mb-1">🏆 DEPARTMENTS</p><p className="text-xs text-blue-800"><span className="font-semibold">Fastest:</span> {digestData.department_spotlight.fastest}</p><p className="text-xs text-amber-700 mt-1"><span className="font-semibold">Needs attention:</span> {digestData.department_spotlight.needs_attention}</p></div>}
          </div>
          {digestData.pattern_to_watch && <div className="flex gap-2 p-3 bg-yellow-50 rounded-xl text-sm text-yellow-800"><span>👁️</span><p><span className="font-semibold">Watch:</span> {digestData.pattern_to_watch}</p></div>}
          {digestData.positive_highlight && <div className="flex gap-2 p-3 bg-green-50 rounded-xl text-sm text-green-800"><span>✨</span><p>{digestData.positive_highlight}</p></div>}
          {digestData.recommendations?.length > 0 && <div><p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Recommendations</p><ul className="space-y-1.5">{digestData.recommendations.map((item, index) => <li key={index} className="flex gap-2 text-sm text-gray-700"><span className="text-violet-500 font-bold">{index + 1}.</span>{item}</li>)}</ul></div>}
          <p className="text-xs text-gray-400 text-right">Generated {generatedAtLabel(digestData.generated_at)} · Powered by Gemini</p>
        </div>
      )}
      {!digest && !loading && <div className="px-5 py-8 text-center text-gray-400 text-sm">Click <strong>Generate</strong> to get this week&apos;s AI campus health summary</div>}
    </div>
  )
}

function generatedAtLabel(value) {
  return new Date(value).toLocaleString()
}
