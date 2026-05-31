import { useState, useEffect, useRef, useCallback } from 'react'
import { getLiveFeedback } from '../../services/api'
import type { LiveFeedbackResponse, LiveTip } from '../../types'
import {
  Gauge, Zap, CheckCircle2, AlertTriangle, Info,
  Sparkles, Loader2,
} from 'lucide-react'

const DEBOUNCE_MS = 500

function scoreColor(score: number): string {
  return score >= 70 ? '#a3ff47' : score >= 45 ? '#47c8ff' : '#ff6b47'
}

function MiniBar({ label, score }: { label: string; score: number }) {
  const color = scoreColor(score)
  return (
    <div>
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-ink-400 text-xs font-mono">{label}</span>
        <span className="font-display font-bold text-sm" style={{ color }}>{score}</span>
      </div>
      <div className="h-2 bg-ink-800 rounded-full overflow-hidden border border-ink-700">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${score}%`, background: `linear-gradient(90deg, ${color}80, ${color})` }}
        />
      </div>
    </div>
  )
}

const TIP_ICON: Record<LiveTip['type'], React.ReactNode> = {
  good: <CheckCircle2 size={14} className="text-acid mt-0.5 shrink-0" />,
  warning: <AlertTriangle size={14} className="text-coral mt-0.5 shrink-0" />,
  info: <Info size={14} className="text-sky-cool mt-0.5 shrink-0" />,
}

export default function LiveEditorPage() {
  const [resumeText, setResumeText] = useState('')
  const [jd, setJd] = useState('')
  const [feedback, setFeedback] = useState<LiveFeedbackResponse | null>(null)
  const [scoring, setScoring] = useState(false)
  const [error, setError] = useState('')

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const runScoring = useCallback((text: string, jobDesc: string) => {
    // Cancel any in-flight request
    if (abortRef.current) abortRef.current.abort()
    if (!text.trim()) {
      setFeedback(null)
      setScoring(false)
      return
    }
    const controller = new AbortController()
    abortRef.current = controller
    setScoring(true)
    setError('')

    getLiveFeedback({ resumeText: text, jobDescription: jobDesc }, controller.signal)
      .then(res => {
        setFeedback(res)
        setScoring(false)
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === 'AbortError') return // superseded
        setError(err instanceof Error ? err.message : 'Scoring failed.')
        setScoring(false)
      })
  }, [])

  // Debounce on any change to resume or JD
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      runScoring(resumeText, jd)
    }, DEBOUNCE_MS)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [resumeText, jd, runScoring])

  // Cleanup on unmount
  useEffect(() => () => { if (abortRef.current) abortRef.current.abort() }, [])

  const overall = feedback?.overall_score ?? 0
  const overallColor = scoreColor(overall)

  return (
    <div className="max-w-6xl mx-auto px-8 py-12">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Zap size={26} className="text-acid" />
          Live Resume Editor
        </h1>
        <p className="text-ink-400 text-sm">
          Edit your resume and watch your score update in real time. No upload needed — paste, tweak, improve.
        </p>
      </div>

      <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
        {/* Editor column */}
        <div className="space-y-5">
          <section>
            <label className="text-xs font-mono text-ink-400 uppercase tracking-widest mb-2 block">
              Resume Text
            </label>
            <textarea
              value={resumeText}
              onChange={e => setResumeText(e.target.value)}
              placeholder="Paste or type your resume here. Edit freely — your score updates as you go."
              rows={20}
              className="w-full bg-ink-800 border border-ink-700 rounded-xl px-4 py-3 text-ink-100 text-sm leading-relaxed placeholder:text-ink-600 focus:outline-none focus:border-acid/40 resize-y font-mono"
            />
          </section>

          <section>
            <label className="text-xs font-mono text-ink-400 uppercase tracking-widest mb-2 block">
              Job Description <span className="text-ink-600 normal-case">(optional — enables ATS keyword scoring)</span>
            </label>
            <textarea
              value={jd}
              onChange={e => setJd(e.target.value)}
              placeholder="Paste the target job description to score keyword match against it."
              rows={5}
              className="w-full bg-ink-800 border border-ink-700 rounded-xl px-4 py-3 text-ink-100 text-sm placeholder:text-ink-600 focus:outline-none focus:border-acid/40 resize-y"
            />
          </section>
        </div>

        {/* Live score column (sticky) */}
        <div className="lg:sticky lg:top-8 self-start space-y-4">
          {/* Overall */}
          <div className="glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display font-bold text-white flex items-center gap-2">
                <Gauge size={16} className="text-acid" />
                Live Score
              </h2>
              {scoring && <Loader2 size={15} className="text-acid animate-spin" />}
            </div>

            {feedback ? (
              <>
                <div className="text-center mb-5">
                  <div className="font-display font-bold text-5xl leading-none" style={{ color: overallColor }}>
                    {overall}
                  </div>
                  <div className="text-ink-500 text-[10px] font-mono uppercase tracking-widest mt-1">
                    Overall / 100
                  </div>
                </div>

                <div className="space-y-3">
                  {jd.trim() && <MiniBar label="ATS Match" score={Math.round(feedback.ats_score)} />}
                  <MiniBar label="Impact" score={feedback.impact_score} />
                  <MiniBar label="Structure" score={feedback.structure_score} />
                </div>

                <div className="mt-4 pt-4 border-t border-ink-800 flex justify-between text-xs font-mono text-ink-500">
                  <span>{feedback.word_count} words</span>
                  {jd.trim() && (
                    <span>
                      <span className="text-acid">{feedback.matched_keywords.length}</span> matched ·{' '}
                      <span className="text-coral">{feedback.missing_keywords.length}</span> missing
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-10 text-ink-600 text-sm">
                <Sparkles size={24} className="mx-auto mb-3 opacity-50" />
                Start typing to see your live score.
              </div>
            )}

            {error && (
              <p className="text-coral text-xs mt-3 flex items-center gap-1.5">
                <AlertTriangle size={12} /> {error}
              </p>
            )}
          </div>

          {/* Tips */}
          {feedback && feedback.tips.length > 0 && (
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xs font-mono text-ink-400 uppercase tracking-widest mb-3">
                Live Tips
              </h3>
              <ul className="space-y-2.5">
                {feedback.tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-ink-300 leading-snug">
                    {TIP_ICON[tip.type]}
                    {tip.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing keywords */}
          {feedback && jd.trim() && feedback.missing_keywords.length > 0 && (
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xs font-mono text-ink-400 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <AlertTriangle size={13} className="text-coral" />
                Add These Keywords
              </h3>
              <div className="flex flex-wrap gap-2">
                {feedback.missing_keywords.map(k => (
                  <span key={k} className="chip-missing">{k}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
