from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Any
from datetime import datetime
import uuid
import re


# ── Resume ──────────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    resume_id: str
    file_url: str
    parsed_text: str
    message: str = "Resume uploaded and parsed successfully"


class ParsedResume(BaseModel):
    raw_text: str
    skills: List[str] = []
    experience_snippets: List[str] = []
    projects: List[str] = []
    bullet_points: List[str] = []


# ── Job Description ──────────────────────────────────────────────────────────

class JobDescriptionInput(BaseModel):
    content: str = Field(..., min_length=50, max_length=50000, description="Full job description text")
    # user_id removed - obtained from JWT token
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate job description content."""
        if not v or not v.strip():
            raise ValueError("Job description cannot be empty")
        
        # Check for minimum alphanumeric content
        alphanumeric_count = sum(c.isalnum() for c in v)
        if alphanumeric_count < 30:
            raise ValueError("Job description must contain at least 30 alphanumeric characters")
        
        return v.strip()


# ── Analysis ─────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    resume_id: str = Field(..., min_length=1, max_length=100)
    job_description: str = Field(..., min_length=50, max_length=50000)
    # user_id removed - obtained from JWT token
    role_type: Optional[str] = Field(default="general", pattern="^(sde|ml|analyst|general)$")
    persona: Optional[str] = Field(default="standard", pattern="^(standard|faang|startup|hr)$")
    
    @field_validator('resume_id')
    @classmethod
    def validate_resume_id(cls, v: str) -> str:
        """Validate resume ID format."""
        if not v or not v.strip():
            raise ValueError("Resume ID is required")
        
        # Validate UUID format
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid resume ID format")
        
        return v.strip()
    
    @field_validator('job_description')
    @classmethod
    def validate_jd(cls, v: str) -> str:
        """Validate job description."""
        if not v or not v.strip():
            raise ValueError("Job description is required")
        
        # Check for minimum alphanumeric content
        alphanumeric_count = sum(c.isalnum() for c in v)
        if alphanumeric_count < 30:
            raise ValueError("Job description must contain sufficient readable content")
        
        return v.strip()


class ATSResult(BaseModel):
    score: float = Field(..., ge=0, le=100)
    matched_keywords: List[str]
    missing_keywords: List[str]
    total_jd_keywords: int
    keyword_density: float


class RecruiterFeedback(BaseModel):
    score: float = Field(..., ge=0, le=10)
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    persona: Optional[str] = "standard"


class JDIntelligence(BaseModel):
    role_summary: str = ""
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    experience_level: str = ""
    key_responsibilities: List[str] = []
    education: str = ""


class StrengthMetric(BaseModel):
    score: int = Field(0, ge=0, le=100)
    rationale: str = ""


class StrengthBreakdown(BaseModel):
    skill_match: StrengthMetric = StrengthMetric()
    experience_relevance: StrengthMetric = StrengthMetric()
    project_depth: StrengthMetric = StrengthMetric()
    keyword_coverage: StrengthMetric = StrengthMetric()
    impact_score: StrengthMetric = StrengthMetric()
    structure_score: StrengthMetric = StrengthMetric()
    overall: int = Field(0, ge=0, le=100)


class RewrittenBullet(BaseModel):
    original: str
    improved: str


class AnalysisResult(BaseModel):
    analysis_id: str
    ats: ATSResult
    recruiter: RecruiterFeedback
    rewritten_bullets: List[RewrittenBullet]
    jd_intelligence: Optional[JDIntelligence] = None
    strength_breakdown: Optional[StrengthBreakdown] = None
    semantic_match: Optional["SemanticMatch"] = None
    created_at: str


class AnalysisResponse(BaseModel):
    success: bool = True
    data: AnalysisResult


# ── Semantic Matching ────────────────────────────────────────────────────────

class SemanticMatch(BaseModel):
    score: float = Field(..., ge=0, le=100, description="Semantic similarity score 0-100")
    interpretation: str = ""
    embedding_dimensions: int = 128
    raw_similarity: float = Field(0.0, ge=0, le=1)
    keyword_score: float = 0.0  # ATS score for comparison
    score_difference: float = 0.0  # Semantic - Keyword


class SemanticMatchResponse(BaseModel):
    semantic_match: SemanticMatch


# ── Rewrite ──────────────────────────────────────────────────────────────────

class RewriteRequest(BaseModel):
    bullet_points: List[str] = Field(..., min_length=1, max_length=20)
    job_context: Optional[str] = Field(default="", max_length=10000)
    
    @field_validator('bullet_points')
    @classmethod
    def validate_bullets(cls, v: List[str]) -> List[str]:
        """Validate bullet points."""
        if not v:
            raise ValueError("At least one bullet point is required")
        
        if len(v) > 20:
            raise ValueError("Maximum 20 bullet points allowed")
        
        # Validate each bullet point
        validated = []
        for i, bullet in enumerate(v):
            if not bullet or not bullet.strip():
                raise ValueError(f"Bullet point {i+1} is empty")
            
            if len(bullet) > 1000:
                raise ValueError(f"Bullet point {i+1} is too long (max 1000 characters)")
            
            validated.append(bullet.strip())
        
        return validated


class RewriteResponse(BaseModel):
    rewritten: List[RewrittenBullet]


# ── Live Feedback (Real-Time Editing) ────────────────────────────────────────

class LiveFeedbackRequest(BaseModel):
    resume_text: str = Field(default="", max_length=100000)
    job_description: str = Field(default="", max_length=50000)
    
    @field_validator('resume_text', 'job_description')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text fields."""
        if v and len(v) > 100000:
            raise ValueError("Text is too long")
        return v.strip() if v else ""


class LiveTip(BaseModel):
    type: str = "info"  # good | warning | info
    message: str


class LiveFeedbackResponse(BaseModel):
    overall_score: int = Field(0, ge=0, le=100)
    ats_score: float = Field(0, ge=0, le=100)
    impact_score: int = Field(0, ge=0, le=100)
    structure_score: int = Field(0, ge=0, le=100)
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    word_count: int = 0
    tips: List[LiveTip] = []


# ── Cover Letter ─────────────────────────────────────────────────────────────

class CoverLetterRequest(BaseModel):
    analysis_id: str = Field(..., min_length=1, max_length=100)
    # user_id removed - obtained from JWT token
    tone: Optional[str] = Field(default="professional", pattern="^(professional|enthusiastic|concise)$")
    applicant_name: Optional[str] = Field(default="", max_length=100)
    company_name: Optional[str] = Field(default="", max_length=200)
    role_title: Optional[str] = Field(default="", max_length=200)
    
    @field_validator('analysis_id')
    @classmethod
    def validate_analysis_id(cls, v: str) -> str:
        """Validate analysis ID format."""
        if not v or not v.strip():
            raise ValueError("Analysis ID is required")
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid analysis ID format")
        
        return v.strip()
    
    @field_validator('applicant_name', 'company_name', 'role_title')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> str:
        """Validate string fields."""
        if not v:
            return ""
        
        # Remove potentially dangerous characters
        v = v.strip()
        
        # Remove control characters
        v = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        
        return v


class CoverLetterResponse(BaseModel):
    cover_letter: str
    tone: str


# ── Skill Gap Roadmap ────────────────────────────────────────────────────────

class SkillGapRequest(BaseModel):
    analysis_id: str = Field(..., min_length=1, max_length=100)
    # user_id removed - obtained from JWT token
    
    @field_validator('analysis_id')
    @classmethod
    def validate_analysis_id(cls, v: str) -> str:
        """Validate analysis ID format."""
        if not v or not v.strip():
            raise ValueError("Analysis ID is required")
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid analysis ID format")
        
        return v.strip()


class SkillGapItem(BaseModel):
    skill: str
    priority: str = "medium"  # high | medium | low
    reason: str = ""
    learning_path: List[str] = []
    estimated_time: str = ""


class SkillGapRoadmap(BaseModel):
    summary: str = ""
    readiness_score: int = 0  # 0-100
    matched_skills: List[str] = []
    missing_skills: List[SkillGapItem] = []


class SkillGapResponse(BaseModel):
    roadmap: SkillGapRoadmap


# ── Red Flag Detection ──────────────────────────────────────────────────────

class RedFlag(BaseModel):
    category: str  # buzzword | metrics | gap | weak_verbs | tech_overload | length
    severity: str  # critical | warning | info
    message: str
    details: Optional[str] = ""


class RedFlagReport(BaseModel):
    flags: List[RedFlag] = []
    total_count: int = 0
    severity_breakdown: dict = {"critical": 0, "warning": 0, "info": 0}


class RedFlagRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=100000)
    
    @field_validator('resume_text')
    @classmethod
    def validate_resume_text(cls, v: str) -> str:
        """Validate resume text."""
        if not v or not v.strip():
            raise ValueError("Resume text is required")
        
        if len(v.strip()) < 50:
            raise ValueError("Resume text is too short (minimum 50 characters)")
        
        return v.strip()


class RedFlagResponse(BaseModel):
    report: RedFlagReport


# ── Resume Evolution Tracker ────────────────────────────────────────────────

class VersionSnapshot(BaseModel):
    analysis_id: str
    version_number: int
    ats_score: float
    recruiter_score: float
    created_at: str
    jd_preview: str = ""


class EvolutionTimeline(BaseModel):
    resume_id: str
    total_versions: int
    first_score: float
    latest_score: float
    improvement: float  # percentage improvement
    versions: List[VersionSnapshot]


class EvolutionResponse(BaseModel):
    timeline: EvolutionTimeline


class VersionCompareRequest(BaseModel):
    version1_id: str = Field(..., min_length=1, max_length=100)
    version2_id: str = Field(..., min_length=1, max_length=100)
    # user_id removed - obtained from JWT token
    
    @field_validator('version1_id', 'version2_id')
    @classmethod
    def validate_version_ids(cls, v: str) -> str:
        """Validate version ID format."""
        if not v or not v.strip():
            raise ValueError("Version ID is required")
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid version ID format")
        
        return v.strip()


class VersionComparison(BaseModel):
    version1: VersionSnapshot
    version2: VersionSnapshot
    score_diff: float
    recruiter_diff: float
    keyword_changes: dict  # added, removed keywords


class CompareResponse(BaseModel):
    comparison: VersionComparison


# ── History ──────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    analysis_id: str
    resume_id: str
    jd_preview: str
    ats_score: float
    recruiter_score: float
    created_at: str


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int


class AnalysisDetailResponse(BaseModel):
    analysis_id: str
    resume_text: str
    job_description: str
    ats: ATSResult
    recruiter: RecruiterFeedback
    rewritten_bullets: List[RewrittenBullet]
    jd_intelligence: Optional[JDIntelligence] = None
    strength_breakdown: Optional[StrengthBreakdown] = None
    created_at: str


# ── AI Resume Auto-Editor ───────────────────────────────────────────────────

class EditSuggestion(BaseModel):
    """A single edit suggestion for the resume."""
    section: str  # experience | skills | education | projects | summary
    type: str  # add | replace | remove | reword
    original_text: str = ""  # Empty if type is 'add'
    suggested_text: str
    reason: str  # Why this change improves the resume
    priority: str = "medium"  # high | medium | low
    impact: str = ""  # Expected impact on ATS/recruiter score


class AutoEditSuggestionsRequest(BaseModel):
    analysis_id: str = Field(..., min_length=1, max_length=100)
    # user_id removed - obtained from JWT token
    max_suggestions: Optional[int] = Field(default=10, ge=1, le=50)
    
    @field_validator('analysis_id')
    @classmethod
    def validate_analysis_id(cls, v: str) -> str:
        """Validate analysis ID format."""
        if not v or not v.strip():
            raise ValueError("Analysis ID is required")
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid analysis ID format")
        
        return v.strip()


class AutoEditSuggestionsResponse(BaseModel):
    suggestions: List[EditSuggestion]
    total_count: int
    summary: str  # Overall assessment of what needs improvement


class ApplyEditsRequest(BaseModel):
    analysis_id: str = Field(..., min_length=1, max_length=100)
    resume_text: str = Field(..., min_length=100, max_length=100000)
    applied_suggestions: List[EditSuggestion] = Field(..., max_length=50)
    format: str = Field(default="both", pattern="^(pdf|docx|both)$")
    # user_id removed - obtained from JWT token
    
    @field_validator('analysis_id')
    @classmethod
    def validate_analysis_id(cls, v: str) -> str:
        """Validate analysis ID format."""
        if not v or not v.strip():
            raise ValueError("Analysis ID is required")
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid analysis ID format")
        
        return v.strip()
    
    @field_validator('resume_text')
    @classmethod
    def validate_resume_text(cls, v: str) -> str:
        """Validate resume text."""
        if not v or not v.strip():
            raise ValueError("Resume text is required")
        
        if len(v.strip()) < 100:
            raise ValueError("Resume text is too short")
        
        return v.strip()
    
    @field_validator('applied_suggestions')
    @classmethod
    def validate_suggestions(cls, v: List[EditSuggestion]) -> List[EditSuggestion]:
        """Validate applied suggestions."""
        if not v:
            raise ValueError("At least one suggestion must be applied")
        
        if len(v) > 50:
            raise ValueError("Too many suggestions (maximum 50)")
        
        return v


class GeneratedResumeFile(BaseModel):
    format: str  # pdf | docx
    filename: str
    download_url: str
    size_bytes: int


class ApplyEditsResponse(BaseModel):
    success: bool
    edited_text: str  # The modified resume text
    files: List[GeneratedResumeFile]  # Generated PDF/DOCX files
    changes_summary: str  # Summary of what was changed
