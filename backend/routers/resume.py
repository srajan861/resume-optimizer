from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.schemas import ResumeUploadResponse
from services.parser import extract_text_from_file, parse_resume_sections
from services.storage import upload_resume_file, save_resume_record_with_latex
from services.latex_service import resume_to_latex
from core.config import settings

router = APIRouter()

MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """
    Upload a resume (PDF or DOCX), extract text, convert to LaTeX, and store in Supabase.
    LaTeX format preserves ALL formatting and structure.
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
    
    # Extract text
    import io
    up = UploadFile(filename=filename, file=io.BytesIO(file_bytes))
    raw_text = await extract_text_from_file(up)
    
    # Parse sections
    parsed = parse_resume_sections(raw_text)
    
    # Convert to LaTeX (preserves formatting)
    print("🔄 Generating LaTeX code...")
    latex_code = await resume_to_latex(raw_text, filename)
    print(f"✅ LaTeX code ready ({len(latex_code)} chars)")
    
    # Upload original file to Supabase Storage
    file_url = await upload_resume_file(file_bytes, filename, user_id)
    
    # Save to DB with LaTeX code
    resume_id = await save_resume_record_with_latex(
        user_id=user_id,
        file_url=file_url,
        parsed_text=raw_text,
        latex_code=latex_code,
        filename=filename,
    )
    
    return ResumeUploadResponse(
        resume_id=resume_id,
        file_url=file_url,
        parsed_text=raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
    )
