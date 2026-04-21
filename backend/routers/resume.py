from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.schemas import ResumeUploadResponse
from services.parser import extract_text_from_file, parse_resume_sections
from services.storage import upload_resume_file, save_resume_record
from core.config import settings

router = APIRouter()

MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """
    Upload a resume (PDF or DOCX), extract text, and store in Supabase.
    Returns resume_id and parsed text preview.
    """
    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )
    
    # Read and size-check
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB.",
        )
    
    # Re-wrap bytes as UploadFile-like for text extraction
    from io import BytesIO
    import types

    mock_file = types.SimpleNamespace(
        filename=filename,
        read=lambda: file_bytes,
    )

    # Extract text (need UploadFile interface)
    from fastapi import UploadFile as FUF
    import io

    up = UploadFile(filename=filename, file=io.BytesIO(file_bytes))
    raw_text = await extract_text_from_file(up)
    
    # Parse sections
    parsed = parse_resume_sections(raw_text)
    
    # Upload to Supabase Storage
    file_url = await upload_resume_file(file_bytes, filename, user_id)
    
    # Save to DB
    resume_id = await save_resume_record(
        user_id=user_id,
        file_url=file_url,
        parsed_text=raw_text,
        filename=filename,
    )
    
    return ResumeUploadResponse(
        resume_id=resume_id,
        file_url=file_url,
        parsed_text=raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
    )
