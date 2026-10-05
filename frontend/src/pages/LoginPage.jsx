import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { AlertTriangle } from 'lucide-react'

export default function LoginPage() {
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student', department: '' })
  const { login, register } = useAuth()
  const navigate = useNavigate()

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
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-600 rounded-2xl mb-3 shadow-lg">
            <AlertTriangle size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">S.O.S.</h1>
          <p className="text-gray-500 text-sm mt-1">Spark On-Site Solutions</p>
          <p className="text-gray-400 text-xs mt-0.5">Campus Hazard Reporting</p>
        </div>

        {/* Card */}
        <div className="card shadow-lg">
          {/* Tab switch */}
          <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
            {['login', 'register'].map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
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
                <input className="input" value={form.name} onChange={set('name')} required placeholder="Your name" />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input className="input" type="email" value={form.email} onChange={set('email')} required placeholder="you@university.edu" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input className="input" type="password" value={form.password} onChange={set('password')} required placeholder="••••••••" minLength={6} />
            </div>

            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select className="input" value={form.role} onChange={set('role')}>
                    <option value="student">Student / Staff</option>
                    <option value="authority">Authority</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                {form.role === 'authority' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                    <select className="input" value={form.department} onChange={set('department')}>
                      <option value="">Select department</option>
                      <option value="Electrical">Electrical</option>
                      <option value="Civil">Civil / Maintenance</option>
                      <option value="Security">Security</option>
                      <option value="Admin">Admin</option>
                    </select>
                  </div>
                )}
              </>
            )}

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Demo shortcuts */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-gray-500 mb-2 font-medium">Quick demo login:</p>
            <div className="flex flex-wrap gap-1.5">
              {[
                { label: 'Student', email: 'arjun@student.edu', password: 'student123' },
                { label: 'Authority', email: 'raj.elec@university.edu', password: 'auth123' },
                { label: 'Admin', email: 'admin@university.edu', password: 'admin123' },
              ].map(d => (
                <button
                  key={d.label}
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
