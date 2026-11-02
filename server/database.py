import sqlite3
import os
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

DB_PATH = os.path.join(os.path.dirname(__file__), "findmycampus.db")

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if url and key and url.strip() and key.strip():
        try:
            from supabase import create_client
            _supabase_client = create_client(url.strip(), key.strip())
            logger.info("Connected to Supabase successfully!")
            return _supabase_client
        except Exception as e:
            logger.error(f"Could not initialize Supabase client: {e}")
            return None
    return None

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        report_type TEXT NOT NULL,           -- 'lost' or 'found'
        item_name TEXT NOT NULL,
        category TEXT NOT NULL,
        color TEXT,
        description TEXT NOT NULL,
        location TEXT NOT NULL,
        approximate_time TEXT,
        image_path TEXT,
        private_verification_details TEXT,  -- Masked from public search results
        reporter_name TEXT,
        reporter_contact TEXT,               -- Masked from search
        status TEXT DEFAULT 'active',        -- 'active', 'matched', 'resolved'
        is_demo INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_requests (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        requester_name TEXT NOT NULL,
        requester_contact TEXT NOT NULL,
        claim_verification_proof TEXT NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports (id)
    );
    """)

    # Purge any remaining fake demo rows
    cursor.execute("DELETE FROM reports WHERE is_demo = 1")
    conn.commit()
    conn.close()

def save_report(data: dict) -> str:
    report_id = f"FMC-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    report_dict = {
        "id": report_id,
        "report_type": data.get("report_type", "lost"),
        "item_name": data.get("item_name", "Unnamed Item").strip(),
        "category": data.get("category", "Other"),
        "color": data.get("color", ""),
        "description": data.get("description", "").strip(),
        "location": data.get("location", "").strip(),
        "approximate_time": data.get("approximate_time", ""),
        "image_path": data.get("image_path"),
        "private_verification_details": data.get("private_verification_details", ""),
        "reporter_name": data.get("reporter_name", "Anonymous Student"),
        "reporter_contact": data.get("reporter_contact", ""),
        "status": "active",
        "is_demo": 0,
        "created_at": now_iso
    }

    # 1. Sync to Supabase if configured
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("reports").insert(report_dict).execute()
            logger.info(f"Synced report {report_id} to Supabase")
        except Exception as e:
            logger.warning(f"Supabase sync warning: {e}. Note: If RLS is enabled in Supabase, run docs/supabase_schema.sql to allow anon inserts.")

    # 2. Local persistence
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reports (
        id, report_type, item_name, category, color, description,
        location, approximate_time, image_path, private_verification_details,
        reporter_name, reporter_contact, status, is_demo, created_at
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, ?
    )
    """, (
        report_id,
        report_dict["report_type"],
        report_dict["item_name"],
        report_dict["category"],
        report_dict["color"],
        report_dict["description"],
        report_dict["location"],
        report_dict["approximate_time"],
        report_dict["image_path"],
        report_dict["private_verification_details"],
        report_dict["reporter_name"],
        report_dict["reporter_contact"],
        now_iso
    ))
    conn.commit()
    conn.close()

    return report_id

def get_report_by_id(report_id: str):
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("reports").select("*").eq("id", report_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Supabase get_report_by_id error: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_reports_for_matching():
    """
    Returns active records for the backend matcher.
    Queries Supabase first; if Supabase returns records, uses them.
    If Supabase is empty or returns an error, checks local SQLite database.
    Zero fake demo data.
    """
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("reports").select("*").eq("status", "active").order("created_at", desc=True).execute()
            if res.data and len(res.data) > 0:
                return res.data
        except Exception as e:
            logger.error(f"Supabase fetch error: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE status = 'active' AND is_demo = 0 ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def save_contact_request(report_id: str, requester_name: str, requester_contact: str, claim_verification_proof: str, message: str) -> str:
    req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    claim_dict = {
        "id": req_id,
        "report_id": report_id,
        "requester_name": requester_name,
        "requester_contact": requester_contact,
        "claim_verification_proof": claim_verification_proof,
        "message": message or "",
        "status": "pending",
        "created_at": now_iso
    }

    sb = get_supabase_client()
    if sb:
        try:
            sb.table("contact_requests").insert(claim_dict).execute()
            logger.info(f"Synced claim request {req_id} to Supabase")
        except Exception as e:
            logger.warning(f"Supabase claim sync warning: {e}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO contact_requests (
        id, report_id, requester_name, requester_contact,
        claim_verification_proof, message, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        req_id, report_id, requester_name, requester_contact,
        claim_verification_proof, message, now_iso
    ))
    conn.commit()
    conn.close()
    return req_id

def sync_local_to_supabase():
    sb = get_supabase_client()
    if not sb:
        return {"synced": 0, "error": "Supabase client not configured"}
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE is_demo = 0")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    synced_count = 0
    for r in rows:
        try:
            sb.table("reports").upsert(r).execute()
            synced_count += 1
        except Exception as e:
            logger.warning(f"Could not sync {r['id']} to Supabase: {e}")
            
    return {"synced": synced_count, "total": len(rows)}
