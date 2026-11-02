-- ========================================================
-- FindMyCampus / CampusSathi Supabase PostgreSQL Schema
-- Run this in your Supabase Dashboard -> SQL Editor -> Run
-- ========================================================

-- 1. Reports Table
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
    reporter_contact TEXT,               -- Masked from public search results
    status TEXT DEFAULT 'active',        -- 'active', 'matched', 'resolved'
    is_demo INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Contact Requests Table (Safe Contact Mediation)
CREATE TABLE IF NOT EXISTS contact_requests (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    requester_name TEXT NOT NULL,
    requester_contact TEXT NOT NULL,
    claim_verification_proof TEXT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending',       -- 'pending', 'approved', 'declined'
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Indexes for Fast Matching
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
CREATE INDEX IF NOT EXISTS idx_reports_report_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_contact_requests_report_id ON contact_requests(report_id);

-- 4. Row Level Security (RLS) Policies
-- Run these lines to allow your publishable anon key to read and insert reports:
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow anon read-write on reports" ON reports;
CREATE POLICY "Allow anon read-write on reports" ON reports FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anon read-write on contact_requests" ON contact_requests;
CREATE POLICY "Allow anon read-write on contact_requests" ON contact_requests FOR ALL USING (true) WITH CHECK (true);
