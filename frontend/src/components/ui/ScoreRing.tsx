interface ScoreRingProps {
  score: number
  max: number
  label: string
  color?: string
  size?: number
}

export default function ScoreRing({
  score,
  max,
  label,
  color = '#a3ff47',
  size = 120,
}: ScoreRingProps) {
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(score / max, 1)
  const offset = circumference * (1 - progress)
  const pct = Math.round((score / max) * 100)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={8}
          />
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="score-ring"
            style={{ filter: `drop-shadow(0 0 6px ${color}60)` }}
          />
        </svg>
        {/* Value */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display font-extrabold text-white" style={{ fontSize: size * 0.22 }}>
            {score.toFixed(max === 10 ? 1 : 0)}
          </span>
          <span className="text-ink-500 font-mono" style={{ fontSize: size * 0.1 }}>
            /{max}
          </span>
        </div>
      </div>
      <span className="text-ink-400 text-xs font-mono uppercase tracking-widest">{label}</span>
    </div>
  )
}
