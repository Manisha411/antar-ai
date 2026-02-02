import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const JOURNAL_URL = import.meta.env.VITE_JOURNAL_URL || 'http://localhost:8080'
const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:3001'

export default function Profile() {
  const { token, user, updateUser } = useAuth()
  const [exporting, setExporting] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [firstName, setFirstName] = useState(user?.firstName ?? '')
  const [lastName, setLastName] = useState(user?.lastName ?? '')
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileError, setProfileError] = useState('')
  useEffect(() => {
    setFirstName(user?.firstName ?? '')
    setLastName(user?.lastName ?? '')
  }, [user?.firstName, user?.lastName])
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }

  const fetchAllEntries = async () => {
    const all = []
    let page = 0
    const size = 50
    while (true) {
      const res = await fetch(
        `${JOURNAL_URL}/api/v1/entries?page=${page}&size=${size}`,
        { headers }
      )
      if (!res.ok) throw new Error('Failed to fetch entries')
      const data = await res.json()
      const items = data.content ?? data
      if (!items?.length) break
      all.push(...items)
      if (items.length < size) break
      page++
    }
    return all
  }

  const handleExport = async () => {
    setExporting(true)
    setError('')
    setMessage('')
    try {
      const entries = await fetchAllEntries()
      const blob = new Blob(
        [JSON.stringify({ exportedAt: new Date().toISOString(), entries }, null, 2)],
        { type: 'application/json' }
      )
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `journal-export-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
      setMessage('Export downloaded.')
    } catch (err) {
      setError(err.message || 'Export failed.')
    } finally {
      setExporting(false)
    }
  }

  const handleDeleteAll = () => {
    if (!confirmDelete) {
      setConfirmDelete(true)
      setError('')
      setMessage('')
      return
    }
    doDelete()
  }

  const doDelete = async () => {
    setDeleting(true)
    setError('')
    setMessage('')
    try {
      const res = await fetch(`${JOURNAL_URL}/api/v1/entries`, {
        method: 'DELETE',
        headers,
      })
      if (!res.ok) throw new Error('Failed to delete journal data')
      setMessage('All journal entries have been deleted.')
      setConfirmDelete(false)
    } catch (err) {
      setError(err.message || 'Delete failed.')
    } finally {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  const cancelDelete = () => {
    setConfirmDelete(false)
    setError('')
  }

  const handleUpdateName = async (e) => {
    e.preventDefault()
    setProfileError('')
    setSavingProfile(true)
    try {
      const res = await fetch(`${AUTH_URL}/api/v1/auth/profile`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ firstName: firstName.trim(), lastName: lastName.trim() }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.error || 'Failed to update name')
      updateUser({ firstName: data.firstName ?? '', lastName: data.lastName ?? '' })
      setMessage('Name updated.')
      setTimeout(() => setMessage(''), 3000)
    } catch (err) {
      setProfileError(err.message || 'Could not update name.')
    } finally {
      setSavingProfile(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-xl font-semibold text-sage-700">Profile</h1>

      {/* Basic details */}
      <div className="bg-white border border-sage-200 rounded-card p-6 shadow-soft">
        <h2 className="font-serif text-sm font-semibold text-sage-700 mb-3">Account details</h2>
        <dl className="space-y-2 text-sm">
          <div>
            <dt className="text-sage-500">First name</dt>
            <dd className="text-sage-700 font-medium">{user?.firstName ? user.firstName : '—'}</dd>
          </div>
          <div>
            <dt className="text-sage-500">Last name</dt>
            <dd className="text-sage-700 font-medium">{user?.lastName ? user.lastName : '—'}</dd>
          </div>
          <div>
            <dt className="text-sage-500">Email</dt>
            <dd className="text-sage-700 font-medium">{user?.email ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-sage-500">Account ID</dt>
            <dd className="text-sage-600 font-mono text-xs truncate max-w-full" title={user?.userId}>
              {user?.userId ?? '—'}
            </dd>
          </div>
        </dl>
        <form onSubmit={handleUpdateName} className="mt-4 pt-4 border-t border-sage-100 space-y-3">
          <h3 className="text-xs font-medium text-sage-600 uppercase tracking-wide">Update name</h3>
          <div className="flex flex-wrap gap-3">
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="First name"
              className="flex-1 min-w-[120px] border border-sage-200 rounded-xl px-3 py-2 text-sage-700 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-300/50"
            />
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Last name"
              className="flex-1 min-w-[120px] border border-sage-200 rounded-xl px-3 py-2 text-sage-700 placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-sage-300/50"
            />
          </div>
          {profileError && <p className="text-sm text-red-600">{profileError}</p>}
          <button
            type="submit"
            disabled={savingProfile}
            className="bg-sage-500 text-white rounded-xl px-4 py-2 font-medium hover:bg-sage-600 disabled:opacity-50"
          >
            {savingProfile ? 'Saving...' : 'Save name'}
          </button>
        </form>
      </div>

      {/* Export / Delete */}
      <div className="bg-white border border-sage-200 rounded-card p-6 shadow-soft space-y-4">
        <h2 className="font-serif text-sm font-semibold text-sage-700">Data</h2>

        {message && <p className="text-sm text-sage-600">{message}</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="bg-sage-500 text-white rounded-xl px-4 py-2 font-medium hover:bg-sage-600 disabled:opacity-50"
          >
            {exporting ? 'Exporting...' : 'Export my journal'}
          </button>
          {!confirmDelete ? (
            <button
              type="button"
              onClick={handleDeleteAll}
              disabled={deleting}
              className="border border-red-200 text-red-700 bg-red-50 rounded-xl px-4 py-2 font-medium hover:bg-red-100 disabled:opacity-50"
            >
              Delete all journal data
            </button>
          ) : (
            <>
              <span className="text-sm text-sage-600 self-center">Delete all entries? This cannot be undone.</span>
              <button
                type="button"
                onClick={doDelete}
                disabled={deleting}
                className="bg-red-600 text-white rounded-xl px-4 py-2 font-medium hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Yes, delete everything'}
              </button>
              <button
                type="button"
                onClick={cancelDelete}
                disabled={deleting}
                className="text-sage-600 hover:text-sage-800 font-medium"
              >
                Cancel
              </button>
            </>
          )}
        </div>
        <p className="text-xs text-sage-500">
          Export downloads all your journal entries as a JSON file. Delete removes all entries from this account permanently; your login (email) is unchanged.
        </p>
      </div>
    </div>
  )
}
