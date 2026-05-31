import re
from typing import Set, List, Tuple
from models.schemas import ATSResult, LiveFeedbackResponse, LiveTip

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
    Compute ATS compatibility score.
    
    Formula: match_score = (matched_keywords / total_jd_keywords) * 100
    Enhanced with stopword removal and case normalization.
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
    
    matched = jd_keywords & resume_keywords
    missing = jd_keywords - resume_keywords
    
    # Filter to meaningful missing keywords (length > 3, not pure numbers)
    meaningful_missing = sorted([
        k for k in missing
        if len(k) > 3 and not k.replace(" ", "").isdigit()
    ])
    
    meaningful_matched = sorted([
        k for k in matched
        if len(k) > 3
    ])
    
    # Cap at meaningful set sizes
    total = len([k for k in jd_keywords if len(k) > 3])
    match_count = len(meaningful_matched)
    
    raw_score = (match_count / total * 100) if total > 0 else 0.0
    score = min(round(raw_score, 1), 100.0)
    
    # Keyword density: how dense are matched terms in resume
    resume_tokens = tokenize(resume_text)
    resume_len = max(len(resume_tokens), 1)
    density = round((match_count / resume_len) * 100, 2)
    
    return ATSResult(
        score=score,
        matched_keywords=meaningful_matched[:30],
        missing_keywords=meaningful_missing[:30],
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

    if word_count < 150:
        score -= 40
        tips.append(LiveTip(type="warning", message="Resume looks short. Aim for 250-600 words of substance."))
    elif word_count > 900:
        score -= 20
        tips.append(LiveTip(type="warning", message="Resume is long. Tighten it toward one page of impact."))
    else:
        tips.append(LiveTip(type="good", message="Length is in a healthy range."))

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
