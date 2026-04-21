import { useNavigate } from 'react-router-dom'
import { ArrowRight, Zap, Target, Brain, TrendingUp } from 'lucide-react'

const FEATURES = [
  { icon: Target, label: 'ATS Score', desc: 'Keyword matching against any job description' },
  { icon: Brain, label: 'Recruiter AI', desc: 'Simulated senior recruiter evaluation' },
  { icon: Zap, label: 'Bullet Rewriter', desc: 'Transform weak points into impact statements' },
  { icon: TrendingUp, label: 'Score History', desc: 'Track your resume improvement over time' },
]

export default function LandingPage() {
  const nav = useNavigate()

  return (
    <div className="min-h-screen bg-ink-900 relative overflow-hidden">
      {/* Grid bg */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `linear-gradient(#a3ff47 1px, transparent 1px), linear-gradient(90deg, #a3ff47 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Glow blobs */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-acid/5 blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-sky-cool/5 blur-[100px]" />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <span className="font-display text-xl font-bold text-acid tracking-tight">
          Resume<span className="text-white">IQ</span>
        </span>
        <button onClick={() => nav('/auth')} className="btn-ghost text-sm py-2 px-4">
          Sign In
        </button>
      </nav>

      {/* Hero */}
      <main className="relative z-10 max-w-5xl mx-auto px-8 pt-24 pb-32 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-acid/20 bg-acid/5 text-acid text-xs font-mono mb-8 animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-acid animate-pulse" />
          AI-Powered Resume Intelligence
        </div>

        <h1
          className="font-display text-6xl md:text-7xl font-extrabold leading-none mb-6 animate-fade-up"
          style={{ animationDelay: '0.1s', opacity: 0 }}
        >
          Beat the ATS.
          <br />
          <span className="gradient-text">Impress the Recruiter.</span>
        </h1>

        <p
          className="text-ink-300 text-xl max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-up"
          style={{ animationDelay: '0.2s', opacity: 0 }}
        >
          Upload your resume, paste any job description, and get a full
          ATS compatibility score, AI-simulated recruiter feedback, and
          rewritten bullet points — in under 60 seconds.
        </p>

        <div
          className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-up"
          style={{ animationDelay: '0.3s', opacity: 0 }}
        >
          <button
            onClick={() => nav('/auth')}
            className="btn-primary flex items-center gap-2 text-base px-8 py-4 shadow-[0_0_40px_rgba(163,255,71,0.2)]"
          >
            Analyze My Resume <ArrowRight size={18} />
          </button>
          <span className="text-ink-500 text-sm font-mono">Free • No credit card</span>
        </div>

        {/* Score preview */}
        <div
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-4 text-left animate-fade-up"
          style={{ animationDelay: '0.4s', opacity: 0 }}
        >
          {FEATURES.map(({ icon: Icon, label, desc }) => (
            <div key={label} className="glass rounded-xl p-5 group hover:border-acid/20 transition-all">
              <Icon size={20} className="text-acid mb-3" />
              <p className="font-display font-semibold text-white text-sm mb-1">{label}</p>
              <p className="text-ink-400 text-xs leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* Social proof bar */}
        <div className="mt-16 flex items-center justify-center gap-8 text-ink-500 text-sm font-mono">
          <span><span className="text-acid font-bold">PDF</span> + DOCX</span>
          <span className="w-px h-4 bg-ink-700" />
          <span><span className="text-acid font-bold">Gemini</span> AI</span>
          <span className="w-px h-4 bg-ink-700" />
          <span>Supabase <span className="text-acid font-bold">Auth</span></span>
          <span className="w-px h-4 bg-ink-700" />
          <span>Real-time <span className="text-acid font-bold">ATS</span></span>
        </div>
      </main>
    </div>
  )
}
