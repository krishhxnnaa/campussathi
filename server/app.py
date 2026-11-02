import os
import uuid
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import (
    init_db, save_report, get_report_by_id,
    get_all_reports_for_matching, save_contact_request
)
from .sarvam_service import (
    transcribe_audio, extract_report_details, synthesize_speech
)
from .matcher import match_and_rank_reports

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize database
init_db()

app = FastAPI(
    title="FindMyCampus API",
    description="Voice-First Smart Lost & Found for Sarvam Campus '26",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory simple rate limiting and deduplication guard
_last_submissions = {}

# --- Pydantic Schemas ---
class ExtractRequest(BaseModel):
    text: str
    current_fields: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    target_type: Optional[str] = None  # 'lost' or 'found'

class ReportCreateRequest(BaseModel):
    report_type: str = Field(..., pattern="^(lost|found)$")
    item_name: str = Field(..., min_length=2, max_length=150)
    category: str = Field("Other", max_length=50)
    color: Optional[str] = Field("", max_length=50)
    description: str = Field(..., min_length=5, max_length=1000)
    location: str = Field(..., min_length=2, max_length=150)
    approximate_time: Optional[str] = Field("", max_length=100)
    image_path: Optional[str] = None
    private_verification_details: Optional[str] = Field("", max_length=500)
    reporter_name: Optional[str] = Field("Anonymous Student", max_length=100)
    reporter_contact: Optional[str] = Field("", max_length=100)

class ContactRequestCreate(BaseModel):
    report_id: str
    requester_name: str = Field(..., min_length=2, max_length=100)
    requester_contact: str = Field(..., min_length=5, max_length=100)
    claim_verification_proof: str = Field(..., min_length=5, max_length=500)
    message: Optional[str] = Field("", max_length=500)

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    language_code: Optional[str] = "en-IN"

# --- API Endpoints ---

@app.get("/api/health")
def health_check():
    sarvam_configured = bool(os.getenv("SARVAM_API_KEY"))
    from .database import get_supabase_client
    supabase_connected = get_supabase_client() is not None
    return {
        "status": "healthy",
        "sarvam_configured": sarvam_configured,
        "supabase_connected": supabase_connected,
        "service": "FindMyCampus"
    }

@app.post("/api/sarvam/transcribe")
async def api_transcribe(audio: UploadFile = File(...)):
    """Accepts recorded audio from browser and transcribes using Saaras STT."""
    # Enforce file size limit (10MB)
    contents = await audio.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file exceeds 10MB limit")
    if len(contents) < 100:
        raise HTTPException(status_code=400, detail="Audio recording is empty or corrupted")

    filename = audio.filename or "recording.webm"
    result = transcribe_audio(contents, filename=filename)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Transcription failed"))

    return result

@app.post("/api/sarvam/extract")
def api_extract(req: ExtractRequest):
    """Uses Sarvam reasoning model to extract structured attributes from description."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Description text is empty")
    
    result = extract_report_details(req.text, req.current_fields)
    return result

@app.post("/api/sarvam/tts")
def api_tts(req: TTSRequest):
    """Generates audio for follow-up questions or confirmation messages."""
    result = synthesize_speech(req.text, req.language_code or "en-IN")
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "TTS synthesis failed"))
    return result

@app.post("/api/upload-image")
async def api_upload_image(image: UploadFile = File(...)):
    """Uploads an item photograph with mime and size verification."""
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and WebP images are permitted.")

    contents = await image.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 5MB limit.")

    ext = image.filename.split(".")[-1].lower() if "." in image.filename else "jpg"
    safe_filename = f"item_{uuid.uuid4().hex[:12]}.{ext}"
    target_path = os.path.join(UPLOADS_DIR, safe_filename)

    with open(target_path, "wb") as f:
        f.write(contents)

    return {"image_path": f"/uploads/{safe_filename}"}

@app.post("/api/reports")
def api_create_report(req: ReportCreateRequest, request: Request):
    """Creates and persists an explicit, user-confirmed report."""
    # Deduplication guard: check if identical item was posted within 30s
    dedup_key = f"{req.item_name.strip().lower()}_{req.location.strip().lower()}"
    now = time.time()
    if dedup_key in _last_submissions and (now - _last_submissions[dedup_key]) < 30:
        raise HTTPException(status_code=429, detail="Duplicate submission detected. Please wait before re-submitting.")
    _last_submissions[dedup_key] = now

    report_id = save_report(req.model_dump())
    return {
        "success": True,
        "report_id": report_id,
        "message": f"Report {report_id} has been recorded successfully."
    }

@app.post("/api/search")
def api_search(req: SearchRequest):
    """
    Search-first endpoint. Does NOT expose full database.
    Ranks candidates using attribute matching and textual token relevance.
    Masks private verification details and contact info.
    """
    clean_query = req.query.strip()
    if len(clean_query) < 2:
        return {"query": clean_query, "count": 0, "results": []}

    candidates = get_all_reports_for_matching()
    matched = match_and_rank_reports(clean_query, candidates, target_type=req.target_type)

    return {
        "query": clean_query,
        "count": len(matched),
        "results": matched
    }

@app.post("/api/contact-requests")
def api_contact_request(req: ContactRequestCreate):
    """
    Safely lodges a claim / contact request without exposing finder/owner's private phone/email.
    """
    report = get_report_by_id(req.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Referenced report was not found.")

    req_id = save_contact_request(
        report_id=req.report_id,
        requester_name=req.requester_name,
        requester_contact=req.requester_contact,
        claim_verification_proof=req.claim_verification_proof,
        message=req.message or ""
    )

    return {
        "success": True,
        "request_id": req_id,
        "message": "Your claim verification request has been safely forwarded to the item custodian."
    }

# Static file serving
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

