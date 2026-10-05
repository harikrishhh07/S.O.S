import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('sos_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('sos_token')
    if (token) {
      authAPI.me()
        .then(r => { setUser(r.data); localStorage.setItem('sos_user', JSON.stringify(r.data)) })
        .catch(() => { localStorage.removeItem('sos_token'); localStorage.removeItem('sos_user'); setUser(null) })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const r = await authAPI.login({ email, password })
    localStorage.setItem('sos_token', r.data.access_token)
    localStorage.setItem('sos_user', JSON.stringify(r.data.user))
    setUser(r.data.user)
    return r.data.user
  }

  const register = async (data) => {
    const r = await authAPI.register(data)
    localStorage.setItem('sos_token', r.data.access_token)
    localStorage.setItem('sos_user', JSON.stringify(r.data.user))
    setUser(r.data.user)
    return r.data.user
  }

  const logout = () => {
    localStorage.removeItem('sos_token')
    localStorage.removeItem('sos_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
