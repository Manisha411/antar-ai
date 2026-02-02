import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

const AUTH_KEY = 'journal_token'
const USER_KEY = 'journal_user'

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => localStorage.getItem(AUTH_KEY))
  const [user, setUserState] = useState(() => {
    try {
      const u = localStorage.getItem(USER_KEY)
      return u ? JSON.parse(u) : null
    } catch {
      return null
    }
  })

  const login = useCallback((newToken, newUser) => {
    setTokenState(newToken)
    setUserState(newUser)
    localStorage.setItem(AUTH_KEY, newToken)
    localStorage.setItem(USER_KEY, JSON.stringify(newUser || {}))
  }, [])

  const updateUser = useCallback((updates) => {
    setUserState((prev) => {
      const next = { ...prev, ...updates }
      localStorage.setItem(USER_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  const logout = useCallback(() => {
    setTokenState(null)
    setUserState(null)
    localStorage.removeItem(AUTH_KEY)
    localStorage.removeItem(USER_KEY)
  }, [])

  return (
    <AuthContext.Provider value={{ token, user, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
