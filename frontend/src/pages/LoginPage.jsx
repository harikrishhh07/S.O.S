import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { gsap } from 'gsap'
import { ANIM } from '../animations/config'
import toast from 'react-hot-toast'
import { AlertTriangle } from 'lucide-react'

const DEPARTMENTS = [
  { id: 'architect_services', label: 'Architect Services' },
  { id: 'facility_services', label: 'Facility Services' },
  { id: 'hostel_services', label: 'Hostel Services' },
  { id: 'transport_services', label: 'Transport Services' },
  { id: 'security_services', label: 'Security Services' },
  { id: 'housekeeping_services', label: 'Housekeeping Services' },
  { id: 'electrical_services', label: 'Electrical Services' },
  { id: 'civil_plumbing_services', label: 'Civil & Plumbing Services' },
  { id: 'fire_safety_services', label: 'Fire & Safety Services' },
  { id: 'hvac_ac_services', label: 'HVAC / AC Services' },
  { id: 'it_telecom_services', label: 'IT & Telecom Services' },
  { id: 'laundry_services', label: 'Laundry Services' },
  { id: 'mess_food_services', label: 'Mess / Food Services' },
  { id: 'transport_parking', label: 'Transport & Parking' },
  { id: 'landscaping_campus', label: 'Landscaping & Campus Maintenance' },
  { id: 'waste_management', label: 'Waste Management' },
  { id: 'student_admin_services', label: 'Student / Administrative Services' },
  { id: 'medical_health_services', label: 'Medical / Health Services' },
  { id: 'library_services', label: 'Library Services' },
  { id: 'sports_recreation', label: 'Sports & Recreation' },
  { id: 'labs_technical', label: 'Laboratories & Technical Facilities' },
  { id: 'procurement_stores', label: 'Procurement / Stores' },
  { id: 'environment_sustainability', label: 'Environment & Sustainability' },
  { id: 'events_campus_facilities', label: 'Events & Campus Facilities' },
]

export default function LoginPage() {
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student', department: '' })
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const heroRef = useRef(null)

  // Staggered entrance on mount
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: ANIM.hero_ease } })
      tl.from('.login-icon',  { scale: 0.5, opacity: 0, duration: ANIM.slow,   rotate: -15 })
        .from('.login-title', { y: 20, opacity: 0, duration: ANIM.normal }, '-=0.4')
        .from('.login-sub',   { y: 15, opacity: 0, duration: ANIM.normal }, '-=0.35')
        .from('.login-card',  { y: 30, opacity: 0, duration: ANIM.slow,   scale: 0.97 }, '-=0.3')
    }, heroRef)
    return () => ctx.revert()
  }, [])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      let user
      if (mode === 'login') {
        user = await login(form.email, form.password)
      } else {
        user = await register(form)
      }
      toast.success(`Welcome, ${user.name}!`)
      if (user.role === 'admin') navigate('/admin')
      else if (user.role === 'authority') navigate('/authority')
      else navigate('/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div ref={heroRef} className="min-h-screen bg-gradient-to-br from-red-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="login-icon inline-flex items-center justify-center w-16 h-16 bg-red-600 rounded-2xl mb-3 shadow-lg">
            <AlertTriangle size={32} className="text-white" />
          </div>
          <h1 className="login-title text-2xl font-bold text-gray-900">S.O.S.</h1>
          <p className="login-sub text-gray-500 text-sm mt-1">Spark On-Site Solutions</p>
          <p className="login-sub text-gray-400 text-xs mt-0.5">Campus Hazard Reporting</p>
        </div>

        {/* Card */}
        <div className="login-card card shadow-lg">
          {/* Tab switch */}
          <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
            {['login', 'register'].map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                data-cursor="link"
                className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-all ${
                  mode === m ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Register'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input className="input" data-cursor="text" value={form.name} onChange={set('name')} required placeholder="Your name" />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input className="input" data-cursor="text" type="email" value={form.email} onChange={set('email')} required placeholder="you@university.edu" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input className="input" data-cursor="text" type="password" value={form.password} onChange={set('password')} required placeholder="••••••••" minLength={6} />
            </div>

            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select className="input" data-cursor="link" value={form.role} onChange={set('role')}>
                    <option value="student">Student / Staff</option>
                    <option value="authority">Authority</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                {form.role === 'authority' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                    <select className="input" data-cursor="link" value={form.department} onChange={set('department')}>
                      <option value="">Select department</option>
                      {DEPARTMENTS.map(department => (
                        <option key={department.id} value={department.id}>{department.label}</option>
                      ))}
                    </select>
                  </div>
                )}
              </>
            )}

            <button type="submit" className="btn-primary w-full" data-cursor="link" data-magnetic="0.3" disabled={loading}>
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Demo shortcuts */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-gray-500 mb-2 font-medium">Quick demo login:</p>
            <div className="flex flex-wrap gap-1.5">
              {[
                { label: 'Admin',     email: 'admin@university.edu',       password: 'admin123' },
                { label: 'Authority', email: 'electrical@university.edu',  password: 'auth123'  },
                { label: 'Student',   email: 'student@university.edu',     password: 'student123' },
              ].map(d => (
                <button
                  key={d.label}
                  data-cursor="link"
                  className="text-xs bg-gray-100 hover:bg-gray-200 px-2.5 py-1 rounded-md transition-colors"
                  onClick={() => { setForm(f => ({ ...f, email: d.email, password: d.password })); setMode('login') }}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
