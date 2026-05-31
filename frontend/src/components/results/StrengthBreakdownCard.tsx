import type { StrengthBreakdown, StrengthMetric } from '../../types'
import { BarChart3 } from 'lucide-react'

const METRICS: { key: keyof Omit<StrengthBreakdown, 'overall'>; label: string }[] = [
  { key: 'skill_match', label: 'Skill Match' },
  { key: 'experience_relevance', label: 'Experience Relevance' },
  { key: 'project_depth', label: 'Project Depth' },
  { key: 'keyword_coverage', label: 'Keyword Coverage' },
  { key: 'impact_score', label: 'Impact' },
  { key: 'structure_score', label: 'Structure' },
]

function scoreColor(score: number): string {
  return score >= 70 ? '#a3ff47' : score >= 45 ? '#47c8ff' : '#ff6b47'
}

function MetricBar({ label, metric }: { label: string; metric: StrengthMetric }) {
  const color = scoreColor(metric.score)
  return (
    <div>
      <div className="flex justify-between items-baseline mb-1.5">
        <span className="text-ink-300 text-sm">{label}</span>
        <span className="font-display font-bold text-sm" style={{ color }}>
          {metric.score}
        </span>
      </div>
      <div className="h-2.5 bg-ink-800 rounded-full overflow-hidden border border-ink-700">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${metric.score}%`,
            background: `linear-gradient(90deg, ${color}80, ${color})`,
            boxShadow: `0 0 6px ${color}50`,
          }}
        />
      </div>
      {metric.rationale && (
        <p className="text-ink-500 text-xs mt-1 leading-snug">{metric.rationale}</p>
      )}
    </div>
  )
}

export default function StrengthBreakdownCard({ data }: { data: StrengthBreakdown }) {
  // If every metric is 0, extraction likely failed — don't render a misleading card.
  const allZero =
    data.overall === 0 && METRICS.every(m => (data[m.key]?.score ?? 0) === 0)
  if (allZero) return null

  const overallColor = scoreColor(data.overall)

  return (
    <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.12s' }}>
      <div className="flex items-center justify-between mb-5">
        <h2 className="font-display font-bold text-white flex items-center gap-2">
          <BarChart3 size={16} className="text-acid" />
          Resume Strength Breakdown
        </h2>
        <div className="text-right">
          <div className="font-display font-bold text-2xl leading-none" style={{ color: overallColor }}>
            {data.overall}
          </div>
          <div className="text-ink-500 text-[10px] font-mono uppercase tracking-widest">
            Overall
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-4">
        {METRICS.map(m => (
          <MetricBar key={m.key} label={m.label} metric={data[m.key]} />
        ))}
      </div>
    </div>
  )
}
