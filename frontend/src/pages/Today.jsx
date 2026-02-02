import { useState, useEffect, useRef, useMemo } from 'react'
import { useAuth } from '../context/AuthContext'
import OnboardingModal, { setOnboardingDone } from '../components/OnboardingModal'

const JOURNAL_URL = import.meta.env.VITE_JOURNAL_URL || 'http://localhost:8080'
const PROMPT_URL = import.meta.env.VITE_PROMPT_URL || 'http://localhost:8000'
const ROTATION_INTERVAL_MS = 4500

const MOOD_OPTIONS = [
  'Calm', 'Anxious', 'Grateful', 'Tired', 'Hopeful',
  'Frustrated', 'Peaceful', 'Overwhelmed', 'Joyful', 'Reflective',
]

// Quick check-in: slider 1–5 maps to short mood labels for API
const QUICK_MOOD_LABELS = ['Rough', 'Low', 'Okay', 'Good', 'Great']

export default function Today() {
  const { token, user } = useAuth()
  const textareaRef = useRef(null)
  const [initialPrompt, setInitialPrompt] = useState('') // today's prompt from API (reset when "Done for now")
  const [prompt, setPrompt] = useState('') // pinned prompt (shown when rotation is stopped)
  const [suggestions, setSuggestions] = useState([])
  const [content, setContent] = useState('')
  const [mood, setMood] = useState(null)
  const [loadingPrompt, setLoadingPrompt] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showFollowUp, setShowFollowUp] = useState(false)
  const [followUpPrompts, setFollowUpPrompts] = useState([])
  const [rotationIndex, setRotationIndex] = useState(0)
  const [pinned, setPinned] = useState(false) // true = stop rotation and show pinned prompt
  const [streak, setStreak] = useState(null) // { streak, entriesThisWeek } from API
  const [showQuickCheckInModal, setShowQuickCheckInModal] = useState(false)
  const [quickMoodSlider, setQuickMoodSlider] = useState(3) // 1–5, default "Okay"
  const [quickCheckInContent, setQuickCheckInContent] = useState('') // content only when modal is open
  const quickCheckInRef = useRef(null)

  const allPrompts = useMemo(() => {
    const list = [initialPrompt, ...suggestions].filter(Boolean)
    return [...new Set(list)]
  }, [initialPrompt, suggestions])

  const displayPrompt = pinned ? prompt : (allPrompts[rotationIndex % (allPrompts.length || 1)] ?? prompt)

  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }

  useEffect(() => {
    let cancelled = false
    async function fetchPromptAndSuggestions() {
      try {
        const [promptRes, suggestionsRes, entriesRes] = await Promise.all([
          fetch(`${PROMPT_URL}/api/v1/prompts/today`, { headers, cache: 'no-store' }),
          fetch(`${PROMPT_URL}/api/v1/prompts/suggestions`, { headers, cache: 'no-store' }),
          fetch(`${JOURNAL_URL}/api/v1/entries?size=1`, { headers, cache: 'no-store' }),
        ])
        if (!cancelled) {
          const defaultPrompt = "What's on your mind today?"
          if (promptRes.ok) {
            const data = await promptRes.json()
            const p = data.prompt || defaultPrompt
            setInitialPrompt(p)
            setPrompt(p)
          } else {
            setInitialPrompt(defaultPrompt)
            setPrompt(defaultPrompt)
          }
          if (suggestionsRes.ok) {
            const data = await suggestionsRes.json()
            setSuggestions(Array.isArray(data.suggestions) ? data.suggestions.slice(0, 3) : [])
          } else {
            setSuggestions([])
          }
        }
      } catch {
        if (!cancelled) {
          const defaultPrompt = "What's on your mind today?"
          setInitialPrompt(defaultPrompt)
          setPrompt(defaultPrompt)
          setSuggestions([])
        }
      } finally {
        if (!cancelled) setLoadingPrompt(false)
      }
    }
    fetchPromptAndSuggestions()
    return () => { cancelled = true }
  }, [token])

  // Fetch streak on load so the card shows even if prompt/suggestions fail
  useEffect(() => {
    let cancelled = false
    async function fetchStreak() {
      try {
        const res = await fetch(`${JOURNAL_URL}/api/v1/entries/streak`, { headers, cache: 'no-store' })
        if (cancelled) return
        if (res.ok) {
          const data = await res.json()
          setStreak({ streak: data.streak ?? 0, entriesThisWeek: data.entriesThisWeek ?? 0 })
        } else {
          setStreak({ streak: 0, entriesThisWeek: 0 })
        }
      } catch {
        if (!cancelled) setStreak({ streak: 0, entriesThisWeek: 0 })
      }
    }
    fetchStreak()
    return () => { cancelled = true }
  }, [token])

  useEffect(() => {
    if (pinned || allPrompts.length <= 1) return
    const id = setInterval(() => {
      setRotationIndex((i) => i + 1)
    }, ROTATION_INTERVAL_MS)
    return () => clearInterval(id)
  }, [pinned, allPrompts.length])

  const save = async (e) => {
    e.preventDefault()
    if (!content.trim()) return
    setSaving(true)
    setMessage('')
    try {
      const body = { content: content.trim() }
      if (mood) body.mood = mood
      const res = await fetch(`${JOURNAL_URL}/api/v1/entries`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        cache: 'no-store',
      })
      if (!res.ok) {
        const text = await res.text()
        if (res.status === 401 || res.status === 403) {
          setMessage('Session invalid. Please sign out and sign in again.')
          return
        }
        if (res.status >= 500) {
          setMessage('Journal service error. Check that it is running.')
          return
        }
        throw new Error(text || `Save failed (${res.status})`)
      }
      const savedContent = content.trim()
      setMessage('Saved.')
      setContent('')
      setMood(null)
      setShowFollowUp(true)
      setFollowUpPrompts([])
      try {
        const [streakRes, followUpRes] = await Promise.all([
          fetch(`${JOURNAL_URL}/api/v1/entries/streak`, { headers, cache: 'no-store' }),
          fetch(`${PROMPT_URL}/api/v1/prompts/follow-up`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ last_entry: savedContent ? savedContent.slice(0, 800) : '' }),
            cache: 'no-store',
          }),
        ])
        if (streakRes.ok) {
          const data = await streakRes.json()
          const newStreak = data.streak ?? 0
          const newEntriesThisWeek = data.entriesThisWeek ?? 0
          setStreak({ streak: newStreak, entriesThisWeek: newEntriesThisWeek })
          if (newStreak >= 2) {
            setMessage(`Saved. You're on a ${newStreak}-day streak!`)
          } else if (newEntriesThisWeek >= 1) {
            setMessage(`Saved. You've written ${newEntriesThisWeek} time${newEntriesThisWeek === 1 ? '' : 's'} this week.`)
          }
        }
        if (followUpRes?.ok) {
          const data = await followUpRes.json()
          const list = Array.isArray(data.prompts) && data.prompts.length > 0
            ? data.prompts
            : (data.prompt ? [data.prompt] : [])
          setFollowUpPrompts(list)
        }
      } catch {
        // keep "Saved." if streak/follow-up fetch fails
      }
    } catch (err) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setMessage('Cannot reach journal service. Is it running on ' + JOURNAL_URL + '?')
      } else {
        setMessage('Failed to save. Try again.')
      }
    } finally {
      setSaving(false)
    }
  }

  const dismissOnboarding = () => {
    setOnboardingDone()
    setShowOnboarding(false)
  }

  const refreshTodayPrompt = async () => {
    try {
      const res = await fetch(`${PROMPT_URL}/api/v1/prompts/today`, { headers, cache: 'no-store' })
      if (res.ok) {
        const data = await res.json()
        const p = data.prompt || "What's on your mind today?"
        setInitialPrompt(p)
        setPrompt(p)
      }
    } catch {
      // keep current prompt on failure
    }
  }

  const openQuickCheckIn = () => {
    setQuickCheckInContent('')
    setQuickMoodSlider(3)
    setShowQuickCheckInModal(true)
    setTimeout(() => quickCheckInRef.current?.focus(), 100)
  }

  const saveQuickCheckIn = async (e) => {
    e.preventDefault()
    if (!quickCheckInContent.trim()) return
    setSaving(true)
    setMessage('')
    try {
      const body = {
        content: quickCheckInContent.trim(),
        mood: QUICK_MOOD_LABELS[quickMoodSlider - 1],
      }
      const res = await fetch(`${JOURNAL_URL}/api/v1/entries`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        cache: 'no-store',
      })
      if (!res.ok) {
        const text = await res.text()
        if (res.status === 401 || res.status === 403) {
          setMessage('Session invalid. Please sign out and sign in again.')
          return
        }
        setMessage('Failed to save. Try again.')
        return
      }
      setQuickCheckInContent('')
      setShowQuickCheckInModal(false)
      try {
        const streakRes = await fetch(`${JOURNAL_URL}/api/v1/entries/streak`, { headers, cache: 'no-store' })
        if (streakRes.ok) {
          const data = await streakRes.json()
          const newStreak = data.streak ?? 0
          const newEntriesThisWeek = data.entriesThisWeek ?? 0
          setStreak({ streak: newStreak, entriesThisWeek: newEntriesThisWeek })
          if (newStreak >= 2) {
            setMessage(`Quick check-in saved. You're on a ${newStreak}-day streak!`)
          } else if (newEntriesThisWeek >= 1) {
            setMessage(`Quick check-in saved. You've written ${newEntriesThisWeek} time${newEntriesThisWeek === 1 ? '' : 's'} this week.`)
          } else {
            setMessage('Quick check-in saved.')
          }
        } else {
          setMessage('Quick check-in saved.')
        }
      } catch {
        setMessage('Quick check-in saved.')
      }
    } catch (err) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setMessage('Cannot reach journal service.')
      } else {
        setMessage('Failed to save. Try again.')
      }
    } finally {
      setSaving(false)
    }
  }

  const streakCopy =
    streak == null
      ? null
      : streak.streak >= 2
        ? `Keep it going — write today to extend your ${streak.streak}-day streak.`
        : streak.streak === 1
          ? "You wrote yesterday. One more day to grow your streak!"
          : streak.entriesThisWeek >= 1
            ? `You have ${streak.entriesThisWeek} ${streak.entriesThisWeek === 1 ? 'entry' : 'entries'} this week. Write today to start a streak.`
            : "Your first entry starts a streak. Take a minute to check in."

  return (
    <div className="space-y-6">
      {showOnboarding && <OnboardingModal onDismiss={dismissOnboarding} />}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="font-serif text-xl font-semibold text-sage-700">
          {user?.firstName?.trim() ? `Hi, ${user.firstName.trim()}` : 'Today'}
        </h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowOnboarding(true)}
            className="text-sm font-medium text-sage-600 bg-sage-50 hover:bg-sage-100 border border-sage-200 rounded-xl px-3 py-1.5 transition-colors"
            title="What to expect"
          >
            Psst...
          </button>
          <button
            type="button"
            onClick={openQuickCheckIn}
            className="text-sm font-medium text-sage-600 bg-sage-50 hover:bg-sage-100 border border-sage-300 rounded-xl px-3 py-1.5 transition-colors"
          >
            Quick check-in (1 min)
          </button>
        </div>
      </div>

      {streak != null && (
        <div
          className={`rounded-xl border-2 p-4 ${
            streak.streak >= 2
              ? 'border-amber-300 bg-amber-50'
              : streak.streak === 1 || streak.entriesThisWeek >= 1
                ? 'border-slate-200 bg-slate-50'
                : 'border-slate-200 bg-slate-50'
          }`}
        >
          <div className="flex items-center gap-3 flex-wrap">
            {streak.streak >= 1 ? (
              <div className="flex items-center gap-2">
                <span className="text-2xl" aria-hidden>🔥</span>
                <span className="text-xl font-bold text-slate-800">
                  {streak.streak}-day streak
                </span>
              </div>
            ) : (
              <span className="text-lg font-semibold text-slate-700">Your streak</span>
            )}
            {streak.entriesThisWeek >= 0 && (
              <span className="text-sm text-slate-600">
                {streak.entriesThisWeek} {streak.entriesThisWeek === 1 ? 'entry' : 'entries'} this week
              </span>
            )}
          </div>
          {streakCopy && (
            <p className="text-sm text-slate-600 mt-2">{streakCopy}</p>
          )}
        </div>
      )}

      {loadingPrompt ? (
        <p className="text-sage-500">Loading prompt...</p>
      ) : (
        <>
          <div className="space-y-1">
            <button
              type="button"
              onClick={() => {
                setPrompt(displayPrompt)
                setPinned(true)
                setContent('')
                setShowFollowUp(false)
                setTimeout(() => textareaRef.current?.focus(), 0)
              }}
              className="w-full text-left text-sage-700 bg-sage-50 hover:bg-sage-100 border border-sage-200 rounded-card p-4 italic transition-colors"
            >
              "{displayPrompt}"
            </button>
            {pinned && allPrompts.length > 1 && (
              <button
                type="button"
                onClick={() => setPinned(false)}
                className="text-sm text-sage-500 hover:text-sage-700 transition-colors"
              >
                Choose another prompt
              </button>
            )}
          </div>
          <form onSubmit={save} className="space-y-4">
            <div>
              <p className="text-sm text-sage-600 mb-2">How are you feeling? (optional)</p>
              <div className="flex flex-wrap gap-2">
                {MOOD_OPTIONS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMood(mood === m ? null : m)}
                    className={`rounded-full px-3 py-1.5 text-sm font-medium border-2 transition-colors ${
                      mood === m
                        ? 'border-sage-500 bg-sage-500 text-white'
                        : 'border-sage-300 bg-white text-sage-600 hover:border-sage-400'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your entry..."
              rows={6}
              className="w-full border border-sage-200 rounded-card px-3 py-2.5 text-sage-700 placeholder-sage-300 resize-y focus:outline-none focus:ring-2 focus:ring-sage-300/50 focus:border-sage-400"
            />
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={saving || !content.trim()}
                className="bg-sage-500 text-white rounded-xl px-4 py-2 font-medium hover:bg-sage-600 disabled:opacity-50 transition-colors"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              {message && <span className="text-sm text-sage-600">{message}</span>}
            </div>
          </form>
        </>
      )}
      {showFollowUp && (
        <div className="border-t border-slate-200 pt-4 space-y-2">
          <p className="text-sm text-slate-600">Want to go deeper?</p>
          {followUpPrompts.map((p, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setPrompt(p)
                setPinned(true)
                setContent('')
                setShowFollowUp(false)
                setTimeout(() => textareaRef.current?.focus(), 0)
              }}
              className="text-sm text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-lg px-3 py-2 text-left w-full block"
            >
              {p}
            </button>
          ))}
          <button
            type="button"
            onClick={() => {
              setShowFollowUp(false)
              setPinned(false)
              refreshTodayPrompt()
            }}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Done for now
          </button>
        </div>
      )}

      {showQuickCheckInModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => setShowQuickCheckInModal(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="quick-check-in-title"
        >
          <div
            className="bg-white rounded-card shadow-card border border-sage-100 max-w-md w-full p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 id="quick-check-in-title" className="font-serif text-lg font-semibold text-sage-700">
                Quick check-in (1 min)
              </h2>
              <button
                type="button"
                onClick={() => setShowQuickCheckInModal(false)}
                className="text-sage-400 hover:text-sage-600 p-1 rounded transition-colors"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <p className="text-sage-600 italic text-sm">"{initialPrompt || "What's on your mind today?"}"</p>
            <form onSubmit={saveQuickCheckIn} className="space-y-4">
              <div>
                <p className="text-sm text-sage-600 mb-2">How are you right now?</p>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-sage-500">Rough</span>
                  <input
                    type="range"
                    min={1}
                    max={5}
                    value={quickMoodSlider}
                    onChange={(e) => setQuickMoodSlider(Number(e.target.value))}
                    className="flex-1 h-2 bg-sage-200 rounded-lg appearance-none cursor-pointer accent-sage-600"
                  />
                  <span className="text-xs text-sage-500">Great</span>
                </div>
                <p className="text-sm font-medium text-sage-700 mt-1">{QUICK_MOOD_LABELS[quickMoodSlider - 1]}</p>
              </div>
              <textarea
                ref={quickCheckInRef}
                value={quickCheckInContent}
                onChange={(e) => setQuickCheckInContent(e.target.value)}
                placeholder="One line is enough."
                rows={3}
                className="w-full border border-sage-200 rounded-card px-3 py-2 text-sage-700 placeholder-sage-300 resize-y focus:outline-none focus:ring-2 focus:ring-sage-300/50"
              />
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving || !quickCheckInContent.trim()}
                  className="bg-sage-500 text-white rounded-xl px-4 py-2 font-medium hover:bg-sage-600 disabled:opacity-50 transition-colors"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowQuickCheckInModal(false)}
                  className="text-sage-600 hover:text-sage-700 text-sm transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
