import json
import re
from typing import List, Optional
from groq import Groq
from core.config import settings
from models.schemas import (
    RecruiterFeedback, RewrittenBullet, JDIntelligence,
    SkillGapRoadmap, SkillGapItem,
    StrengthBreakdown, StrengthMetric,
)
ROLE_CONTEXT = {
    "sde": "Software Development Engineer (SDE) role focusing on system design, coding, and software architecture",
    "ml": "Machine Learning Engineer role focusing on ML systems, model development, and data pipelines",
    "analyst": "Data/Business Analyst role focusing on data analysis, insights, and business intelligence",
    "general": "general professional role",
}

# Each persona evaluates the SAME resume through a different hiring lens.
PERSONA_CONTEXT = {
    "standard": {
        "title": "Senior Recruiter",
        "lens": (
            "You evaluate resumes in a balanced, general-purpose way. Weigh relevance, "
            "measurable impact, technical depth, and clarity roughly equally."
        ),
        "values": "overall relevance, measurable achievements, clear structure",
        "tone": "professional and balanced",
    },
    "faang": {
        "title": "FAANG / Big Tech Technical Recruiter",
        "lens": (
            "You hire for large-scale tech companies (Google, Meta, Amazon, etc.). You care most "
            "about scale, algorithmic and system-design depth, quantified impact at scale, strong "
            "engineering fundamentals, and signals of working on high-traffic / high-complexity systems. "
            "You are demanding and score conservatively — a 7+ means truly strong."
        ),
        "values": "scale, system design, algorithmic depth, quantified impact, top-tier signals",
        "tone": "rigorous, high-bar, detail-oriented",
    },
    "startup": {
        "title": "Early-Stage Startup Recruiter / Founder",
        "lens": (
            "You hire for a fast-moving startup. You care most about ownership, versatility, "
            "shipping speed, end-to-end delivery, scrappiness, and the ability to wear many hats. "
            "You value builders who ship real products over pure pedigree. You reward initiative "
            "and breadth, and you are wary of candidates who only operated inside rigid processes."
        ),
        "values": "ownership, versatility, shipping speed, end-to-end impact, initiative",
        "tone": "energetic, pragmatic, builder-focused",
    },
    "hr": {
        "title": "HR / People & Culture Recruiter",
        "lens": (
            "You screen for culture fit, communication, professionalism, and overall presentation. "
            "You care most about clarity, soft skills, consistency, career progression, red-flag-free "
            "history, and how well the resume reads to a non-technical reviewer. You are less focused "
            "on deep technical nuance and more on coherence, readability, and human signals."
        ),
        "values": "communication, clarity, culture fit, professionalism, career progression",
        "tone": "warm, people-focused, presentation-aware",
    },
}

MODEL = "llama-3.3-70b-versatile"


def get_client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from LLM response."""
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


async def simulate_recruiter(
    resume_text: str,
    jd_text: str,
    role_type: str = "general",
    persona: str = "standard",
) -> RecruiterFeedback:
    """Use Groq to simulate a recruiter evaluating the resume through a chosen persona lens."""
    role_desc = ROLE_CONTEXT.get(role_type, ROLE_CONTEXT["general"])
    p = PERSONA_CONTEXT.get(persona, PERSONA_CONTEXT["standard"])

    prompt = f"""You are a {p['title']} with 10+ years of experience hiring for {role_desc}.

## YOUR EVALUATION LENS:
{p['lens']}
You especially value: {p['values']}.
Adopt a {p['tone']} tone in your feedback.

Evaluate the following resume against the job description STRICTLY through this lens.
Two different recruiters should reach different conclusions on the same resume — make your
persona's priorities clearly visible in the score, strengths, weaknesses, and suggestions.

## JOB DESCRIPTION:
{jd_text[:3000]}

## RESUME:
{resume_text[:3000]}

Evaluate based on:
1. Relevance to the job description
2. Impact and measurability of achievements
3. Technical depth and skill alignment
4. Clarity, structure, and professionalism
...all weighted according to YOUR persona's priorities above.

You MUST respond with ONLY a valid JSON object. No explanation, no markdown, just raw JSON:
{{
  "score": <number between 0 and 10>,
  "strengths": [<3-5 specific strength strings>],
  "weaknesses": [<3-5 specific weakness strings>],
  "suggestions": [<4-6 concrete, actionable improvement suggestions>]
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
        print(f"✅ Groq recruiter response received (persona={persona})")
        data = _extract_json(raw)

        return RecruiterFeedback(
            score=float(data.get("score", 5.0)),
            strengths=data.get("strengths", [])[:6],
            weaknesses=data.get("weaknesses", [])[:6],
            suggestions=data.get("suggestions", [])[:6],
            persona=persona,
        )
    except Exception as e:
        print(f"❌ Groq recruiter simulation failed: {type(e).__name__}: {e}")
        return RecruiterFeedback(
            score=5.0,
            strengths=["Resume submitted for review"],
            weaknesses=["Could not fully analyze — please try again"],
            suggestions=["Ensure your resume clearly lists measurable achievements"],
            persona=persona,
        )


async def rewrite_bullet_points(
    bullets: List[str],
    job_context: str = "",
) -> List[RewrittenBullet]:
    """Rewrite weak bullet points to be more impactful using Groq."""
    if not bullets:
        return []

    results: List[RewrittenBullet] = []
    batch_size = 5

    for i in range(0, len(bullets), batch_size):
        batch = bullets[i:i + batch_size]
        batch_results = await _rewrite_batch(batch, job_context)
        results.extend(batch_results)

    return results


async def _rewrite_batch(
    bullets: List[str],
    job_context: str = "",
) -> List[RewrittenBullet]:
    """Rewrite a batch of bullet points."""
    numbered = "\n".join(f"{j+1}. {b}" for j, b in enumerate(bullets))
    context_note = f"\nTarget role context: {job_context}" if job_context else ""

    prompt = f"""You are an expert resume writer and career coach.{context_note}

Rewrite each bullet point below to be more impactful. Use:
- Strong action verbs (Led, Built, Optimized, Delivered, Reduced, Increased, etc.)
- Specific numbers and measurable outcomes where possible
- Concise, results-focused language
- Active voice

Here are the bullet points to rewrite:
{numbered}

Respond ONLY with valid JSON — no markdown, no explanation:
{{
  "rewrites": [
    {{"original": "<original bullet 1>", "improved": "<improved bullet 1>"}},
    {{"original": "<original bullet 2>", "improved": "<improved bullet 2>"}}
  ]
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
        data = _extract_json(raw)
        rewrites = data.get("rewrites", [])

        result = []
        for j, bullet in enumerate(bullets):
            improved = rewrites[j].get("improved", bullet) if j < len(rewrites) else bullet
            result.append(RewrittenBullet(original=bullet, improved=improved))

        return result
    except Exception as e:
        print(f"❌ Groq rewrite failed: {type(e).__name__}: {e}")
        return [RewrittenBullet(original=b, improved=b) for b in bullets]


# ── Cover Letter ─────────────────────────────────────────────────────────────

COVER_LETTER_TONE = {
    "professional": "polished, formal, and confident — suitable for corporate and traditional roles",
    "enthusiastic": "warm, energetic, and passionate while staying professional — great for startups and mission-driven teams",
    "concise": "tight and to-the-point, no filler, every sentence earns its place — for busy hiring managers",
}


async def generate_cover_letter(
    resume_text: str,
    jd_text: str,
    tone: str = "professional",
    applicant_name: str = "",
    company_name: str = "",
    role_title: str = "",
) -> str:
    """Generate a tailored cover letter from a resume + job description using Groq."""
    tone_desc = COVER_LETTER_TONE.get(tone, COVER_LETTER_TONE["professional"])

    name_line = applicant_name.strip() or "the applicant"
    company_line = company_name.strip() or "the company"
    role_line = role_title.strip() or "the role described in the job description"

    prompt = f"""You are an expert career coach and professional cover letter writer.

Write a tailored, one-page cover letter for {name_line}, applying for {role_line} at {company_line}.

Use a {tone_desc} tone.

Ground every claim in the candidate's ACTUAL resume below — do NOT invent experience,
employers, degrees, or metrics that are not present. Pull the most relevant achievements
and skills that match the job description, and connect them explicitly to what the role needs.

## JOB DESCRIPTION:
{jd_text[:3000]}

## CANDIDATE RESUME:
{resume_text[:3000]}

Requirements for the cover letter:
- 3 to 4 short paragraphs, no more than ~320 words total
- Open with a strong hook that names the role and shows genuine fit
- Middle paragraph(s): 2-3 concrete, relevant achievements tied to the job's needs
- Close with a confident call to action
- Use "{applicant_name}" as the sign-off name if provided, otherwise end with "Sincerely," on its own line
- Do NOT use placeholders like [Your Name] or [Address]; if a detail is unknown, omit it gracefully
- Output ONLY the cover letter body text. No preamble, no markdown headers, no explanation."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1024,
        )
        letter = (response.choices[0].message.content or "").strip()
        # Strip any accidental markdown code fences
        letter = re.sub(r"^```(?:\w+)?\n?", "", letter)
        letter = re.sub(r"\n?```$", "", letter).strip()
        print(f"✅ Groq cover letter generated (tone={tone})")
        if not letter:
            raise ValueError("Empty cover letter returned")
        return letter
    except Exception as e:
        print(f"❌ Groq cover letter generation failed: {type(e).__name__}: {e}")
        raise


# ── JD Intelligence Extractor ────────────────────────────────────────────────

async def extract_jd_intelligence(jd_text: str) -> JDIntelligence:
    """Parse a job description into structured intelligence using Groq."""
    prompt = f"""You are an expert technical recruiter and job-description analyst.

Read the job description below and extract structured intelligence from it.
Only include information that is actually present or strongly implied — do not invent.

## JOB DESCRIPTION:
{jd_text[:3500]}

Respond with ONLY a valid JSON object. No markdown, no explanation, just raw JSON:
{{
  "role_summary": "<1-2 sentence summary of what this role is>",
  "required_skills": [<must-have skills/technologies, 5-12 items>],
  "nice_to_have_skills": [<preferred/bonus skills, 0-8 items>],
  "experience_level": "<e.g. 'Entry-level (0-2 yrs)', 'Mid (3-5 yrs)', 'Senior (5+ yrs)'>",
  "key_responsibilities": [<3-6 core responsibilities as short phrases>],
  "education": "<degree/education requirement if stated, else empty string>"
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
        print("✅ Groq JD intelligence extracted")
        data = _extract_json(raw)

        return JDIntelligence(
            role_summary=str(data.get("role_summary", "")).strip(),
            required_skills=[str(s).strip() for s in data.get("required_skills", [])][:12],
            nice_to_have_skills=[str(s).strip() for s in data.get("nice_to_have_skills", [])][:8],
            experience_level=str(data.get("experience_level", "")).strip(),
            key_responsibilities=[str(s).strip() for s in data.get("key_responsibilities", [])][:6],
            education=str(data.get("education", "")).strip(),
        )
    except Exception as e:
        print(f"❌ Groq JD intelligence extraction failed: {type(e).__name__}: {e}")
        return JDIntelligence(
            role_summary="",
            required_skills=[],
            nice_to_have_skills=[],
            experience_level="",
            key_responsibilities=[],
            education="",
        )


# ── Skill Gap Roadmap ────────────────────────────────────────────────────────

async def generate_skill_gap_roadmap(
    resume_text: str,
    jd_text: str,
    required_skills: Optional[List[str]] = None,
    nice_to_have_skills: Optional[List[str]] = None,
) -> SkillGapRoadmap:
    """Compare a resume against a job's requirements and build a learning roadmap."""
    req_skills = required_skills or []
    nice_skills = nice_to_have_skills or []

    skills_hint = ""
    if req_skills or nice_skills:
        skills_hint = (
            f"\nThe job's REQUIRED skills are: {', '.join(req_skills) or 'n/a'}.\n"
            f"The NICE-TO-HAVE skills are: {', '.join(nice_skills) or 'n/a'}.\n"
            "Use these as the primary checklist when finding gaps."
        )

    prompt = f"""You are a senior career coach and technical mentor.

Compare the candidate's resume against the target job and produce a concrete skill-gap roadmap.

CRITICAL: Only include skills in "missing_skills" that are NOT already present in the candidate's resume.
If a skill is already demonstrated in the resume, add it to "matched_skills" instead.

For each TRULY MISSING skill, give a realistic, ordered learning path (concrete steps/resources types,
not brand names), a priority, a one-line reason it matters for THIS role, and a rough time estimate.
{skills_hint}

## JOB DESCRIPTION:
{jd_text[:2500]}

## CANDIDATE RESUME:
{resume_text[:2500]}

IMPORTANT: Carefully check the resume before listing a skill as "missing". If the candidate mentions the skill,
technology, or related experience, DO NOT include it in missing_skills - add it to matched_skills instead.

Respond with ONLY a valid JSON object. No markdown, no explanation, just raw JSON:
{{
  "summary": "<2-3 sentence honest assessment of how ready the candidate is for this role>",
  "readiness_score": <integer 0-100 representing how well-prepared the candidate currently is>,
  "matched_skills": [<skills from the JD the candidate ALREADY CLEARLY HAS based on their resume>],
  "missing_skills": [
    {{
      "skill": "<skill name that is NOT in the resume>",
      "priority": "<high|medium|low>",
      "reason": "<why this matters for this specific role, one sentence>",
      "learning_path": [<3-4 ordered, concrete steps to learn it>],
      "estimated_time": "<e.g. '2-3 weeks', '1 month'>"
    }}
  ]
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1600,
        )
        raw = response.choices[0].message.content or ""
        print("✅ Groq skill gap roadmap generated")
        data = _extract_json(raw)

        missing_items: List[SkillGapItem] = []
        for item in data.get("missing_skills", [])[:10]:
            if not isinstance(item, dict):
                continue
            priority = str(item.get("priority", "medium")).lower().strip()
            if priority not in ("high", "medium", "low"):
                priority = "medium"
            missing_items.append(SkillGapItem(
                skill=str(item.get("skill", "")).strip(),
                priority=priority,
                reason=str(item.get("reason", "")).strip(),
                learning_path=[str(s).strip() for s in item.get("learning_path", [])][:5],
                estimated_time=str(item.get("estimated_time", "")).strip(),
            ))

        try:
            readiness = int(round(float(data.get("readiness_score", 0))))
        except (TypeError, ValueError):
            readiness = 0
        readiness = max(0, min(100, readiness))

        return SkillGapRoadmap(
            summary=str(data.get("summary", "")).strip(),
            readiness_score=readiness,
            matched_skills=[str(s).strip() for s in data.get("matched_skills", [])][:20],
            missing_skills=missing_items,
        )
    except Exception as e:
        print(f"❌ Groq skill gap roadmap failed: {type(e).__name__}: {e}")
        raise


# ── Resume Strength Breakdown ────────────────────────────────────────────────

_STRENGTH_DIMENSIONS = [
    "skill_match",
    "experience_relevance",
    "project_depth",
    "keyword_coverage",
    "impact_score",
    "structure_score",
]


def _clamp_score(value, default: int = 0) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, n))


async def analyze_strength_breakdown(
    resume_text: str,
    jd_text: str,
) -> StrengthBreakdown:
    """Score the resume across multiple dimensions using Groq."""
    prompt = f"""You are an expert resume evaluator and hiring analyst.

Score the resume against the job description across SIX independent dimensions.
Each dimension is scored 0-100. Be discerning — use the full range, do not cluster scores.

Dimensions:
1. skill_match — how well the candidate's skills align with the job's required skills
2. experience_relevance — how relevant their work experience is to this specific role
3. project_depth — depth, complexity, and substance of projects/work shown
4. keyword_coverage — coverage of important terms/technologies from the job description
5. impact_score — presence of quantified, measurable outcomes (numbers, %, scale)
6. structure_score — clarity, organization, formatting, and readability of the resume

## JOB DESCRIPTION:
{jd_text[:2800]}

## RESUME:
{resume_text[:2800]}

Respond with ONLY a valid JSON object. No markdown, no explanation, just raw JSON:
{{
  "skill_match": {{"score": <0-100>, "rationale": "<one short sentence>"}},
  "experience_relevance": {{"score": <0-100>, "rationale": "<one short sentence>"}},
  "project_depth": {{"score": <0-100>, "rationale": "<one short sentence>"}},
  "keyword_coverage": {{"score": <0-100>, "rationale": "<one short sentence>"}},
  "impact_score": {{"score": <0-100>, "rationale": "<one short sentence>"}},
  "structure_score": {{"score": <0-100>, "rationale": "<one short sentence>"}}
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
        print("✅ Groq strength breakdown generated")
        data = _extract_json(raw)

        metrics = {}
        for dim in _STRENGTH_DIMENSIONS:
            entry = data.get(dim, {})
            if not isinstance(entry, dict):
                entry = {}
            metrics[dim] = StrengthMetric(
                score=_clamp_score(entry.get("score", 0)),
                rationale=str(entry.get("rationale", "")).strip(),
            )

        overall = round(sum(m.score for m in metrics.values()) / len(metrics))

        return StrengthBreakdown(overall=overall, **metrics)
    except Exception as e:
        print(f"❌ Groq strength breakdown failed: {type(e).__name__}: {e}")
        return StrengthBreakdown()


# ── AI Resume Auto-Editor ────────────────────────────────────────────────────

async def generate_auto_edit_suggestions(
    resume_text: str,
    jd_text: str,
    ats_result: "ATSResult",
    recruiter_feedback: "RecruiterFeedback",
    max_suggestions: int = 10,
) -> tuple[List["EditSuggestion"], str]:
    """Generate AI-powered edit suggestions to improve the resume."""
    from models.schemas import EditSuggestion
    
    # Build context from existing analysis
    missing_kw = ", ".join(ats_result.missing_keywords[:15]) if ats_result.missing_keywords else "none"
    weaknesses = "\n".join(f"- {w}" for w in recruiter_feedback.weaknesses[:5])
    suggestions_context = "\n".join(f"- {s}" for s in recruiter_feedback.suggestions[:5])
    
    prompt = f"""You are an expert resume optimization consultant and ATS specialist.

Analyze the resume and generate SPECIFIC, ACTIONABLE edit suggestions to improve it for this job.
Focus on high-impact changes that will boost ATS scores and recruiter appeal.

## CURRENT ANALYSIS:
- ATS Score: {ats_result.score:.0f}%
- Recruiter Score: {recruiter_feedback.score:.1f}/10
- Missing Keywords: {missing_kw}

## WEAKNESSES IDENTIFIED:
{weaknesses}

## IMPROVEMENT SUGGESTIONS:
{suggestions_context}

## JOB DESCRIPTION:
{jd_text[:2500]}

## CURRENT RESUME:
{resume_text[:3000]}

Generate up to {max_suggestions} concrete edit suggestions. Each suggestion should:
- Target a specific section (experience, skills, education, projects, summary)
- Specify the type of edit (add, replace, remove, reword)
- Include the original text (if replacing/removing) and suggested new text
- Explain WHY this change improves the resume
- Indicate priority (high/medium/low) and expected impact

Focus on:
1. Adding missing keywords naturally
2. Replacing weak bullet points with strong, quantified ones
3. Improving action verbs and measurable outcomes
4. Fixing structure/formatting issues
5. Removing fluff or buzzwords

Respond with ONLY a valid JSON object. No markdown, no explanation:
{{
  "summary": "<2-3 sentence overall assessment of what needs improvement>",
  "suggestions": [
    {{
      "section": "<experience|skills|education|projects|summary>",
      "type": "<add|replace|remove|reword>",
      "original_text": "<exact text from resume if replacing/removing, empty if adding>",
      "suggested_text": "<the new/improved text>",
      "reason": "<why this change improves the resume, one sentence>",
      "priority": "<high|medium|low>",
      "impact": "<expected impact, e.g., '+5% ATS', 'stronger action verb', 'adds missing keyword'>"
    }}
  ]
}}"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content or ""
        print("✅ Groq auto-edit suggestions generated")
        data = _extract_json(raw)

        summary = str(data.get("summary", "")).strip()
        suggestions_data = data.get("suggestions", [])[:max_suggestions]
        
        suggestions: List[EditSuggestion] = []
        for item in suggestions_data:
            if not isinstance(item, dict):
                continue
            
            # Validate type and priority
            edit_type = str(item.get("type", "replace")).lower().strip()
            if edit_type not in ("add", "replace", "remove", "reword"):
                edit_type = "replace"
            
            priority = str(item.get("priority", "medium")).lower().strip()
            if priority not in ("high", "medium", "low"):
                priority = "medium"
            
            suggestions.append(EditSuggestion(
                section=str(item.get("section", "experience")).strip(),
                type=edit_type,
                original_text=str(item.get("original_text", "")).strip(),
                suggested_text=str(item.get("suggested_text", "")).strip(),
                reason=str(item.get("reason", "")).strip(),
                priority=priority,
                impact=str(item.get("impact", "")).strip(),
            ))

        return suggestions, summary
    except Exception as e:
        print(f"❌ Groq auto-edit suggestions failed: {type(e).__name__}: {e}")
        # Return safe fallback
        return [], "Unable to generate suggestions at this time. Please try again."
