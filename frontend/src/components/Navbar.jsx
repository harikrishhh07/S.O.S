import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { notificationsAPI } from '../api/client'
import { Bell, Menu, X, AlertTriangle } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [notifs, setNotifs] = useState([])
  const [showNotifs, setShowNotifs] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const notifRef = useRef(null)

  useEffect(() => {
    if (!user) return
    notificationsAPI.list().then(r => setNotifs(r.data)).catch(() => {})
    const interval = setInterval(() => {
      notificationsAPI.list().then(r => setNotifs(r.data)).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [user])

  const unread = notifs.filter(n => !n.read).length

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const markAllRead = () => {
    notificationsAPI.markAllRead().then(() => setNotifs(prev => prev.map(n => ({ ...n, read: true }))))
  }

  if (!user) return null

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-red-600 text-lg">
          <AlertTriangle size={20} />
          S.O.S.
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          <Link to="/" className="nav-link text-gray-600 hover:text-red-600 transition-colors" data-cursor="link">Feed</Link>
          {(user.role === 'student' || user.role === 'authority') && (
            <Link to="/report/new" className="btn-primary text-sm py-1.5 px-3" data-cursor="link" data-magnetic="0.35">+ Report Hazard</Link>
          )}
          {(user.role === 'authority' || user.role === 'admin') && (
            <Link to="/authority" className="nav-link text-gray-600 hover:text-red-600" data-cursor="link">Queue</Link>
          )}
          {user.role === 'admin' && (
            <Link to="/admin" className="nav-link text-gray-600 hover:text-red-600" data-cursor="link">Admin</Link>
          )}
          <Link to="/my-reports" className="nav-link text-gray-600 hover:text-red-600" data-cursor="link">My Reports</Link>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setShowNotifs(!showNotifs)}
              className="relative p-2 text-gray-600 hover:text-red-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Bell size={20} />
              {unread > 0 && (
                <span className="absolute top-0.5 right-0.5 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unread > 9 ? '9+' : unread}
                </span>
              )}
            </button>

            {showNotifs && (
              <div className="absolute right-0 top-10 w-80 bg-white rounded-xl shadow-xl border border-gray-100 z-50">
                <div className="flex items-center justify-between px-4 py-3 border-b">
                  <span className="font-semibold text-sm">Notifications</span>
                  {unread > 0 && (
                    <button onClick={markAllRead} className="text-xs text-red-600 hover:underline">
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-72 overflow-y-auto divide-y divide-gray-50">
                  {notifs.length === 0 ? (
                    <div className="px-4 py-6 text-center text-gray-400 text-sm">No notifications</div>
                  ) : (
                    notifs.slice(0, 15).map(n => (
                      <div
                        key={n.id}
                        className={`px-4 py-3 text-xs hover:bg-gray-50 cursor-pointer ${!n.read ? 'bg-red-50' : ''}`}
                        onClick={() => { if (n.report_id) navigate(`/reports/${n.report_id}`); setShowNotifs(false) }}
                      >
                        <p className={`${!n.read ? 'font-semibold text-gray-800' : 'text-gray-600'}`}>{n.message}</p>
                        <p className="text-gray-400 mt-0.5">{new Date(n.sent_at).toLocaleString()}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="hidden md:flex items-center gap-2">
            <span className="text-sm text-gray-600">{user.name}</span>
            <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-red-600 transition-colors">
              Logout
            </button>
          </div>

          {/* Mobile menu toggle */}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2">
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t px-4 py-3 space-y-2">
          <Link to="/" className="block py-2 text-sm" onClick={() => setMobileOpen(false)}>Feed</Link>
          <Link to="/report/new" className="block py-2 text-sm font-semibold text-red-600" onClick={() => setMobileOpen(false)}>+ Report Hazard</Link>
          {(user.role === 'authority' || user.role === 'admin') && <Link to="/authority" className="block py-2 text-sm" onClick={() => setMobileOpen(false)}>Queue</Link>}
          {user.role === 'admin' && <Link to="/admin" className="block py-2 text-sm" onClick={() => setMobileOpen(false)}>Admin</Link>}
          <Link to="/my-reports" className="block py-2 text-sm" onClick={() => setMobileOpen(false)}>My Reports</Link>
          <button onClick={handleLogout} className="block py-2 text-sm text-red-600">Logout</button>
        </div>
      )}
    </nav>
  )
}
