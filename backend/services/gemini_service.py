import json
import re
import asyncio
from typing import List
import httpx
from core.config import settings
from models.schemas import RecruiterFeedback, RewrittenBullet


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

ROLE_CONTEXT = {
    "sde": "Software Development Engineer (SDE) role focusing on system design, coding, and software architecture",
    "ml": "Machine Learning Engineer role focusing on ML systems, model development, and data pipelines",
    "analyst": "Data/Business Analyst role focusing on data analysis, insights, and business intelligence",
    "general": "general professional role",
}


async def _call_gemini(prompt: str, temperature: float = 0.3) -> str:
    """Make an async call to the Gemini API."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048,
            "topP": 0.8,
        },
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{GEMINI_API_URL}?key={settings.GEMINI_API_KEY}",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
    
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("No response from Gemini API")
    
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        raise ValueError("Empty response from Gemini API")
    
    return parts[0].get("text", "")


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from LLM response."""
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in text
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
) -> RecruiterFeedback:
    """Use Gemini to simulate a senior recruiter evaluating the resume."""
    role_desc = ROLE_CONTEXT.get(role_type, ROLE_CONTEXT["general"])
    
    prompt = f"""You are a senior recruiter with 10+ years of experience hiring for {role_desc}.

Evaluate the following resume against the job description provided.

## JOB DESCRIPTION:
{jd_text[:3000]}

## RESUME:
{resume_text[:3000]}

Evaluate based on:
1. Relevance to the job description
2. Impact and measurability of achievements  
3. Technical depth and skill alignment
4. Clarity, structure, and professionalism

You MUST respond with ONLY a valid JSON object. No explanation, no markdown, just raw JSON:
{{
  "score": <number between 0 and 10>,
  "strengths": [<3-5 specific strength strings>],
  "weaknesses": [<3-5 specific weakness strings>],
  "suggestions": [<4-6 concrete, actionable improvement suggestions>]
}}"""

    try:
        raw = await _call_gemini(prompt, temperature=0.2)
        data = _extract_json(raw)
        
        return RecruiterFeedback(
            score=float(data.get("score", 5.0)),
            strengths=data.get("strengths", [])[:6],
            weaknesses=data.get("weaknesses", [])[:6],
            suggestions=data.get("suggestions", [])[:6],
        )
    except Exception as e:
        # Fallback response if AI fails
        return RecruiterFeedback(
            score=5.0,
            strengths=["Resume submitted for review"],
            weaknesses=["Could not fully analyze — please try again"],
            suggestions=["Ensure your resume clearly lists measurable achievements"],
        )


async def rewrite_bullet_points(
    bullets: List[str],
    job_context: str = "",
) -> List[RewrittenBullet]:
    """Rewrite weak bullet points to be more impactful using Gemini."""
    if not bullets:
        return []
    
    # Process in batches of 5 to avoid token limits
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
        raw = await _call_gemini(prompt, temperature=0.4)
        data = _extract_json(raw)
        rewrites = data.get("rewrites", [])
        
        result = []
        for j, bullet in enumerate(bullets):
            if j < len(rewrites):
                improved = rewrites[j].get("improved", bullet)
            else:
                improved = bullet
            result.append(RewrittenBullet(original=bullet, improved=improved))
        
        return result
    except Exception:
        # Fallback: return originals unchanged
        return [RewrittenBullet(original=b, improved=b) for b in bullets]
