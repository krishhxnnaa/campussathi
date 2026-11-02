import os
import re
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("sarvam_service")
logger.setLevel(logging.INFO)

API_KEY = os.getenv("SARVAM_API_KEY")

_client = None

def get_sarvam_client():
    global _client
    if _client is None:
        key = os.getenv("SARVAM_API_KEY")
        if not key or not key.strip():
            raise ValueError("SARVAM_API_KEY is not configured in .env")
        from sarvamai import SarvamAI
        _client = SarvamAI(api_subscription_key=key.strip())
    return _client

def transcribe_audio(file_bytes: bytes, filename: str = "voice_recording.webm") -> Dict[str, Any]:
    """
    Transcribes audio using Sarvam Saaras STT (saaras:v3).
    Supports Indian accents, Hindi, English, and code-mixed speech (Hinglish).
    """
    client = get_sarvam_client()
    try:
        # Determine appropriate content type / extension
        ext = filename.split(".")[-1].lower() if "." in filename else "webm"
        mime_types = {
            "webm": "audio/webm",
            "wav": "audio/wav",
            "mp3": "audio/mp3",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg"
        }
        content_type = mime_types.get(ext, "audio/webm")
        
        response = client.speech_to_text.transcribe(
            file=(filename, file_bytes, content_type),
            model="saaras:v3",
            mode="transcribe",
            language_code="unknown"  # Auto-detect language
        )
        
        transcript_text = getattr(response, "transcript", "")
        detected_language = getattr(response, "language_code", "unknown")
        
        return {
            "success": True,
            "transcript": transcript_text.strip(),
            "language_code": detected_language
        }
    except Exception as e:
        logger.error(f"Error in Saaras STT transcription: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "transcript": ""
        }

VALID_CATEGORIES = [
    "Electronics", "Keys & Cards", "Bags & Wallets", "Books & Stationery",
    "Clothing & Accessories", "Personal Items", "Other"
]

def sanitize_extracted_data(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    
    report_type = str(data.get("reportType", "lost")).strip().lower()
    if report_type not in ["lost", "found"]:
        report_type = "lost"

    category = str(data.get("category", "Other")).strip()
    matched_cat = next((c for c in VALID_CATEGORIES if c.lower() == category.lower()), "Other")

    return {
        "reportType": report_type,
        "itemName": str(data.get("itemName", "") or "").strip()[:150],
        "category": matched_cat,
        "color": str(data.get("color", "") or "").strip()[:50],
        "description": str(data.get("description", "") or "").strip()[:1000],
        "location": str(data.get("location", "") or "").strip()[:150],
        "approximateTime": str(data.get("approximateTime", "") or "").strip()[:100],
        "identifiableAttributes": str(data.get("identifiableAttributes", "") or "").strip()[:500],
        "missingInformation": str(data.get("missingInformation", "") or "").strip()[:300],
        "followUpQuestion": str(data.get("followUpQuestion", "") or "").strip()[:300]
    }

def extract_report_details(user_text: str, current_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Uses Sarvam's conversational reasoning model (sarvam-105b-conversations)
    to extract structured lost/found attributes from natural language.
    Strictly outputs valid JSON with no invented details.
    """
    client = get_sarvam_client()
    
    system_prompt = (
        "You are an AI assistant for FindMyCampus, a college Lost & Found platform.\n"
        "Your task is to analyze the student's description of a lost or found item and extract structured details.\n"
        "STRICT RULES:\n"
        "1. Never invent or hallucinate information that was not mentioned by the user.\n"
        "2. If an attribute is unknown, leave it empty or null.\n"
        "3. Identify any missing key information (e.g. brand, color, exact location, distinguishing features).\n"
        "4. Formulate one short, polite follow-up question if critical details are missing to help identify the item.\n"
        "5. Output ONLY valid JSON in the exact schema below. Do not wrap in conversational text.\n\n"
        "JSON SCHEMA:\n"
        "{\n"
        '  "reportType": "lost" | "found",\n'
        '  "itemName": "concise item title (e.g. Blue Milton Water Bottle)",\n'
        '  "category": "Electronics" | "Keys & Cards" | "Bags & Wallets" | "Books & Stationery" | "Clothing & Accessories" | "Personal Items" | "Other",\n'
        '  "color": "primary color(s)",\n'
        '  "description": "clean summary of physical description",\n'
        '  "location": "campus location mentioned",\n'
        '  "approximateTime": "time or day mentioned",\n'
        '  "identifiableAttributes": "unique marks, stickers, engraving, model number if mentioned",\n'
        '  "missingInformation": "what important detail is still missing",\n'
        '  "followUpQuestion": "one concise question asking for missing info, or empty if description is thorough"\n'
        "}"
    )

    context = f"User description: {user_text}"
    if current_fields:
        context += f"\nPreviously known fields: {json.dumps(current_fields)}"

    try:
        response = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.1
        )
        
        raw_content = response.choices[0].message.content.strip()
        
        # Robust JSON extraction: strip markdown code blocks if present
        clean_json_str = raw_content
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_content)
        if match:
            clean_json_str = match.group(1).strip()
            
        data = json.loads(clean_json_str)
        sanitized_data = sanitize_extracted_data(data)
        return {
            "success": True,
            "data": sanitized_data,
            "raw": raw_content
        }
    except Exception as e:
        logger.error(f"Error in Sarvam extraction: {str(e)}")
        # Graceful fallback: return safe partial struct without crashing
        fallback_data = sanitize_extracted_data({
            "reportType": "lost",
            "itemName": user_text[:60] if user_text else "",
            "category": "Other",
            "color": "",
            "description": user_text,
            "location": "",
            "approximateTime": "",
            "identifiableAttributes": "",
            "missingInformation": "Could not auto-extract fields.",
            "followUpQuestion": "Could you specify the exact location and category?"
        })
        return {
            "success": False,
            "error": str(e),
            "data": fallback_data
        }

def synthesize_speech(text: str, language_code: str = "en-IN") -> Dict[str, Any]:
    """
    Synthesizes speech using Sarvam Bulbul TTS (bulbul:v3).
    Returns base64 encoded audio string.
    """
    try:
        client = get_sarvam_client()
        res = client.text_to_speech.convert(
            text=text[:500],  # Bound length for safety
            language_code=language_code,
            model="bulbul:v3"
        )
        if res.audios and len(res.audios) > 0:
            return {
                "success": True,
                "audio_base64": res.audios[0]
            }
        return {"success": False, "error": "No audio returned"}
    except Exception as e:
        logger.error(f"Error in Bulbul TTS: {str(e)}")
        return {"success": False, "error": str(e)}

