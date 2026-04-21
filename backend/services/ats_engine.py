import re
from typing import Set, List, Tuple
from models.schemas import ATSResult

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
