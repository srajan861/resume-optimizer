from fastapi import APIRouter, Query
from models.schemas import HistoryResponse, HistoryItem
from services.storage import get_user_history

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user_id: str = Query(..., description="User ID from Supabase Auth"),
    limit: int = Query(20, ge=1, le=100),
):
    """Fetch analysis history for authenticated user."""
    items_raw = await get_user_history(user_id, limit)
    
    items = []
    for row in items_raw:
        jd_content = ""
        if row.get("job_descriptions"):
            jd_content = row["job_descriptions"].get("content", "")
        
        items.append(HistoryItem(
            analysis_id=row["id"],
            resume_id=row["resume_id"],
            jd_preview=jd_content[:120] + "..." if len(jd_content) > 120 else jd_content,
            ats_score=row.get("ats_score", 0),
            recruiter_score=row.get("recruiter_score", 0),
            created_at=row.get("created_at", ""),
        ))
    
    return HistoryResponse(items=items, total=len(items))
