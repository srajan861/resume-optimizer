from fastapi import APIRouter, HTTPException, Query
from models.schemas import (
    EvolutionResponse, EvolutionTimeline,
    CompareResponse, VersionComparison,
)
from services.storage import get_resume_evolution, compare_versions

router = APIRouter()


@router.get("/evolution/{resume_id}", response_model=EvolutionResponse)
async def get_evolution_timeline(resume_id: str, user_id: str = Query(...)):
    """
    Get the evolution timeline for a specific resume.
    Shows all versions (analyses) with ATS/recruiter scores over time.
    
    Returns:
    - Version history with timestamps
    - Score progression graph data
    - Improvement metrics
    """
    timeline_data = await get_resume_evolution(resume_id, user_id)
    
    if not timeline_data:
        raise HTTPException(
            status_code=404,
            detail="No versions found for this resume"
        )
    
    timeline = EvolutionTimeline(**timeline_data)
    return EvolutionResponse(timeline=timeline)


@router.get("/evolution/compare", response_model=CompareResponse)
async def compare_resume_versions(
    v1: str = Query(..., description="Analysis ID of version 1"),
    v2: str = Query(..., description="Analysis ID of version 2"),
    user_id: str = Query(...),
):
    """
    Compare two resume analysis versions side-by-side.
    
    Shows:
    - Score differences (ATS, recruiter)
    - Keyword changes (added/removed)
    - Improvement metrics
    """
    comparison_data = await compare_versions(v1, v2, user_id)
    
    if not comparison_data:
        raise HTTPException(
            status_code=404,
            detail="One or both versions not found"
        )
    
    comparison = VersionComparison(**comparison_data)
    return CompareResponse(comparison=comparison)
