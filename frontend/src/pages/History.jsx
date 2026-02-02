import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const JOURNAL_URL = import.meta.env.VITE_JOURNAL_URL || 'http://localhost:8080'

export default function History() {
  const { token } = useAuth()
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    setError('')
    fetch(`${JOURNAL_URL}/api/v1/entries?size=50`, { headers, cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status))
        return res.json()
      })
      .then((data) => {
        setEntries(Array.isArray(data.content) ? data.content : (Array.isArray(data) ? data : []))
      })
      .catch((err) => {
        if (err.message === '401') {
          setError('Please log in again.')
        } else if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
          setError(`Could not reach the journal service. Is it running at ${JOURNAL_URL}?`)
        } else {
          setError('Could not load entries. Check that the journal service is running and you are logged in.')
        }
      })
      .finally(() => setLoading(false))
  }, [token])

  const formatDate = (iso) => {
    try {
      const d = new Date(iso)
      return d.toLocaleDateString(undefined, { dateStyle: 'medium' }) + ' ' + d.toLocaleTimeString(undefined, { timeStyle: 'short' })
    } catch {
      return iso
    }
  }

  if (loading) return <p className="text-sage-500">Loading...</p>
  if (error) return <p className="text-red-600">{error}</p>

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-xl font-semibold text-sage-700">Past entries</h1>
      {entries.length === 0 ? (
        <p className="text-sage-500">No entries yet. Write something on Today.</p>
      ) : (
        <ul className="space-y-4">
          {entries.map((e) => (
            <li key={e.id} className="bg-white border border-sage-200 rounded-card p-4 shadow-soft">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <p className="text-sm text-sage-500">{formatDate(e.createdAt)}</p>
                {e.mood && (
                  <span className="text-xs font-medium text-sage-600 bg-sage-100 rounded-full px-2.5 py-0.5">
                    {e.mood}
                  </span>
                )}
              </div>
              <p className="text-sage-700 whitespace-pre-wrap leading-relaxed">{e.content}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
