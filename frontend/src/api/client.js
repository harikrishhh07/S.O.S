import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sos_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sos_token')
      localStorage.removeItem('sos_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsAPI = {
  list: (params) => api.get('/reports', { params }),
  mine: () => api.get('/reports/mine'),
  get: (id) => api.get(`/reports/${id}`),
  delete: (id) => api.delete(`/reports/${id}`),
  create: (formData) => api.post('/reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  updateStatus: (id, data) => api.patch(`/reports/${id}/status`, data),
  assign: (id, data) => api.patch(`/reports/${id}/assign`, data),
  hype: (id) => api.post(`/reports/${id}/hype`),
  unhype: (id) => api.delete(`/reports/${id}/hype`),
  resolve: (id, formData) => api.post(`/reports/${id}/resolve`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  confirm: (id, confirmed) => api.post(`/reports/${id}/confirm`, new URLSearchParams({ confirmed })),
  autoResolveStale: () => api.post('/reports/admin/auto-resolve-stale'),
}

// ── Notifications ─────────────────────────────────────────────────────────────
export const notificationsAPI = {
  list: () => api.get('/notifications'),
  markAllRead: () => api.patch('/notifications/read'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
}

// ── Locations ─────────────────────────────────────────────────────────────────
export const locationsAPI = {
  list: () => api.get('/locations'),
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export const analyticsAPI = {
  summary: () => api.get('/analytics/summary'),
  digest: () => api.get('/analytics/digest'),
  generateDigest: () => api.post('/analytics/digest/generate'),
}

// ── Location Inference (Feature 2) ────────────────────────────────────────────
export const locationInferenceAPI = {
  inferFromImage: (imageFile) => {
    const fd = new FormData()
    fd.append('image', imageFile)
    return api.post('/reports/infer-location', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export default api
