import { useState, useEffect } from 'react'
import { TrendingUp, Calendar, Award, Loader2 } from 'lucide-react'
import { getResumeEvolution } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import type { EvolutionTimeline, VersionSnapshot } from '../../types'

interface Props {
  resumeId: string
}

export default function EvolutionCard({ resumeId }: Props) {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<EvolutionTimeline | null>(null)

  useEffect(() => {
    if (!resumeId || !user) {
      setLoading(false)
      return
    }

    async function fetchEvolution() {
      setLoading(true)
      setError(null)

      try {
        const res = await getResumeEvolution(resumeId)
        setTimeline(res.timeline)
      } catch (err: any) {
        setError(err.message || 'Failed to load evolution data')
      } finally {
        setLoading(false)
      }
    }

    fetchEvolution()
  }, [resumeId, user])

  if (loading) {
    return (
      <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.3s' }}>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={16} className="text-acid" />
          <h2 className="font-display font-bold text-white">Resume Evolution</h2>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-acid" />
          <span className="ml-3 text-ink-400 text-sm font-mono">Loading version history...</span>
        </div>
      </div>
    )
  }

  if (error || !timeline) {
    return (
      <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.3s' }}>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={16} className="text-acid" />
          <h2 className="font-display font-bold text-white">Resume Evolution</h2>
        </div>
        <div className="bg-ink-800/40 border border-ink-700 rounded-lg p-4">
          <p className="text-ink-400 text-sm font-mono">
            {error || 'No version history available for this resume.'}
          </p>
        </div>
      </div>
    )
  }

  // Only show if there are 2+ versions
  if (timeline.total_versions < 2) {
    return null
  }

  const improvementColor = timeline.improvement >= 0 ? 'text-acid' : 'text-coral'
  const improvementIcon = timeline.improvement >= 0 ? '↗' : '↘'

  // Calculate chart dimensions
  const chartWidth = 800
  const chartHeight = 200
  const padding = { top: 20, right: 20, bottom: 40, left: 50 }
  const plotWidth = chartWidth - padding.left - padding.right
  const plotHeight = chartHeight - padding.top - padding.bottom

  // Scale data points
  const maxScore = Math.max(...timeline.versions.map(v => v.ats_score), 100)
  const minScore = Math.min(...timeline.versions.map(v => v.ats_score), 0)
  const scoreRange = maxScore - minScore || 1

  const points = timeline.versions.map((v, idx) => {
    const x = padding.left + (idx / (timeline.versions.length - 1 || 1)) * plotWidth
    const y = padding.top + plotHeight - ((v.ats_score - minScore) / scoreRange) * plotHeight
    return { x, y, version: v }
  })

  // Create path for line
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ')

  return (
    <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.3s' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="font-display font-bold text-white flex items-center gap-2">
          <TrendingUp size={16} className="text-acid" />
          Resume Evolution
        </h2>
        <div className="text-right">
          <div className={`font-display font-bold text-2xl leading-none ${improvementColor}`}>
            {improvementIcon} {Math.abs(timeline.improvement).toFixed(1)}%
          </div>
          <div className="text-ink-500 text-[10px] font-mono uppercase tracking-widest">
            Improvement
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-ink-800/40 rounded-lg px-3 py-2.5 border border-ink-700">
          <div className="text-[10px] text-ink-500 font-mono uppercase tracking-widest mb-0.5">Versions</div>
          <div className="text-xl font-display font-bold text-white">{timeline.total_versions}</div>
        </div>
        <div className="bg-ink-800/40 rounded-lg px-3 py-2.5 border border-ink-700">
          <div className="text-[10px] text-ink-500 font-mono uppercase tracking-widest mb-0.5">First Score</div>
          <div className="text-xl font-display font-bold text-ink-400">{timeline.first_score.toFixed(0)}%</div>
        </div>
        <div className="bg-ink-800/40 rounded-lg px-3 py-2.5 border border-ink-700">
          <div className="text-[10px] text-ink-500 font-mono uppercase tracking-widest mb-0.5">Latest Score</div>
          <div className="text-xl font-display font-bold text-acid">{timeline.latest_score.toFixed(0)}%</div>
        </div>
      </div>

      {/* Line Chart */}
      <div className="bg-ink-900/50 rounded-lg p-4 border border-ink-700 overflow-x-auto">
        <svg
          width={chartWidth}
          height={chartHeight}
          className="w-full"
          style={{ minWidth: '600px' }}
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map(score => {
            const y = padding.top + plotHeight - ((score - minScore) / scoreRange) * plotHeight
            return (
              <g key={score}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="#2a2f3a"
                  strokeWidth="1"
                  strokeDasharray="4 2"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill="#6b7280"
                  fontSize="11"
                  fontFamily="monospace"
                >
                  {score}
                </text>
              </g>
            )
          })}

          {/* Line */}
          <path
            d={pathD}
            fill="none"
            stroke="#a3ff47"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Points */}
          {points.map((p, idx) => (
            <g key={idx}>
              <circle
                cx={p.x}
                cy={p.y}
                r="6"
                fill="#a3ff47"
                stroke="#0a0e14"
                strokeWidth="2"
              />
              <text
                x={p.x}
                y={chartHeight - 10}
                textAnchor="middle"
                fill="#9ca3af"
                fontSize="10"
                fontFamily="monospace"
              >
                V{p.version.version_number}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Version Timeline */}
      <div className="mt-5 space-y-2">
        {timeline.versions.slice().reverse().map((version) => (
          <div
            key={version.analysis_id}
            className="flex items-center justify-between p-3 bg-ink-800/20 rounded-lg border border-ink-700 hover:border-ink-600 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-acid/20 border border-acid/30">
                <span className="text-acid font-mono font-bold text-xs">V{version.version_number}</span>
              </div>
              <div>
                <div className="text-white text-sm font-medium">
                  Version {version.version_number}
                </div>
                <div className="text-ink-500 text-xs font-mono flex items-center gap-2">
                  <Calendar size={10} />
                  {new Date(version.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-white text-sm font-display font-bold">
                  {version.ats_score.toFixed(0)}%
                </div>
                <div className="text-ink-500 text-[10px] font-mono uppercase">ATS</div>
              </div>
              <div className="text-right">
                <div className="text-sky-cool text-sm font-display font-bold">
                  {version.recruiter_score.toFixed(1)}/10
                </div>
                <div className="text-ink-500 text-[10px] font-mono uppercase">Recruiter</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-5 pt-5 border-t border-ink-700">
        <p className="text-xs text-ink-500 font-mono">
          📈 <strong className="text-ink-400">Track Progress:</strong> Each analysis creates a new version, allowing you to visualize improvements over time.
        </p>
      </div>
    </div>
  )
}
