"""
Standalone script to verify Supabase connection.
Run with: python server/test_supabase.py
"""
import sys
import os

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.supabase_db import test_connection, init_supabase_db, get_all_reports_for_matching

def main():
    print("Testing Supabase PostgreSQL Connection...")
    res = test_connection()
    if res.get("success"):
        print("[SUCCESS]", res["message"])
        print("\nSeeding demo data if empty...")
        init_supabase_db()
        items = get_all_reports_for_matching()
        print(f"[SUCCESS] Found {len(items)} active reports in Supabase!")
        for item in items[:3]:
            print(f"   - [{item.get('report_type')}] {item.get('item_name')} ({item.get('location')})")
    else:
        print("[ERROR] Connection failed:")
        print("  ", res.get("error"))
        print("\nMake sure you have added these to your .env file:")
        print("SUPABASE_URL=https://your-project-id.supabase.co")
        print("SUPABASE_KEY=your_supabase_anon_or_service_role_key")

if __name__ == "__main__":
    main()
