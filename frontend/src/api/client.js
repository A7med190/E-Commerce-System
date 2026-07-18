const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

function getToken() {
  return localStorage.getItem('access_token')
}

function getRefresh() {
  return localStorage.getItem('refresh_token')
}

async function refreshAccessToken() {
  const refresh = getRefresh()
  if (!refresh) return null
  const res = await fetch(`${API_BASE}/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) return null
  const data = await res.json()
  localStorage.setItem('access_token', data.access)
  return data.access
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

export async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res = await fetch(url, { ...options, headers })

  if (res.status === 401 && getRefresh() && !path.includes('/auth/refresh')) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(url, { ...options, headers })
    }
  }

  if (res.status === 204) return null
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) {
    const message =
      (data && (data.detail || (data.non_field_errors && data.non_field_errors[0]))) ||
      'Request failed'
    throw new ApiError(message, res.status, data)
  }
  return data
}

export const api = {
  get: (path) => apiFetch(path, { method: 'GET' }),
  post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: (path, body) => apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) }),
  put: (path, body) => apiFetch(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => apiFetch(path, { method: 'DELETE' }),
}
