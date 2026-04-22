import { useState, useMemo } from 'react'
import { FileText, Eye, EyeOff } from 'lucide-react'

interface ResumePreviewProps {
  resumeText: string
  matchedKeywords: string[]
  missingKeywords: string[]
}

export default function ResumePreview({
  resumeText,
  matchedKeywords,
  missingKeywords,
}: ResumePreviewProps) {
  const [visible, setVisible] = useState(false)

  const highlighted = useMemo(() => {
    if (!resumeText) return ''

    let text = resumeText

    // Sort by length descending to match longer phrases first
    const allKeywords = [
      ...missingKeywords.map(k => ({ word: k, type: 'missing' })),
      ...matchedKeywords.map(k => ({ word: k, type: 'matched' })),
    ].sort((a, b) => b.word.length - a.word.length)

    // Escape special regex characters
    const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

    // Replace each keyword with a marked span placeholder
    const replacements: { placeholder: string; html: string }[] = []

    allKeywords.forEach(({ word, type }, i) => {
      const placeholder = `__KW_${i}__`
      const regex = new RegExp(`\\b(${escape(word)})\\b`, 'gi')
      const color =
        type === 'matched'
          ? 'background:#a3ff4720;color:#a3ff47;border-radius:3px;padding:0 2px;border-bottom:1.5px solid #a3ff47;'
          : 'background:#ff6b4720;color:#ff6b47;border-radius:3px;padding:0 2px;border-bottom:1.5px solid #ff6b47;'
      const html = `<mark style="${color}" title="${type === 'matched' ? '✓ Matched' : '✗ Missing'} keyword">$1</mark>`

      if (regex.test(text)) {
        text = text.replace(regex, placeholder)
        replacements.push({ placeholder, html })
      }
    })

    // Now replace placeholders with actual HTML
    replacements.forEach(({ placeholder, html }) => {
      text = text.split(placeholder).join(html)
    })

    // Convert newlines to <br> for display
    text = text.replace(/\n/g, '<br/>')

    return text
  }, [resumeText, matchedKeywords, missingKeywords])

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setVisible(!visible)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-ink-800/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          <FileText size={16} className="text-acid" />
          <span className="font-display font-bold text-white">
            Resume Preview
          </span>
          <span className="text-xs font-mono text-ink-500">
            with keyword highlights
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* Legend */}
          <div className="hidden sm:flex items-center gap-3 text-xs font-mono">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-acid" />
              <span className="text-ink-400">Matched</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-coral" />
              <span className="text-ink-400">Missing</span>
            </span>
          </div>
          {visible ? (
            <EyeOff size={15} className="text-ink-500" />
          ) : (
            <Eye size={15} className="text-ink-500" />
          )}
        </div>
      </button>

      {/* Content */}
      {visible && (
        <div className="border-t border-ink-700 px-6 py-5">
          {/* Mobile legend */}
          <div className="flex sm:hidden items-center gap-4 text-xs font-mono mb-4">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-acid" />
              <span className="text-ink-400">Matched keyword</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-coral" />
              <span className="text-ink-400">Missing keyword</span>
            </span>
          </div>

          <div
            className="text-ink-300 text-sm leading-relaxed font-mono whitespace-pre-wrap max-h-[500px] overflow-y-auto pr-2"
            dangerouslySetInnerHTML={{ __html: highlighted }}
          />
        </div>
      )}
    </div>
  )
}