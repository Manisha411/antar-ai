import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts'

const INSIGHTS_URL = import.meta.env.VITE_INSIGHTS_URL || 'http://localhost:8001'
const JOURNAL_URL = import.meta.env.VITE_JOURNAL_URL || 'http://localhost:8080'

const DAYS_OPTIONS = [7, 30, 90]
const MOOD_COLORS = {
  Rough: '#fca5a5',
  Low: '#fdba74',
  Okay: '#e2e8f0',
  Good: '#86efac',
  Great: '#4ade80',
  Calm: '#a5b4fc',
  Anxious: '#f472b6',
  Grateful: '#fcd34d',
  Tired: '#94a3b8',
  Hopeful: '#67e8f9',
  Frustrated: '#f87171',
  Peaceful: '#bbf7d0',
  Overwhelmed: '#c4b5fd',
  Joyful: '#fde047',
  Reflective: '#cbd5e1',
}

function getMoodColor(mood) {
  return MOOD_COLORS[mood] || '#94a3b8'
}

// Short date for chart axis: "YYYY-MM-DD" -> "Jan 15" (or "M/D" when many points)
function formatChartDate(isoDateStr) {
  if (!isoDateStr || isoDateStr.length < 10) return isoDateStr || ''
  const [y, m, d] = isoDateStr.slice(0, 10).split('-').map(Number)
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[(m || 1) - 1]} ${d || 1}`
}

// Optional: mood-aligned music and ambient sound suggestions (no API; links open YouTube search)
const MOOD_MUSIC_AMBIENT = {
  Calm: {
    music: 'Ambient, soft piano, acoustic',
    musicQuery: 'calm ambient piano music',
    ambient: [
      { label: 'Rain', query: 'rain sounds relaxing' },
      { label: 'Nature', query: 'forest birds ambient' },
      { label: 'Ocean', query: 'ocean waves calm' },
    ],
  },
  Anxious: {
    music: 'Calming piano, lo-fi, slow tempo',
    musicQuery: 'calming music for anxiety',
    ambient: [
      { label: 'Rain', query: 'rain sounds sleep' },
      { label: 'White noise', query: 'white noise relaxing' },
      { label: 'Binaural', query: 'binaural beats calm' },
    ],
  },
  Grateful: {
    music: 'Uplifting acoustic, folk, gentle',
    musicQuery: 'grateful uplifting acoustic',
    ambient: [
      { label: 'Birds', query: 'morning birds peaceful' },
      { label: 'Stream', query: 'stream water sounds' },
    ],
  },
  Tired: {
    music: 'Lo-fi, minimal, no lyrics',
    musicQuery: 'lofi study chill',
    ambient: [
      { label: 'Rain', query: 'rain on window' },
      { label: 'Fan', query: 'fan white noise' },
    ],
  },
  Hopeful: {
    music: 'Uplifting, hopeful, inspiring',
    musicQuery: 'hopeful uplifting instrumental',
    ambient: [
      { label: 'Morning', query: 'morning birds sunrise' },
      { label: 'Nature', query: 'nature sounds peaceful' },
    ],
  },
  Frustrated: {
    music: 'Calm down, instrumental, slow',
    musicQuery: 'calm down music instrumental',
    ambient: [
      { label: 'Rain', query: 'heavy rain sounds' },
      { label: 'Thunder', query: 'distant thunder rain' },
    ],
  },
  Peaceful: {
    music: 'Ambient, meditation, gentle',
    musicQuery: 'peaceful meditation music',
    ambient: [
      { label: 'Ocean', query: 'ocean waves meditation' },
      { label: 'Zen', query: 'zen garden water' },
    ],
  },
  Overwhelmed: {
    music: 'Minimal, ambient, breathing space',
    musicQuery: 'minimal ambient calm',
    ambient: [
      { label: 'Rain', query: 'rain sounds focus' },
      { label: 'Cafe', query: 'coffee shop ambient' },
    ],
  },
  Joyful: {
    music: 'Upbeat acoustic, feel-good',
    musicQuery: 'joyful upbeat acoustic',
    ambient: [
      { label: 'Birds', query: 'birds singing happy' },
      { label: 'Stream', query: 'babbling brook' },
    ],
  },
  Reflective: {
    music: 'Piano, contemplative, soft',
    musicQuery: 'reflective piano contemplative',
    ambient: [
      { label: 'Rain', query: 'rain contemplative' },
      { label: 'Fire', query: 'fireplace crackling' },
    ],
  },
  Rough: {
    music: 'Gentle, supportive, no pressure',
    musicQuery: 'gentle comforting music',
    ambient: [
      { label: 'Rain', query: 'rain sounds calming' },
      { label: 'Ocean', query: 'ocean waves slow' },
    ],
  },
  Low: {
    music: 'Soft, warm, hopeful',
    musicQuery: 'soft hopeful music',
    ambient: [
      { label: 'Rain', query: 'rain sounds' },
      { label: 'Nature', query: 'nature ambient' },
    ],
  },
  Okay: {
    music: 'Neutral, easy listening',
    musicQuery: 'easy listening instrumental',
    ambient: [
      { label: 'Cafe', query: 'coffee shop sounds' },
      { label: 'Rain', query: 'light rain' },
    ],
  },
  Good: {
    music: 'Light, positive, acoustic',
    musicQuery: 'good mood acoustic',
    ambient: [
      { label: 'Nature', query: 'nature sounds' },
      { label: 'Birds', query: 'birds morning' },
    ],
  },
  Great: {
    music: 'Upbeat, celebratory, light',
    musicQuery: 'great day upbeat music',
    ambient: [
      { label: 'Ocean', query: 'ocean waves' },
      { label: 'Birds', query: 'birds singing' },
    ],
  },
}

function getMoodMusicAmbient(mood) {
  return MOOD_MUSIC_AMBIENT[mood] || MOOD_MUSIC_AMBIENT.Calm
}

function getSuggestedMood(moodTrend) {
  if (!moodTrend?.length) return null
  const recent = moodTrend.slice(-7)
  const counts = {}
  recent.forEach(({ moods }) => {
    moods.forEach(({ mood, count }) => {
      counts[mood] = (counts[mood] || 0) + count
    })
  })
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
  return sorted[0]?.[0] || null
}

function youtubeSearchUrl(query) {
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`
}

export default function Dashboard() {
  const { token } = useAuth()
  const [daysRange, setDaysRange] = useState(30)
  const [timeOfDay, setTimeOfDay] = useState('all')
  const [sentiment, setSentiment] = useState([])
  const [themesWithCounts, setThemesWithCounts] = useState([])
  const [themeSentimentBreakdown, setThemeSentimentBreakdown] = useState([])
  const [emotionsOverTime, setEmotionsOverTime] = useState([])
  const [moodTrend, setMoodTrend] = useState([]) // [{ date, moods: [{ mood, count }] }]
  const [caption, setCaption] = useState('')
  const [themeSentiment, setThemeSentiment] = useState({ low: [], neutral: [], high: [] })
  const [emotionsCaption, setEmotionsCaption] = useState('')
  const [patternInsights, setPatternInsights] = useState([])
  const [actionableActions, setActionableActions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const headers = { Authorization: `Bearer ${token}` }

  const timeParams = timeOfDay === 'morning' ? '&hour_from=0&hour_to=11' : timeOfDay === 'afternoon' ? '&hour_from=12&hour_to=17' : timeOfDay === 'evening' ? '&hour_from=18&hour_to=23' : ''

  useEffect(() => {
    const to = new Date()
    const from = new Date()
    from.setDate(from.getDate() - daysRange)
    const fromISO = from.toISOString()
    const toISO = to.toISOString()

    const fetchOpts = { headers, cache: 'no-store' }
    Promise.all([
      fetch(`${INSIGHTS_URL}/api/v1/insights/sentiment?days=${daysRange}${timeParams}`, fetchOpts).then((r) => (r.ok ? r.json() : { data: [] })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/themes/with-counts?days=${daysRange}`, fetchOpts).then((r) => (r.ok ? r.json() : { themes: [] })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/theme-sentiment-breakdown?days=${daysRange}`, fetchOpts).then((r) => (r.ok ? r.json() : { data: [] })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/emotions/over-time?days=${daysRange}`, fetchOpts).then((r) => (r.ok ? r.json() : { data: [] })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/week-caption`, fetchOpts).then((r) => (r.ok ? r.json() : { caption: '' })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/theme-sentiment?days=${daysRange}${timeParams}`, fetchOpts).then((r) => (r.ok ? r.json() : { low: [], neutral: [], high: [] })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/emotions?days=7`, fetchOpts).then((r) => (r.ok ? r.json() : { emotions: [], caption: '' })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/patterns?days=${daysRange}`, fetchOpts).then((r) => (r.ok ? r.json() : { insights: [] })),
      fetch(`${INSIGHTS_URL}/api/v1/insights/actionable?days=${daysRange}`, fetchOpts).then((r) => (r.ok ? r.json() : { actions: [] })),
      fetch(`${JOURNAL_URL}/api/v1/entries?from=${encodeURIComponent(fromISO)}&to=${encodeURIComponent(toISO)}&size=500`, fetchOpts).then((r) => (r.ok ? r.json() : { content: [] })),
    ])
      .then(([sentRes, themesCountRes, breakdownRes, emotionsOtRes, captionRes, themeSentRes, emotionsRes, patternsRes, actionableRes, entriesRes]) => {
        setSentiment(sentRes.data || [])
        setThemesWithCounts(themesCountRes.themes || [])
        setThemeSentimentBreakdown(breakdownRes.data || [])
        setEmotionsOverTime(emotionsOtRes.data || [])
        setCaption(captionRes.caption || '')
        setThemeSentiment({
          low: themeSentRes.low || [],
          neutral: themeSentRes.neutral || [],
          high: themeSentRes.high || [],
        })
        setEmotionsCaption(emotionsRes.caption || '')
        setPatternInsights(patternsRes.insights || [])
        setActionableActions(actionableRes.actions || [])

        const list = Array.isArray(entriesRes.content) ? entriesRes.content : []
        const byDate = {}
        list.forEach((e) => {
          const createdAt = e.createdAt
          if (!createdAt) return
          const d = createdAt.slice(0, 10)
          if (!byDate[d]) byDate[d] = {}
          const m = e.mood && String(e.mood).trim()
          if (m) byDate[d][m] = (byDate[d][m] || 0) + 1
        })
        const trend = Object.entries(byDate)
          .map(([date, counts]) => ({
            date,
            moods: Object.entries(counts)
              .map(([mood, count]) => ({ mood, count }))
              .sort((a, b) => b.count - a.count),
          }))
          .sort((a, b) => a.date.localeCompare(b.date))
        setMoodTrend(trend)
      })
      .catch((err) => {
        console.error('Dashboard load failed:', err)
        setError(`Could not load dashboard. Is the Insights API running at ${INSIGHTS_URL}?`)
      })
      .finally(() => setLoading(false))
  }, [token, daysRange, timeOfDay])

  if (loading) return <p className="text-sage-500">Loading...</p>
  if (error) return <p className="text-red-600">{error}</p>

  const chartDays = sentiment.slice(-Math.min(daysRange, sentiment.length))

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-lg font-semibold text-slate-800">Dashboard</h1>
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm text-slate-600">Range:</span>
          <select
            value={daysRange}
            onChange={(e) => setDaysRange(Number(e.target.value))}
            className="text-sm border border-slate-300 rounded-lg px-2 py-1.5 text-slate-700 bg-white"
          >
            {DAYS_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {d} days
              </option>
            ))}
          </select>
          <span className="text-sm text-slate-600">Time:</span>
          <select
            value={timeOfDay}
            onChange={(e) => setTimeOfDay(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-2 py-1.5 text-slate-700 bg-white"
          >
            <option value="all">All day</option>
            <option value="morning">Morning (0–11)</option>
            <option value="afternoon">Afternoon (12–17)</option>
            <option value="evening">Evening (18–23)</option>
          </select>
        </div>
      </div>

      {/* This week at a glance – week summary + emotions */}
      {(caption || emotionsCaption) && (
        <section>
          <h2 className="text-base font-medium text-slate-700 mb-3">This week at a glance</h2>
          <p className="text-sm text-slate-500 mb-2">Summary of the last 7 days (sentiment and emotions from your entries)</p>
          <div className="space-y-3">
            {caption && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Week summary</h3>
                <p className="text-slate-700 text-sm">{caption}</p>
              </div>
            )}
            {emotionsCaption && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Emotions this week</h3>
                <p className="text-slate-700 text-sm">{emotionsCaption}</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Mood trend chart (7/30/90 days) – Recharts stacked bar */}
      {moodTrend.length > 0 && (() => {
        const moodChartData = moodTrend.map(({ date, moods }) => ({
          date: formatChartDate(date),
          raw: date,
          ...Object.fromEntries(moods.map((m) => [m.mood, m.count])),
        }))
        const moodKeys = [...new Set(moodTrend.flatMap((d) => d.moods.map((m) => m.mood)))].filter(Boolean)
        return (
          <section>
            <h2 className="font-serif text-base font-medium text-sage-700 mb-3">Mood trend</h2>
            <p className="text-sm text-sage-500 mb-2">How you've been feeling (from mood tags)</p>
            <div className="bg-white border border-sage-200 rounded-card p-4 shadow-soft">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={moodChartData} margin={{ top: 8, right: 8, left: 8, bottom: 24 }}>
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    interval="preserveStartEnd"
                    angle={moodTrend.length > 21 ? -35 : 0}
                    textAnchor={moodTrend.length > 21 ? 'end' : 'middle'}
                  />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8 }}
                    formatter={(value, name) => [value, name]}
                    labelFormatter={(label, payload) => payload[0]?.payload?.raw || label}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {moodKeys.map((mood) => (
                    <Bar key={mood} dataKey={mood} stackId="mood" name={mood} fill={getMoodColor(mood)} radius={[0, 0, 0, 0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        )
      })()}

      {/* Mood & sounds – optional music and ambient suggestions */}
      {moodTrend.length > 0 && (() => {
        const suggestedMood = getSuggestedMood(moodTrend)
        if (!suggestedMood) return null
        const info = getMoodMusicAmbient(suggestedMood)
        return (
          <section className="bg-slate-50/80 border border-slate-200 rounded-lg p-4">
            <h2 className="text-base font-medium text-slate-700 mb-1">Mood & sounds</h2>
            <p className="text-xs text-slate-500 mb-3">
              Optional: music and ambient suggestions based on your recent mood. Opens YouTube search; no account needed.
            </p>
            <p className="text-sm text-slate-600 mb-2">
              For <span className="font-medium" style={{ color: getMoodColor(suggestedMood) }}>{suggestedMood}</span>:
            </p>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-slate-600">Music: </span>
                <span className="text-slate-700">{info.music}</span>
                <a
                  href={youtubeSearchUrl(info.musicQuery)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-slate-600 hover:text-slate-900 underline"
                >
                  Search on YouTube
                </a>
              </div>
              <div>
                <span className="text-slate-600">Ambient: </span>
                {info.ambient.map(({ label, query }) => (
                  <a
                    key={label}
                    href={youtubeSearchUrl(query)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mr-2 mt-1 px-2.5 py-1 bg-white border border-sage-200 rounded-lg text-sage-700 hover:bg-sage-100"
                  >
                    {label}
                  </a>
                ))}
              </div>
            </div>
          </section>
        )
      })()}

      {/* Stress / emotion chart */}
      {emotionsOverTime.length > 0 && (
        <section>
          <h2 className="font-serif text-base font-medium text-sage-700 mb-3">Stress & emotions over time</h2>
          <p className="text-sm text-sage-500 mb-2">Emotions detected in your entries by day</p>
          <div className="bg-white border border-sage-200 rounded-card p-4 shadow-soft overflow-x-auto">
            <div className="space-y-2">
              {emotionsOverTime.slice(-21).map(({ date, emotions }) => (
                <div key={date} className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-sage-500 w-14 shrink-0">{formatChartDate(date)}</span>
                  <div className="flex flex-wrap gap-1">
                    {emotions.slice(0, 5).map(({ emotion, count }) => (
                      <span
                        key={emotion}
                        className="px-2 py-0.5 rounded text-xs font-medium bg-sage-100 text-sage-700"
                        title={`${emotion}: ${count}`}
                      >
                        {emotion} {count > 1 ? `×${count}` : ''}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Sentiment over time – Recharts area chart */}
      <section>
        <h2 className="text-base font-medium text-slate-700 mb-3">Sentiment over time</h2>
        {chartDays.length === 0 ? (
          <p className="text-slate-500 text-sm">No sentiment data yet. Write a few entries to see trends.</p>
        ) : (
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart
                data={chartDays.map((d) => ({
                  ...d,
                  score: Number(d.score),
                  dateLabel: formatChartDate(d.date),
                }))}
                margin={{ top: 8, right: 8, left: 8, bottom: 24 }}
              >
                <defs>
                  <linearGradient id="sentimentGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#64748b" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#64748b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="dateLabel"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  interval="preserveStartEnd"
                  angle={chartDays.length > 21 ? -35 : 0}
                  textAnchor={chartDays.length > 21 ? 'end' : 'middle'}
                />
                <YAxis
                  domain={[-1, 1]}
                  tick={{ fontSize: 10, fill: '#64748b' }}
                  width={28}
                  tickFormatter={(v) => (v === 0 ? '0' : v > 0 ? '+' : '') + v}
                />
                <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                  formatter={(value, _, props) => [
                    `${Number(value).toFixed(2)} (${props.payload.label || 'neutral'})`,
                    'Score',
                  ]}
                  labelFormatter={(_, payload) => payload[0]?.payload?.date || _}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#475569"
                  strokeWidth={2}
                  fill="url(#sentimentGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
            <p className="text-xs text-sage-500 mt-2">
              Above zero = more positive, below = more negative. Hover for exact score and label.
            </p>
          </div>
        )}
      </section>

      {/* Top themes – horizontal bar chart */}
      {themesWithCounts.length > 0 && (
        <section>
          <h2 className="font-serif text-base font-medium text-sage-700 mb-3">Top themes & recurrence</h2>
          <p className="text-sm text-sage-500 mb-3">What you've written about most</p>
          <div className="bg-white border border-sage-200 rounded-card p-4 shadow-soft">
            <div className="space-y-3">
              {(() => {
                const maxCount = Math.max(...themesWithCounts.map(({ count }) => count), 1)
                return themesWithCounts.slice(0, 12).map(({ theme, count }) => (
                  <div key={theme} className="flex items-center gap-3">
                    <span className="text-sm font-medium text-sage-700 w-32 shrink-0 truncate" title={theme}>
                      {theme}
                    </span>
                    <div className="flex-1 min-w-0 h-6 bg-sage-100 rounded overflow-hidden flex">
                      <div
                        className="h-full bg-sage-500 rounded-l"
                        style={{ width: `${(count / maxCount) * 100}%`, minWidth: count ? 4 : 0 }}
                      />
                    </div>
                    <span className="text-sm text-sage-500 w-8 text-right">{count}</span>
                  </div>
                ))
              })()}
            </div>
          </div>
        </section>
      )}

      {/* Theme → sentiment breakdown – stacked bar chart */}
      {themeSentimentBreakdown.length > 0 && (
        <section>
          <h2 className="font-serif text-base font-medium text-sage-700 mb-3">Theme → sentiment breakdown</h2>
          <p className="text-sm text-sage-500 mb-3">How each theme tends to appear (tougher vs brighter days)</p>
          <div className="bg-white border border-sage-200 rounded-card p-4 shadow-soft space-y-4">
            {themeSentimentBreakdown.slice(0, 10).map(({ theme, low, neutral, high }) => {
              const total = low + neutral + high || 1
              const lowPct = (low / total) * 100
              const neutralPct = (neutral / total) * 100
              const highPct = (high / total) * 100
              return (
                <div key={theme}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-sage-700 truncate">{theme}</span>
                    <span className="text-xs text-sage-500 shrink-0 ml-2">{low + neutral + high} entries</span>
                  </div>
                  <div className="flex h-5 rounded overflow-hidden bg-sage-100">
                    <div
                      className="bg-red-400 shrink-0"
                      style={{ width: `${lowPct}%` }}
                      title={`Low: ${low}`}
                    />
                    <div
                      className="bg-sage-300 shrink-0"
                      style={{ width: `${neutralPct}%` }}
                      title={`Neutral: ${neutral}`}
                    />
                    <div
                      className="bg-sage-500 shrink-0"
                      style={{ width: `${highPct}%` }}
                      title={`High: ${high}`}
                    />
                  </div>
                </div>
              )
            })}
            <p className="text-xs text-sage-500 mt-2">Red = tougher days · Gray = neutral · Green = brighter days</p>
          </div>
        </section>
      )}

      {/* Themes by mood – with note on overlap */}
      {(themeSentiment.low.length > 0 || themeSentiment.high.length > 0) && (
        <section>
          <h2 className="text-base font-medium text-slate-700 mb-3">Themes by mood</h2>
          <p className="text-sm text-slate-500 mb-2">
            Topics that showed up on tougher vs brighter days. Themes can appear in both — that shows you write about them in different moods.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {themeSentiment.low.length > 0 && (
              <div className="bg-red-50/50 border border-red-100 rounded-lg p-3">
                <p className="text-xs font-medium text-red-700 mb-2">Themes on tougher days</p>
                <div className="flex flex-wrap gap-2">
                  {themeSentiment.low.map((t) => (
                    <span key={t} className="px-2.5 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {themeSentiment.high.length > 0 && (
              <div className="bg-green-50/50 border border-green-100 rounded-lg p-3">
                <p className="text-xs font-medium text-green-700 mb-2">Themes on brighter days</p>
                <div className="flex flex-wrap gap-2">
                  {themeSentiment.high.map((t) => (
                    <span key={t} className="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Patterns – insight cards */}
      {patternInsights.length > 0 && (
        <section>
          <h2 className="font-serif text-base font-medium text-sage-700 mb-3">Patterns</h2>
          <p className="text-sm text-sage-500 mb-2">Correlations from your entries over the selected period</p>
          <div className="space-y-2">
            {patternInsights.map((insight, i) => (
              <div
                key={i}
                className="flex gap-3 p-3 bg-sage-50 border border-sage-200 rounded-card shadow-soft text-sm text-sage-700"
              >
                <span className="text-sage-400 shrink-0" aria-hidden>◆</span>
                <span>{insight}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <h2 className="text-base font-medium text-slate-800 mb-2">Suggested actions</h2>
        <p className="text-sm text-slate-600 mb-2">Small, optional steps — only if they feel right</p>
        {actionableActions.length > 0 ? (
          <>
            <p className="text-xs text-slate-500 mb-3">
              Based on patterns in your entries (e.g. which topics show up on tougher vs brighter days, or which weekdays tend to feel harder). Not a judgment — just gentle suggestions you can ignore.
            </p>
            <ul className="list-disc list-inside text-sm text-slate-700 space-y-2">
              {actionableActions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ul>
          </>
        ) : (
          <p className="text-sm text-slate-600">
            Suggestions appear as patterns emerge from your entries. Write over 7–30 days (including some tougher and brighter days), and the consumer must have processed your entries. Try the <strong>30 days</strong> range; you'll see actions when there are themes that show up on low-sentiment days, or a weekday that tends to feel harder, or themes that show up on brighter days.
          </p>
        )}
      </section>
    </div>
  )
}
