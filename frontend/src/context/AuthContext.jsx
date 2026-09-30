import { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      api.get('/auth/me')
        .then((res) => setUser(res.data.data))
        .catch(() => localStorage.clear())
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('access_token', data.data.access_token)
    localStorage.setItem('refresh_token', data.data.refresh_token)
    const me = await api.get('/auth/me')
    setUser(me.data.data)
    return me.data.data
  }

  const register = async (payload) => {
    await api.post('/auth/register', payload)
    return login(payload.email, payload.password)
  }

  const logout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await api.post('/auth/logout', { refresh_token: refresh })
    } catch {}
    localStorage.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAdmin: user?.role === 'admin', isAgent: user?.role === 'agent' || user?.role === 'admin' }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
