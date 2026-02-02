import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:3001'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const path = isSignUp ? '/api/v1/auth/signup' : '/api/v1/auth/login'
      const body = isSignUp
        ? { email, password, firstName: firstName.trim(), lastName: lastName.trim() }
        : { email, password }
      const res = await fetch(`${AUTH_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.error || 'Request failed')
      login(data.token, {
        email: data.email,
        userId: data.userId,
        firstName: data.firstName ?? '',
        lastName: data.lastName ?? '',
      })
      navigate('/')
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper flex flex-col items-center justify-center p-4 gap-6">
      <img src="/antar-logo.png" alt="Antar.AI" className="h-36 w-auto max-w-full" />
      <div className="w-full max-w-sm bg-white rounded-card shadow-card border border-sage-100 p-6">
        <form onSubmit={submit} className="space-y-4">
          {isSignUp && (
            <>
              <div>
                <label className="block text-sm text-sage-600 mb-1">First name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Optional"
                  className="w-full border border-sage-200 rounded-xl px-3 py-2.5 text-sage-700 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-300/50 focus:border-sage-400"
                />
              </div>
              <div>
                <label className="block text-sm text-sage-600 mb-1">Last name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Optional"
                  className="w-full border border-sage-200 rounded-xl px-3 py-2.5 text-sage-700 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-300/50 focus:border-sage-400"
                />
              </div>
            </>
          )}
          <div>
            <label className="block text-sm text-sage-600 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border border-sage-200 rounded-xl px-3 py-2.5 text-sage-700 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-300/50 focus:border-sage-400"
            />
          </div>
          <div>
            <label className="block text-sm text-sage-600 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-sage-200 rounded-xl px-3 py-2.5 text-sage-700 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-300/50 focus:border-sage-400"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-sage-500 text-white rounded-xl py-2.5 font-medium hover:bg-sage-600 disabled:opacity-50 transition-colors"
          >
            {loading ? '...' : isSignUp ? 'Sign up' : 'Log in'}
          </button>
        </form>
        <button
          type="button"
          onClick={() => { setIsSignUp((s) => !s); setError(''); }}
          className="mt-3 text-sm text-sage-600 hover:text-sage-700 transition-colors"
        >
          {isSignUp ? 'Already have an account? Log in' : 'Need an account? Sign up'}
        </button>
      </div>
    </div>
  )
}
