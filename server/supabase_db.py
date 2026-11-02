import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")))

_client = None

def get_supabase_client():
    """Lazily initializes and returns the Supabase client."""
    global _client
    if _client is not None:
        return _client
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Supabase credentials missing. Please set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY) in your .env file."
        )

    try:
        from supabase import create_client, Client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Supabase client: {str(e)}")


def test_connection() -> Dict[str, Any]:
    """Tests the connection to Supabase and reports status."""
    try:
        client = get_supabase_client()
        res = client.table("reports").select("id").limit(1).execute()
        return {"success": True, "message": "Successfully connected to Supabase PostgreSQL database."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def init_supabase_db():
    """Verifies connection and seeds initial demo records if table is empty."""
    try:
        client = get_supabase_client()
        res = client.table("reports").select("id").eq("is_demo", 1).execute()
        if not res.data or len(res.data) == 0:
            seed_supabase_demo_data()
    except Exception as e:
        print(f"[Supabase Warning] Could not verify/seed demo data: {e}")


def seed_supabase_demo_data():
    """Seeds starter records into the Supabase reports table."""
    client = get_supabase_client()
    demo_items = [
        {
            "id": "FMC-DEMO-001",
            "report_type": "found",
            "item_name": "Titan Neo Wrist Watch",
            "category": "Clothing & Accessories",
            "color": "Black",
            "description": "Black metallic analog watch found on study desk near Central Library 2nd floor reading hall.",
            "location": "Central Library, 2nd Floor",
            "approximate_time": "Yesterday around 5:00 PM",
            "image_path": None,
            "private_verification_details": "Scratch mark near clasp; back engraving says 'Titan Water Resistant 50M'.",
            "reporter_name": "Library Staff (Front Desk)",
            "reporter_contact": "library-lostfound@campus.edu",
            "is_demo": 1,
            "created_at": "2026-11-01T17:30:00Z"
        },
        {
            "id": "FMC-DEMO-002",
            "report_type": "found",
            "item_name": "Milton Insulated Water Bottle",
            "category": "Personal Items",
            "color": "Blue",
            "description": "Dark blue 750ml stainless steel Milton water bottle with sports cap found near dining table.",
            "location": "Hostel 3 Mess Dining Hall",
            "approximate_time": "Today morning at breakfast (8:30 AM)",
            "image_path": None,
            "private_verification_details": "Dented bottom edge and a small mountain sticker on lid.",
            "reporter_name": "Hostel 3 Mess Representative",
            "reporter_contact": "h3-council@campus.edu",
            "is_demo": 1,
            "created_at": "2026-11-02T09:00:00Z"
        },
        {
            "id": "FMC-DEMO-003",
            "report_type": "found",
            "item_name": "Apple AirPods Pro (2nd Gen)",
            "category": "Electronics",
            "color": "White",
            "description": "Found white AirPods Pro charging case with earbuds inside near Row 4 seats.",
            "location": "Seminar Room 102, Academic Block A",
            "approximate_time": "Nov 2, 11:15 AM",
            "image_path": None,
            "private_verification_details": "Small dinosaur sticker on backside; AirPods name on Bluetooth is 'Aryan's AirPods'.",
            "reporter_name": "Dr. Sharma (Faculty)",
            "reporter_contact": "faculty.office@campus.edu",
            "is_demo": 1,
            "created_at": "2026-11-02T11:30:00Z"
        },
        {
            "id": "FMC-DEMO-004",
            "report_type": "lost",
            "item_name": "Black Leather Bi-fold Wallet",
            "category": "Bags & Wallets",
            "color": "Black",
            "description": "WildHorn black leather bi-fold wallet lost while walking back from the main cafeteria.",
            "location": "Path between Main Gate & SAC",
            "approximate_time": "Today around 1:30 PM",
            "image_path": None,
            "private_verification_details": "Contains Campus ID ending in 4492, Metro card, and roughly Rs. 400 cash.",
            "reporter_name": "Rahul Verma",
            "reporter_contact": "+91-98765-43210",
            "is_demo": 1,
            "created_at": "2026-11-02T13:45:00Z"
        },
        {
            "id": "FMC-DEMO-005",
            "report_type": "found",
            "item_name": "Casio fx-991EX ClassWiz Scientific Calculator",
            "category": "Books & Stationery",
            "color": "Black & White",
            "description": "Scientific calculator left on workstation 14 after engineering physics practicals.",
            "location": "Physics Lab 3, Science Block",
            "approximate_time": "Oct 31, 4:45 PM",
            "image_path": None,
            "private_verification_details": "White correction fluid initials 'KV' marked on sliding cover interior.",
            "reporter_name": "Lab Assistant Mukesh",
            "reporter_contact": "physics-lab@campus.edu",
            "is_demo": 1,
            "created_at": "2026-10-31T18:00:00Z"
        },
        {
            "id": "FMC-DEMO-006",
            "report_type": "found",
            "item_name": "HP Laptop Power Adapter (65W USB-C)",
            "category": "Electronics",
            "color": "Black",
            "description": "Black HP USB-C charger left plugged into the wall socket in Study Hall Room 204.",
            "location": "Study Hall Room 204, Library Wing",
            "approximate_time": "Yesterday night around 9:30 PM",
            "image_path": None,
            "private_verification_details": "Red electrical tape wrapped near the USB-C connector pin.",
            "reporter_name": "Night Security Guard",
            "reporter_contact": "security@campus.edu",
            "is_demo": 1,
            "created_at": "2026-11-01T22:00:00Z"
        }
    ]

    for item in demo_items:
        try:
            client.table("reports").upsert(item).execute()
        except Exception as e:
            print(f"[Supabase Seed Warning] Error inserting demo item {item['id']}: {e}")


def save_report(data: dict) -> str:
    """Inserts a new lost/found report into Supabase."""
    client = get_supabase_client()
    report_id = f"FMC-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    record = {
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    client.table("reports").insert(record).execute()
    return report_id


def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single report record by ID."""
    client = get_supabase_client()
    res = client.table("reports").select("*").eq("id", report_id).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None


def get_all_reports_for_matching() -> List[Dict[str, Any]]:
    """Returns active records for the backend matcher."""
    client = get_supabase_client()
    res = client.table("reports").select("*").eq("status", "active").order("created_at", desc=True).execute()
    return res.data or []


def save_contact_request(
    report_id: str,
    requester_name: str,
    requester_contact: str,
    claim_verification_proof: str,
    message: str
) -> str:
    """Inserts a shielded contact request into Supabase."""
    client = get_supabase_client()
    req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

    record = {
        "id": req_id,
        "report_id": report_id,
        "requester_name": requester_name,
        "requester_contact": requester_contact,
        "claim_verification_proof": claim_verification_proof,
        "message": message or "",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    client.table("contact_requests").insert(record).execute()
    return req_id
