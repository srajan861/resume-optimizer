import re
from typing import Set, List, Tuple, Dict
from datetime import datetime
from collections import Counter
from models.schemas import ATSResult, LiveFeedbackResponse, LiveTip, RedFlag, RedFlagReport

# Common English stopwords to filter out
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare", "ought",
    "used", "able", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "it", "what", "which", "who", "whom", "how", "when", "where",
    "why", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "not", "only", "same", "so", "than", "too", "very",
    "just", "our", "your", "their", "its", "as", "if", "about", "through",
    "during", "before", "after", "above", "below", "between", "into", "out",
    "up", "down", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "work", "working", "strong", "good", "well", "new",
    "able", "also", "back", "even", "give", "look", "make", "most", "much",
    "now", "still", "take", "think", "use", "want", "way", "years",
}


def tokenize(text: str) -> List[str]:
    """Normalize and tokenize text into meaningful terms."""
    text = text.lower()
    # Keep alphanumeric and spaces, remove punctuation except hyphens
    text = re.sub(r"[^\w\s\-\+#\.]", " ", text)
    tokens = text.split()
    tokens = [t.strip(".-") for t in tokens if t.strip(".-")]
    return tokens


def extract_keywords(text: str, min_len: int = 2) -> Set[str]:
    """Extract meaningful keywords from text, removing stopwords."""
    tokens = tokenize(text)
    keywords = set()
    
    # Single tokens
    for t in tokens:
        if len(t) >= min_len and t not in STOPWORDS and not t.isdigit():
            keywords.add(t)
    
    # Bigrams for tech terms
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i+1]}"
        if tokens[i] not in STOPWORDS and tokens[i+1] not in STOPWORDS:
            keywords.add(bigram)
    
    return keywords


def compute_ats_score(resume_text: str, jd_text: str) -> ATSResult:
    """
    Compute ATS compatibility score with improved matching logic.
    
    Enhanced to:
    - Better partial word matching
    - Case-insensitive matching
    - Prioritize meaningful technical terms
    - More generous scoring for good matches
    """
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)
    
    if not jd_keywords:
        return ATSResult(
            score=0.0,
            matched_keywords=[],
            missing_keywords=[],
            total_jd_keywords=0,
            keyword_density=0.0,
        )
    
    # Improved matching with multiple strategies
    matched = set()
    missing = set()
    
    resume_text_lower = resume_text.lower()
    resume_words = set(tokenize(resume_text))
    
    for jd_kw in jd_keywords:
        found = False
        
        # Strategy 1: Exact match in extracted keywords
        if jd_kw in resume_keywords:
            matched.add(jd_kw)
            found = True
        
        # Strategy 2: Substring match in resume text
        elif jd_kw in resume_text_lower:
            matched.add(jd_kw)
            found = True
        
        # Strategy 3: Any word from JD keyword exists in resume
        elif any(word in resume_words for word in jd_kw.split()):
            matched.add(jd_kw)
            found = True
        
        # Strategy 4: Resume contains similar form (stem matching)
        elif any(jd_kw[:max(4, len(jd_kw)-2)] in resume_kw for resume_kw in resume_keywords):
            matched.add(jd_kw)
            found = True
        
        if not found:
            missing.add(jd_kw)
    
    # Filter to meaningful keywords only (length > 2, not pure numbers)
    meaningful_missing = sorted([
        k for k in missing
        if len(k) > 2 and not k.replace(" ", "").replace("-", "").replace("+", "").replace("#", "").replace(".", "").isdigit()
    ])[:30]
    
    meaningful_matched = sorted([
        k for k in matched
        if len(k) > 2
    ])[:30]
    
    # Calculate score with improved logic
    total = len([k for k in jd_keywords if len(k) > 2])
    match_count = len([k for k in matched if len(k) > 2])
    
    if total == 0:
        return ATSResult(
            score=0.0,
            matched_keywords=[],
            missing_keywords=[],
            total_jd_keywords=0,
            keyword_density=0.0,
        )
    
    # More realistic scoring: 60%+ match is good
    raw_score = (match_count / total * 100)
    
    # Apply intelligent boosting
    if match_count >= total * 0.6:  # If 60%+ keywords matched
        raw_score = min(raw_score * 1.2, 100)  # 20% boost for strong matches
    elif match_count >= total * 0.4:  # If 40-60% matched
        raw_score = min(raw_score * 1.1, 100)  # 10% boost
    
    score = min(round(raw_score, 1), 100.0)
    
    # Keyword density
    resume_tokens = tokenize(resume_text)
    resume_len = max(len(resume_tokens), 1)
    density = round((match_count / resume_len) * 100, 2)
    
    return ATSResult(
        score=score,
        matched_keywords=meaningful_matched,
        missing_keywords=meaningful_missing,
        total_jd_keywords=total,
        keyword_density=density,
    )


# ── Live Feedback Engine (no LLM — instant) ──────────────────────────────────

ACTION_VERBS = {
    "led", "built", "designed", "developed", "created", "launched", "delivered",
    "optimized", "improved", "increased", "reduced", "decreased", "automated",
    "implemented", "architected", "engineered", "drove", "scaled", "shipped",
    "managed", "owned", "spearheaded", "established", "streamlined", "accelerated",
    "boosted", "generated", "achieved", "executed", "transformed", "migrated",
    "deployed", "integrated", "refactored", "mentored", "coordinated", "analyzed",
    "negotiated", "secured", "grew", "cut", "saved", "won", "founded", "initiated",
}

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "duties included",
    "tasked with", "assisted in", "involved in", "participated in",
]

_NUMBER_RE = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b", re.IGNORECASE)
_PERCENT_METRIC_RE = re.compile(r"(\d+\s?%|\$\s?\d+|\d+[kKmMbB]\b|\d+x\b|\d{2,})")
_BULLET_RE = re.compile(r"^[\s]*(?:[•\-\*\u2022\u2023\u25E6]|\d+[.)]) (.+)$", re.MULTILINE)


def _split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _compute_impact_score(text: str) -> Tuple[int, List[LiveTip]]:
    """Score based on quantified achievements + action verbs. Returns (score, tips)."""
    tips: List[LiveTip] = []
    lines = _split_lines(text)
    bullets = [m.group(1).strip() for m in _BULLET_RE.finditer(text)]
    # Treat substantial lines as bullets too if no markers present
    candidates = bullets if bullets else [ln for ln in lines if len(ln) > 25]

    if not candidates:
        return 0, [LiveTip(type="info", message="Add bullet points describing your achievements.")]

    quantified = sum(1 for b in candidates if _PERCENT_METRIC_RE.search(b))
    starts_with_verb = 0
    weak_count = 0
    for b in candidates:
        first = b.split()[0].lower().strip(".,:;") if b.split() else ""
        if first in ACTION_VERBS:
            starts_with_verb += 1
        low = b.lower()
        if any(wp in low for wp in WEAK_PHRASES):
            weak_count += 1

    total = len(candidates)
    quant_ratio = quantified / total
    verb_ratio = starts_with_verb / total

    score = round((quant_ratio * 60) + (verb_ratio * 40))
    score = max(0, min(100, score))

    if quant_ratio < 0.3:
        tips.append(LiveTip(
            type="warning",
            message=f"Only {quantified}/{total} bullets have numbers. Add metrics (%, $, scale) to show impact.",
        ))
    else:
        tips.append(LiveTip(type="good", message=f"{quantified} bullets are quantified — strong impact signal."))

    if verb_ratio < 0.4:
        tips.append(LiveTip(
            type="warning",
            message="Start more bullets with strong action verbs (Led, Built, Optimized).",
        ))
    if weak_count > 0:
        tips.append(LiveTip(
            type="warning",
            message=f"Replace weak phrases like \"responsible for\" ({weak_count} found) with action verbs.",
        ))

    return score, tips


def _compute_structure_score(text: str) -> Tuple[int, List[LiveTip]]:
    """Score based on length, bullet usage, and section presence."""
    tips: List[LiveTip] = []
    words = tokenize(text)
    word_count = len(words)
    bullets = _BULLET_RE.findall(text)
    lower = text.lower()

    score = 100

    # More lenient length checks - 1 page resume is ~300-500 words
    if word_count < 100:
        score -= 40
        tips.append(LiveTip(type="warning", message="Resume looks short. Aim for 250-500 words of substance."))
    elif word_count > 800:
        score -= 15
        tips.append(LiveTip(type="info", message="Resume is detailed. Consider condensing if over 2 pages."))
    else:
        tips.append(LiveTip(type="good", message="Length is in a healthy range for 1-page resume."))

    if len(bullets) < 3:
        score -= 25
        tips.append(LiveTip(type="info", message="Use bullet points to make achievements scannable."))

    sections = ["experience", "education", "skill", "project"]
    present = sum(1 for s in sections if s in lower)
    if present < 2:
        score -= 20
        tips.append(LiveTip(type="info", message="Add clear sections (Experience, Skills, Education, Projects)."))

    return max(0, min(100, score)), tips


def compute_live_feedback(resume_text: str, jd_text: str) -> LiveFeedbackResponse:
    """
    Fast, LLM-free scoring for the live editor. Combines ATS keyword matching
    with local impact + structure heuristics. Designed to run on every keystroke.
    """
    resume_text = resume_text or ""
    word_count = len(tokenize(resume_text))

    # ATS (reuse existing engine if a JD is provided)
    if jd_text and jd_text.strip():
        ats = compute_ats_score(resume_text, jd_text)
        ats_score = ats.score
        matched = ats.matched_keywords[:20]
        missing = ats.missing_keywords[:20]
    else:
        ats_score = 0.0
        matched = []
        missing = []

    impact_score, impact_tips = _compute_impact_score(resume_text)
    structure_score, structure_tips = _compute_structure_score(resume_text)

    # Overall: weighted blend. If no JD, weight impact/structure more.
    if jd_text and jd_text.strip():
        overall = round(ats_score * 0.45 + impact_score * 0.30 + structure_score * 0.25)
    else:
        overall = round(impact_score * 0.55 + structure_score * 0.45)
    overall = max(0, min(100, overall))

    tips: List[LiveTip] = []
    if jd_text and jd_text.strip() and missing:
        top_missing = ", ".join(missing[:5])
        tips.append(LiveTip(
            type="warning",
            message=f"Missing JD keywords: {top_missing}.",
        ))
    tips.extend(impact_tips)
    tips.extend(structure_tips)

    return LiveFeedbackResponse(
        overall_score=overall,
        ats_score=ats_score,
        impact_score=impact_score,
        structure_score=structure_score,
        matched_keywords=matched,
        missing_keywords=missing,
        word_count=word_count,
        tips=tips[:8],
    )


# ── Red Flag Detector ───────────────────────────────────────────────────────

# Common resume buzzwords that recruiters dislike when overused
BUZZWORDS = {
    "synergy", "leverage", "utilize", "innovative", "passionate", "rockstar",
    "ninja", "guru", "wizard", "thought leader", "team player", "detail-oriented",
    "proactive", "results-driven", "strategic thinker", "go-getter", "hard-working",
    "self-motivated", "enthusiastic", "dynamic", "proven track record", "best of breed",
}

# Weak action verbs that should be replaced
WEAK_VERBS = {
    "handled", "dealt with", "managed", "helped", "supported", "assisted",
    "worked on", "responsible for", "tasked with", "involved in", "duties included",
}


def detect_red_flags(resume_text: str) -> RedFlagReport:
    """
    Scan resume for common red flags that recruiters dislike.
    Returns structured report with categorized warnings.
    """
    flags: List[RedFlag] = []
    resume_lower = resume_text.lower()
    lines = _split_lines(resume_text)
    bullets = [m.group(1).strip() for m in _BULLET_RE.finditer(resume_text)]
    candidates = bullets if bullets else [ln for ln in lines if len(ln) > 25]
    
    # 1. Repeated Buzzwords Detection
    buzzword_counts = Counter()
    for word in BUZZWORDS:
        count = resume_lower.count(word)
        if count > 0:
            buzzword_counts[word] = count
    
    excessive_buzzwords = {w: c for w, c in buzzword_counts.items() if c >= 3}
    if excessive_buzzwords:
        top_offenders = ", ".join([f"'{w}' ({c}x)" for w, c in list(excessive_buzzwords.items())[:3]])
        flags.append(RedFlag(
            category="buzzword",
            severity="warning",
            message=f"Overused buzzwords detected: {top_offenders}",
            details="Replace generic buzzwords with specific, measurable achievements."
        ))
    
    # 2. Lack of Metrics/Numbers
    if candidates:
        bullets_with_metrics = sum(1 for b in candidates if _PERCENT_METRIC_RE.search(b))
        metric_ratio = bullets_with_metrics / len(candidates)
        
        if metric_ratio < 0.2:
            flags.append(RedFlag(
                category="metrics",
                severity="critical",
                message=f"Only {bullets_with_metrics}/{len(candidates)} bullet points contain numbers or metrics",
                details="Add quantified results: percentages, dollar amounts, scale, or time saved."
            ))
        elif metric_ratio < 0.4:
            flags.append(RedFlag(
                category="metrics",
                severity="warning",
                message=f"{bullets_with_metrics}/{len(candidates)} bullets have metrics — add more quantified impact",
                details="Aim for 50%+ of bullets containing numbers to demonstrate measurable achievements."
            ))
    
    # 3. Weak Action Verbs
    weak_verb_bullets = []
    for bullet in candidates:
        first_word = bullet.split()[0].lower().strip(".,:;") if bullet.split() else ""
        if first_word in WEAK_VERBS or any(weak in bullet.lower() for weak in ["responsible for", "worked on", "helped with"]):
            weak_verb_bullets.append(bullet[:50] + "...")
    
    if len(weak_verb_bullets) >= 3:
        flags.append(RedFlag(
            category="weak_verbs",
            severity="warning",
            message=f"{len(weak_verb_bullets)} bullets use weak phrasing",
            details=f"Replace with strong action verbs like: Led, Built, Optimized, Delivered, Reduced. Example: \"{weak_verb_bullets[0]}\""
        ))
    
    # 4. Employment Gaps Detection (YYYY - YYYY pattern)
    date_pattern = re.compile(r'(20\d{2}|19\d{2})')
    years = [int(y) for y in date_pattern.findall(resume_text)]
    years = sorted(set(years))
    
    if len(years) >= 2:
        gaps = []
        for i in range(len(years) - 1):
            gap = years[i+1] - years[i]
            if gap > 2:  # 2+ year gap
                gaps.append((years[i], years[i+1], gap))
        
        if gaps:
            for start, end, duration in gaps:
                flags.append(RedFlag(
                    category="gap",
                    severity="info",
                    message=f"{duration}-year gap detected ({start} → {end})",
                    details="Consider adding a brief explanation if this gap is significant (education, personal projects, freelance)."
                ))
    
    # 5. Technology Overload (too many unrelated techs)
    tech_keywords = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node', 'django', 'flask', 'spring', 'aws', 'azure', 'gcp', 'docker',
        'kubernetes', 'terraform', 'jenkins', 'git', 'sql', 'mongodb', 'postgresql',
        'redis', 'kafka', 'spark', 'hadoop', 'tensorflow', 'pytorch', 'scikit',
    ]
    
    found_techs = [tech for tech in tech_keywords if tech in resume_lower]
    
    if len(found_techs) > 20:
        flags.append(RedFlag(
            category="tech_overload",
            severity="warning",
            message=f"{len(found_techs)} technologies listed — may appear scattered",
            details="Focus on technologies relevant to your target role. Quality > quantity."
        ))
    
    # 6. Resume Length Issues - More lenient for 1-page resumes
    word_count = len(tokenize(resume_text))
    
    # Don't flag if between 200-1200 words (good for 1-2 page resumes)
    if word_count < 200:
        flags.append(RedFlag(
            category="length",
            severity="info",
            message=f"Resume is concise ({word_count} words)",
            details="A good 1-page resume typically has 300-500 words. Consider adding more achievement details if needed."
        ))
    elif word_count > 1200:
        flags.append(RedFlag(
            category="length",
            severity="info",
            message=f"Resume is detailed ({word_count} words)",
            details="Consider condensing to 1-2 pages if over 2 pages. Focus on most impactful achievements."
        ))
    
    # 7. No Clear Sections
    sections = ["experience", "education", "skill", "project"]
    present_sections = sum(1 for s in sections if s in resume_lower)
    
    if present_sections < 2:
        flags.append(RedFlag(
            category="structure",
            severity="warning",
            message="Resume lacks clear section headers",
            details="Add sections: Professional Experience, Skills, Education, Projects to improve readability."
        ))
    
    # Build severity breakdown
    severity_breakdown = {"critical": 0, "warning": 0, "info": 0}
    for flag in flags:
        severity_breakdown[flag.severity] += 1
    
    return RedFlagReport(
        flags=flags,
        total_count=len(flags),
        severity_breakdown=severity_breakdown,
    )
