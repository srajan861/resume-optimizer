import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException
from core.supabase import get_supabase
from core.config import settings


# ── Resume Storage ────────────────────────────────────────────────────────────

async def upload_resume_file(file_bytes: bytes, filename: str, user_id: str) -> str:
    """Upload resume file to Supabase Storage and return public URL."""
    supabase = get_supabase()
    
    ext = filename.rsplit(".", 1)[-1].lower()
    storage_path = f"{user_id}/{uuid.uuid4()}.{ext}"
    
    try:
        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": f"application/{'pdf' if ext == 'pdf' else 'vnd.openxmlformats-officedocument.wordprocessingml.document'}"},
        )
        
        url_data = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(storage_path)
        return url_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


async def save_resume_record(
    user_id: str,
    file_url: str,
    parsed_text: str,
    filename: str,
) -> str:
    """Save resume metadata to database and return resume_id."""
    supabase = get_supabase()
    resume_id = str(uuid.uuid4())
    
    try:
        supabase.table("resumes").insert({
            "id": resume_id,
            "user_id": user_id,
            "file_url": file_url,
            "parsed_text": parsed_text,
            "filename": filename,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        return resume_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")


async def save_resume_record_with_latex(
    user_id: str,
    file_url: str,
    parsed_text: str,
    latex_code: str,
    filename: str,
) -> str:
    """Save resume with LaTeX code to database and return resume_id."""
    supabase = get_supabase()
    resume_id = str(uuid.uuid4())
    
    try:
        supabase.table("resumes").insert({
            "id": resume_id,
            "user_id": user_id,
            "file_url": file_url,
            "parsed_text": parsed_text,
            "latex_code": latex_code,
            "filename": filename,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        return resume_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")


async def get_resume_text(resume_id: str, user_id: str) -> str:
    """Fetch parsed resume text from database."""
    supabase = get_supabase()
    
    try:
        result = (
            supabase.table("resumes")
            .select("parsed_text")
            .eq("id", resume_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        return result.data["parsed_text"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resume: {str(e)}")


# ── Analysis Storage ──────────────────────────────────────────────────────────

async def save_analysis(
    user_id: str,
    resume_id: str,
    jd_content: str,
    ats_score: float,
    recruiter_score: float,
    ats_data: dict,
    recruiter_data: dict,
    rewritten_bullets: list,
    jd_intelligence: Optional[dict] = None,
    strength_breakdown: Optional[dict] = None,
) -> str:
    """Save full analysis result to database."""
    supabase = get_supabase()
    analysis_id = str(uuid.uuid4())
    
    try:
        # Save JD
        jd_id = str(uuid.uuid4())
        supabase.table("job_descriptions").insert({
            "id": jd_id,
            "user_id": user_id,
            "content": jd_content,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        
        # Save analysis
        supabase.table("analyses").insert({
            "id": analysis_id,
            "user_id": user_id,
            "resume_id": resume_id,
            "jd_id": jd_id,
            "ats_score": ats_score,
            "recruiter_score": recruiter_score,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        
        # Save feedback
        supabase.table("feedback").insert({
            "id": str(uuid.uuid4()),
            "analysis_id": analysis_id,
            "missing_keywords": ats_data.get("missing_keywords", []),
            "matched_keywords": ats_data.get("matched_keywords", []),
            "suggestions": recruiter_data.get("suggestions", []),
            "strengths": recruiter_data.get("strengths", []),
            "weaknesses": recruiter_data.get("weaknesses", []),
            "rewritten_points": rewritten_bullets,
            "persona": recruiter_data.get("persona", "standard"),
            "jd_intelligence": jd_intelligence or {},
            "strength_breakdown": strength_breakdown or {},
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        
        return analysis_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")


async def get_analysis_by_id(analysis_id: str, user_id: str) -> Optional[dict]:
    """Fetch full analysis details including resume text, LaTeX code, and job description."""
    supabase = get_supabase()
    
    try:
        # Fetch analysis with related data (including latex_code)
        analysis = (
            supabase.table("analyses")
            .select("*, job_descriptions(content), resumes(parsed_text, latex_code)")
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not analysis.data:
            return None
        
        # Fetch feedback
        feedback = (
            supabase.table("feedback")
            .select("*")
            .eq("analysis_id", analysis_id)
            .single()
            .execute()
        )
        
        # Extract nested data
        jd_data = analysis.data.get("job_descriptions", {})
        resume_data = analysis.data.get("resumes", {})
        
        # Build combined result
        return {
            "analysis_id": analysis.data.get("id"),
            "user_id": analysis.data.get("user_id"),
            "resume_id": analysis.data.get("resume_id"),
            "ats_score": analysis.data.get("ats_score", 0),
            "recruiter_score": analysis.data.get("recruiter_score", 0),
            "created_at": analysis.data.get("created_at", ""),
            "resume_text": resume_data.get("parsed_text", "") if isinstance(resume_data, dict) else "",
            "latex_code": resume_data.get("latex_code", "") if isinstance(resume_data, dict) else "",
            "job_description": jd_data.get("content", "") if isinstance(jd_data, dict) else "",
            "feedback": feedback.data if feedback.data else {},
        }
    except Exception as e:
        print(f"❌ Failed to fetch analysis: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis: {str(e)}")


async def get_user_history(user_id: str, limit: int = 20) -> List[dict]:
    """Fetch analysis history for a user."""
    supabase = get_supabase()
    
    try:
        result = (
            supabase.table("analyses")
            .select("id, resume_id, ats_score, recruiter_score, created_at, job_descriptions(content)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


# ── Resume Evolution ──────────────────────────────────────────────────────────

async def get_resume_evolution(resume_id: str, user_id: str) -> Optional[dict]:
    """Fetch all versions/analyses for a specific resume to track evolution."""
    supabase = get_supabase()
    
    try:
        # Get all analyses for this resume, ordered by creation time
        result = (
            supabase.table("analyses")
            .select("id, ats_score, recruiter_score, created_at, job_descriptions(content)")
            .eq("resume_id", resume_id)
            .eq("user_id", user_id)
            .order("created_at", desc=False)  # Ascending for version numbering
            .execute()
        )
        
        if not result.data:
            return None
        
        versions = []
        for idx, analysis in enumerate(result.data, 1):
            jd_content = (analysis.get("job_descriptions") or {}).get("content", "")
            jd_preview = jd_content[:100] if jd_content else "No JD"
            
            versions.append({
                "analysis_id": analysis["id"],
                "version_number": idx,
                "ats_score": float(analysis.get("ats_score", 0)),
                "recruiter_score": float(analysis.get("recruiter_score", 0)),
                "created_at": analysis.get("created_at", ""),
                "jd_preview": jd_preview,
            })
        
        # Calculate improvement
        first_score = versions[0]["ats_score"] if versions else 0
        latest_score = versions[-1]["ats_score"] if versions else 0
        improvement = latest_score - first_score
        
        return {
            "resume_id": resume_id,
            "total_versions": len(versions),
            "first_score": first_score,
            "latest_score": latest_score,
            "improvement": round(improvement, 1),
            "versions": versions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch evolution: {str(e)}")


async def compare_versions(v1_id: str, v2_id: str, user_id: str) -> Optional[dict]:
    """Compare two analysis versions side-by-side."""
    supabase = get_supabase()
    
    try:
        # Fetch both analyses
        v1 = (
            supabase.table("analyses")
            .select("id, ats_score, recruiter_score, created_at, job_descriptions(content), feedback(matched_keywords, missing_keywords)")
            .eq("id", v1_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        
        v2 = (
            supabase.table("analyses")
            .select("id, ats_score, recruiter_score, created_at, job_descriptions(content), feedback(matched_keywords, missing_keywords)")
            .eq("id", v2_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        
        if not v1.data or not v2.data:
            return None
        
        # Build version snapshots
        def build_snapshot(data, version_num):
            jd_content = (data.get("job_descriptions") or {}).get("content", "")
            return {
                "analysis_id": data["id"],
                "version_number": version_num,
                "ats_score": float(data.get("ats_score", 0)),
                "recruiter_score": float(data.get("recruiter_score", 0)),
                "created_at": data.get("created_at", ""),
                "jd_preview": jd_content[:100] if jd_content else "",
            }
        
        version1 = build_snapshot(v1.data, 1)
        version2 = build_snapshot(v2.data, 2)
        
        # Calculate diffs
        score_diff = version2["ats_score"] - version1["ats_score"]
        recruiter_diff = version2["recruiter_score"] - version1["recruiter_score"]
        
        # Keyword changes
        v1_feedback = v1.data.get("feedback", {})
        v2_feedback = v2.data.get("feedback", {})
        
        v1_matched = set(v1_feedback.get("matched_keywords", []) if isinstance(v1_feedback, dict) else [])
        v2_matched = set(v2_feedback.get("matched_keywords", []) if isinstance(v2_feedback, dict) else [])
        
        added_keywords = list(v2_matched - v1_matched)
        removed_keywords = list(v1_matched - v2_matched)
        
        return {
            "version1": version1,
            "version2": version2,
            "score_diff": round(score_diff, 1),
            "recruiter_diff": round(recruiter_diff, 1),
            "keyword_changes": {
                "added": added_keywords[:10],
                "removed": removed_keywords[:10],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare versions: {str(e)}")


async def delete_analysis(analysis_id: str, user_id: str) -> bool:
    """Delete an analysis and its associated feedback."""
    supabase = get_supabase()
    
    try:
        # Verify ownership first
        check = (
            supabase.table("analyses")
            .select("id")
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not check.data:
            return False
        
        # Delete feedback first (foreign key constraint)
        supabase.table("feedback").delete().eq("analysis_id", analysis_id).execute()
        
        # Delete analysis
        supabase.table("analyses").delete().eq("id", analysis_id).eq("user_id", user_id).execute()
        
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")