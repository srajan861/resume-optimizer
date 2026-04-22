import type { AnalysisResult } from '../types'

export function downloadAnalysisPDF(data: AnalysisResult) {
  const { ats, recruiter, rewritten_bullets } = data

  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>ResumeIQ Analysis Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #ffffff;
      color: #1a1a1a;
      padding: 40px;
      max-width: 900px;
      margin: 0 auto;
      font-size: 13px;
      line-height: 1.6;
    }

    /* Header */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 32px;
      padding-bottom: 16px;
      border-bottom: 3px solid #a3ff47;
    }
    .logo {
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }
    .logo span { color: #3d3d7a; }
    .logo-iq { color: #1a1a1a; }
    .date {
      font-size: 11px;
      color: #666;
      text-align: right;
    }

    /* Scores */
    .scores {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    .score-card {
      border: 2px solid #e5e7eb;
      border-radius: 10px;
      padding: 16px;
      text-align: center;
    }
    .score-value {
      font-size: 36px;
      font-weight: 800;
      line-height: 1;
      margin-bottom: 4px;
    }
    .score-label {
      font-size: 11px;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .score-ats { color: #16a34a; border-color: #16a34a30; background: #f0fdf4; }
    .score-recruiter { color: #2563eb; border-color: #2563eb30; background: #eff6ff; }

    /* Progress bar */
    .progress-bar {
      height: 8px;
      background: #e5e7eb;
      border-radius: 4px;
      overflow: hidden;
      margin: 8px 0 4px;
    }
    .progress-fill {
      height: 100%;
      border-radius: 4px;
      background: linear-gradient(90deg, #16a34a80, #16a34a);
    }

    /* Sections */
    .section {
      margin-bottom: 24px;
    }
    .section-title {
      font-size: 14px;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 10px;
      padding-bottom: 6px;
      border-bottom: 1.5px solid #e5e7eb;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .section-title .icon { font-size: 16px; }

    /* Keywords */
    .keywords {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .keyword {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 500;
      font-family: monospace;
    }
    .keyword-missing {
      background: #fef2f2;
      color: #dc2626;
      border: 1px solid #fecaca;
    }
    .keyword-matched {
      background: #f0fdf4;
      color: #16a34a;
      border: 1px solid #bbf7d0;
    }

    /* Lists */
    .feedback-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    .feedback-card {
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 14px;
    }
    .feedback-card h3 {
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .strength h3 { color: #16a34a; }
    .weakness h3 { color: #dc2626; }
    .feedback-card ul { padding-left: 14px; }
    .feedback-card li { margin-bottom: 4px; font-size: 12px; color: #374151; }

    /* Suggestions */
    .suggestions ol { padding-left: 18px; }
    .suggestions li {
      margin-bottom: 6px;
      font-size: 12px;
      color: #374151;
    }

    /* Bullets */
    .bullet-card {
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 10px;
    }
    .bullet-before {
      padding: 10px 14px;
      background: #fafafa;
      border-bottom: 1px solid #e5e7eb;
    }
    .bullet-after {
      padding: 10px 14px;
      background: #f0fdf4;
    }
    .bullet-label {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 4px;
    }
    .before-label { color: #dc2626; }
    .after-label { color: #16a34a; }
    .bullet-text { font-size: 12px; color: #374151; }

    /* Footer */
    .footer {
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #e5e7eb;
      text-align: center;
      font-size: 11px;
      color: #9ca3af;
    }

    @media print {
      body { padding: 20px; }
      .section { page-break-inside: avoid; }
      .bullet-card { page-break-inside: avoid; }
    }
  </style>
</head>
<body>
  <!-- Header -->
  <div class="header">
    <div class="logo">
      <span>Resume</span><span class="logo-iq">IQ</span>
      <div style="font-size:11px;font-weight:400;color:#666;margin-top:2px;">Analysis Report</div>
    </div>
    <div class="date">
      Generated: ${new Date().toLocaleDateString('en-IN', {
        day: 'numeric', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      })}
    </div>
  </div>

  <!-- Scores -->
  <div class="scores">
    <div class="score-card score-ats">
      <div class="score-value">${ats.score.toFixed(0)}%</div>
      <div class="progress-bar">
        <div class="progress-fill" style="width:${ats.score}%"></div>
      </div>
      <div class="score-label">ATS Match Score</div>
    </div>
    <div class="score-card score-recruiter">
      <div class="score-value">${recruiter.score.toFixed(1)}<span style="font-size:18px;color:#666">/10</span></div>
      <div style="margin:8px 0 4px"></div>
      <div class="score-label">Recruiter Score</div>
    </div>
  </div>

  <!-- Missing Keywords -->
  <div class="section">
    <div class="section-title">
      <span class="icon">⚠️</span> Missing Keywords (${ats.missing_keywords.length})
    </div>
    <div class="keywords">
      ${ats.missing_keywords.map(k => `<span class="keyword keyword-missing">${k}</span>`).join('')}
    </div>
  </div>

  <!-- Matched Keywords -->
  <div class="section">
    <div class="section-title">
      <span class="icon">✅</span> Matched Keywords (${ats.matched_keywords.length})
    </div>
    <div class="keywords">
      ${ats.matched_keywords.map(k => `<span class="keyword keyword-matched">${k}</span>`).join('')}
    </div>
  </div>

  <!-- Strengths & Weaknesses -->
  <div class="feedback-grid">
    <div class="feedback-card strength">
      <h3>💪 Strengths</h3>
      <ul>
        ${recruiter.strengths.map(s => `<li>${s}</li>`).join('')}
      </ul>
    </div>
    <div class="feedback-card weakness">
      <h3>⚠️ Weaknesses</h3>
      <ul>
        ${recruiter.weaknesses.map(w => `<li>${w}</li>`).join('')}
      </ul>
    </div>
  </div>

  <!-- Suggestions -->
  <div class="section suggestions">
    <div class="section-title">
      <span class="icon">💡</span> Actionable Suggestions
    </div>
    <ol>
      ${recruiter.suggestions.map(s => `<li>${s}</li>`).join('')}
    </ol>
  </div>

  <!-- Rewritten Bullets -->
  ${rewritten_bullets.length > 0 ? `
  <div class="section">
    <div class="section-title">
      <span class="icon">✨</span> Rewritten Bullet Points
    </div>
    ${rewritten_bullets.map(b => `
      <div class="bullet-card">
        <div class="bullet-before">
          <div class="bullet-label before-label">✗ Before</div>
          <div class="bullet-text">${b.original}</div>
        </div>
        <div class="bullet-after">
          <div class="bullet-label after-label">✓ After</div>
          <div class="bullet-text">${b.improved}</div>
        </div>
      </div>
    `).join('')}
  </div>
  ` : ''}

  <!-- Footer -->
  <div class="footer">
    Generated by ResumeIQ — resume-optimizer-neon.vercel.app
  </div>

  <script>
    window.onload = () => { window.print(); }
  </script>
</body>
</html>
  `

  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const win = window.open(url, '_blank')
  if (win) {
    win.onafterprint = () => URL.revokeObjectURL(url)
  }
}