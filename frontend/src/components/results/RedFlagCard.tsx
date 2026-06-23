import { useState, useEffect } from 'react'
import { AlertTriangle, AlertCircle, Info, CheckCircle, Loader2 } from 'lucide-react'
import { detectRedFlags } from '../../services/api'
import type { RedFlag, RedFlagReport } from '../../types'

interface Props {
  resumeText: string
}

export default function RedFlagCard({ resumeText }: Props) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<RedFlagReport | null>(null)

  useEffect(() => {
    let aborted = false
    const controller = new AbortController()

    async function fetchRedFlags() {
      if (!resumeText || resumeText.length < 50) {
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const res = await detectRedFlags(resumeText, controller.signal)
        if (!aborted) {
          setReport(res.report)
        }
      } catch (err: any) {
        if (!aborted && err.name !== 'AbortError') {
          setError(err.message || 'Failed to detect red flags')
        }
      } finally {
        if (!aborted) setLoading(false)
      }
    }

    fetchRedFlags()

    return () => {
      aborted = true
      controller.abort()
    }
  }, [resumeText])

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-coral" />
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-400" />
      case 'info':
        return <Info className="w-4 h-4 text-sky-cool" />
      default:
        return null
    }
  }

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      buzzword: 'Buzzword Overuse',
      metrics: 'Missing Metrics',
      gap: 'Employment Gap',
      weak_verbs: 'Weak Phrasing',
      tech_overload: 'Tech Overload',
      length: 'Length Issue',
      structure: 'Structure Issue',
    }
    return labels[category] || category
  }

  if (loading) {
    return (
      <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.14s' }}>
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={16} className="text-coral" />
          <h2 className="font-display font-bold text-white">Red Flag Detector</h2>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-acid" />
          <span className="ml-3 text-ink-400 text-sm font-mono">Scanning for red flags...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.14s' }}>
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={16} className="text-coral" />
          <h2 className="font-display font-bold text-white">Red Flag Detector</h2>
        </div>
        <div className="bg-coral/10 border border-coral/30 rounded-lg p-4">
          <p className="text-coral text-sm font-mono">{error}</p>
        </div>
      </div>
    )
  }

  if (!report) {
    return null
  }

  const { flags, total_count, severity_breakdown } = report

  return (
    <div className="glass rounded-2xl p-6 mb-6 animate-fade-up" style={{ animationDelay: '0.14s' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="font-display font-bold text-white flex items-center gap-2">
          <AlertTriangle size={16} className="text-coral" />
          Red Flag Detector
        </h2>
        <div className="text-right">
          <div className="font-display font-bold text-2xl leading-none text-coral">
            {total_count}
          </div>
          <div className="text-ink-500 text-[10px] font-mono uppercase tracking-widest">
            Total Flags
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="bg-ink-800/40 rounded-lg px-3 py-2.5 border border-ink-700">
          <div className="text-[10px] text-coral font-mono uppercase tracking-widest mb-0.5">Critical</div>
          <div className="text-xl font-display font-bold text-coral">{severity_breakdown.critical}</div>
        </div>
        <div className="bg-ink-800/40 rounded-lg px-3 py-2.5 border border-ink-700">
          <div className="text-[10px] text-yellow-400 font-mono uppercase tracking-widest mb-0.5">Warnings</div>
          <div className="text-xl font-display font-bold text-yellow-400">{severity_breakdown.warning}</div>
        </div>
        <div className="bg-ink-800/40 rounded-lg px-3 py-2.5 border border-ink-700">
          <div className="text-[10px] text-sky-cool font-mono uppercase tracking-widest mb-0.5">Info</div>
          <div className="text-xl font-display font-bold text-sky-cool">{severity_breakdown.info}</div>
        </div>
      </div>

      {/* Flags List or Success State */}
      {flags.length === 0 ? (
        <div className="bg-acid/10 border border-acid/30 rounded-lg p-5 flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-acid flex-shrink-0" />
          <div>
            <h3 className="font-display font-bold text-acid mb-0.5">No Red Flags Detected! 🎉</h3>
            <p className="text-ink-400 text-sm">
              Your resume looks clean and professional. Recruiters will appreciate the quality.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {flags.map((flag, idx) => (
            <div
              key={idx}
              className="border border-ink-700 rounded-lg p-4 bg-ink-800/20"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">{getSeverityIcon(flag.severity)}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase tracking-widest ${
                      flag.severity === 'critical'
                        ? 'bg-coral/20 text-coral border border-coral/30'
                        : flag.severity === 'warning'
                        ? 'bg-yellow-400/20 text-yellow-400 border border-yellow-400/30'
                        : 'bg-sky-cool/20 text-sky-cool border border-sky-cool/30'
                    }`}>
                      {flag.severity}
                    </span>
                    <span className="text-[10px] font-mono text-ink-500 uppercase tracking-widest">
                      {getCategoryLabel(flag.category)}
                    </span>
                  </div>
                  <p className="text-white text-sm mb-1 leading-relaxed">{flag.message}</p>
                  {flag.details && (
                    <p className="text-ink-400 text-xs leading-relaxed">{flag.details}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer Note */}
      <div className="mt-5 pt-5 border-t border-ink-700">
        <p className="text-xs text-ink-500 font-mono">
          💡 <strong className="text-ink-400">Pro Tip:</strong> Fix critical issues first, then address warnings. Red flags are common recruiter dealbreakers.
        </p>
      </div>
    </div>
  )
}
