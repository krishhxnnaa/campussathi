# Testing & Verification Guide

## Test Scenarios

### 1. Voice Reporting (Saaras STT + Reasoning)
- **Action**: Click "Report a Lost Item", select "🎙️ Speak Description", tap mic, say:
  `"I lost my blue Milton water bottle near Hostel 3 mess dining hall this morning."`
- **Expected Outcome**:
  - Audio transcribes cleanly.
  - Sarvam model extracts:
    - Item Name: "Milton water bottle"
    - Color: "Blue"
    - Location: "Hostel 3 mess dining hall"
    - Category: "Personal Items"
  - Follow-up question asks about distinguishing marks or size.

### 2. Text Search & Relevance Matching
- **Action**: Search for `"Titan watch library"`.
- **Expected Outcome**:
  - Matches `FMC-DEMO-001` with high relevance score.
  - Displays match evidence: `"Item name matches: watch • Color match: Black • Location match: library"`.
  - Sensitive details (e.g. scratch mark on clasp) are NOT shown.

### 3. No-Match Query Verification
- **Action**: Search for `"Green guitar amplifier"`.
- **Expected Outcome**:
  - Zero results returned with a clean "No matching items found" state.
  - No random or irrelevant items are surfaced.

### 4. Safe Contact Claim Submission
- **Action**: Click "Claim / Contact Finder" on any search result.
- **Expected Outcome**:
  - Modal opens with summary.
  - Claimant submits proof of ownership.
  - Request ID is generated and securely saved to `contact_requests`.

