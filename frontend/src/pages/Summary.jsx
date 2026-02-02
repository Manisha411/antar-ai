import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const SUMMARY_URL = import.meta.env.VITE_SUMMARY_URL || 'http://localhost:8002'

function SectionTitle({ children }) {
  return <h3 className="text-sm font-semibold text-sage-700 mt-5 mb-1 first:mt-0">{children}</h3>
}

function StructuredSummary({ sections, period }) {
  if (!sections || typeof sections !== 'object') return null
  const isWeekly = period === 'weekly' || sections.reflection_prompt != null
  return (
    <div className="space-y-1">
      {/* Header */}
      <div className="pb-2 border-b border-sage-200">
        <h2 className="font-serif text-lg font-semibold text-sage-700">{sections.header_title || 'Your Reflection'}</h2>
        {sections.header_subtitle && (
          <p className="text-sm text-sage-500 mt-0.5">{sections.header_subtitle}</p>
        )}
      </div>

      {/* Emotional snapshot (weekly) or Overall tone (monthly) */}
      {(sections.emotional_snapshot || sections.overall_tone) && (
        <p className="text-sage-700 leading-relaxed">
          {sections.emotional_snapshot || sections.overall_tone}
        </p>
      )}

      {/* Recurring themes (weekly) */}
      {sections.recurring_themes?.length > 0 && (
        <>
          <SectionTitle>Recurring themes</SectionTitle>
          <ul className="list-disc list-inside text-sage-700 space-y-1 text-sm">
            {sections.recurring_themes.map((line, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
            ))}
          </ul>
        </>
      )}

      {/* Gentle connections (weekly) */}
      {sections.gentle_connections && (
        <>
          <SectionTitle>Gentle connections</SectionTitle>
          <p className="text-sage-700 text-sm italic">&ldquo;{sections.gentle_connections}&rdquo;</p>
        </>
      )}

      {/* Theme evolution (monthly) */}
      {sections.theme_evolution?.length > 0 && (
        <>
          <SectionTitle>Theme evolution</SectionTitle>
          <ul className="list-disc list-inside text-sage-700 space-y-1 text-sm">
            {sections.theme_evolution.map((line, i) => (
              <li key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
            ))}
          </ul>
        </>
      )}

      {/* Notable patterns (monthly) */}
      {sections.notable_patterns?.length > 0 && (
        <>
          <SectionTitle>Notable patterns</SectionTitle>
          <ul className="list-disc list-inside text-sage-700 space-y-1 text-sm">
            {sections.notable_patterns.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </>
      )}

      {/* Progress highlight (monthly) */}
      {sections.progress_highlight && (
        <>
          <SectionTitle>Progress</SectionTitle>
          <p className="text-sage-700 text-sm">{sections.progress_highlight}</p>
        </>
      )}

      {/* Reflection prompt (weekly) */}
      {sections.reflection_prompt?.length > 0 && (
        <>
          <SectionTitle>Reflection questions</SectionTitle>
          <ul className="list-none space-y-2 text-slate-700 text-sm">
            {sections.reflection_prompt.map((q, i) => (
              <li key={i} className="pl-0">"{q}"</li>
            ))}
          </ul>
        </>
      )}

      {/* Looking ahead (monthly) */}
      {sections.looking_ahead && (
        <>
          <SectionTitle>Looking ahead</SectionTitle>
          <p className="text-sage-700 text-sm italic">&ldquo;{sections.looking_ahead}&rdquo;</p>
        </>
      )}
    </div>
  )
}

const PERIODS = [
  { id: 'daily', label: 'Daily', description: 'Reflection on today’s entries' },
  { id: 'weekly', label: 'Weekly', description: 'Key themes and patterns this week' },
  { id: 'monthly', label: 'Monthly', description: 'Themes and progress over the month' },
]

export default function Summary() {
  const { token } = useAuth()
  const [period, setPeriod] = useState('weekly')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generatingPeriod, setGeneratingPeriod] = useState(null)
  const headers = { Authorization: `Bearer ${token}` }

  const fetchLatest = (periodFilter) => {
    setLoading(true)
    setError('')
    const url = periodFilter
      ? `${SUMMARY_URL}/api/v1/summaries/latest?period=${periodFilter}`
      : `${SUMMARY_URL}/api/v1/summaries/latest`
    fetch(url, { headers, cache: 'no-store' })
      .then((r) => {
        if (r.status === 404) return null
        if (!r.ok) throw new Error('Failed to load summary')
        return r.json()
      })
      .then((data) => setSummary(data))
      .catch(() => setError('Could not load summary.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchLatest(period)
  }, [token, period])

  const generate = (periodType) => {
    if (generatingPeriod) return
    setGeneratingPeriod(periodType)
    setError('')
    const endpoint = periodType === 'daily' ? 'daily' : periodType === 'monthly' ? 'monthly' : 'weekly'
    fetch(`${SUMMARY_URL}/api/v1/summaries/${endpoint}`, { headers, cache: 'no-store' })
      .then(async (r) => {
        const data = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(data.detail || data.message || 'Failed to generate summary')
        return data
      })
      .then((data) => {
        setSummary(data)
        if (period !== periodType) setPeriod(periodType)
      })
      .catch((err) => setError(err.message || 'Could not generate summary.'))
      .finally(() => setGeneratingPeriod(null))
  }

  if (loading && !summary) return <p className="text-sage-500">Loading...</p>

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-xl font-semibold text-sage-700">Reflection summaries</h1>
      <p className="text-sm text-sage-600">
        Reflection summaries reflect patterns, not behavior. They describe what came up for you — like a gentle mirror — without judgment or advice.
      </p>

      <div className="flex gap-2 border-b border-sage-200 pb-2">
        {PERIODS.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setPeriod(p.id)}
            className={`px-4 py-2 rounded-t text-sm font-medium transition-colors ${
              period === p.id
                ? 'bg-sage-500 text-white'
                : 'bg-sage-100 text-sage-600 hover:bg-sage-200'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {error && <p className="text-red-600">{error}</p>}

      {summary ? (
        <div className="bg-white border border-sage-200 rounded-card p-6 shadow-soft">
          {summary.sections ? (
            <StructuredSummary sections={summary.sections} period={period} />
          ) : (
            <p className="text-sage-700 whitespace-pre-wrap leading-relaxed">{summary.summary}</p>
          )}
          <p className="text-xs text-sage-500 mt-4 pt-4 border-t border-sage-100">
            Period: {summary.period_start?.slice(0, 10)} – {summary.period_end?.slice(0, 10)}
          </p>
        </div>
      ) : (
        <p className="text-sage-500">
          No {period} summary yet. Generate one from your recent entries.
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        {PERIODS.map((p) => {
          const isThisGenerating = generatingPeriod === p.id
          return (
            <button
              key={p.id}
              type="button"
              data-period={p.id}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (generatingPeriod) return
                generate(e.currentTarget.dataset.period)
              }}
              disabled={isThisGenerating}
              className={`rounded-card px-4 py-2 font-medium transition-colors ${
                isThisGenerating
                  ? 'bg-sage-300 text-white cursor-wait'
                  : 'bg-sage-500 text-white hover:bg-sage-600 disabled:opacity-70'
              }`}
            >
              {isThisGenerating ? 'Generating...' : `Generate ${p.label.toLowerCase()} summary`}
            </button>
          )
        })}
      </div>
    </div>
  )
}
