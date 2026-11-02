# Security & Privacy Specification

## Core Principles

1. **No Public Feed / Anti-Scraping**:
   - There is no endpoint that lists all lost or found items without a specific search query.
   - Database dumps to the client are strictly prevented.

2. **Data Minimization & Field Shielding**:
   - `private_verification_details`, `reporter_contact`, and `reporter_name` are never returned in search responses.
   - Search responses contain only sanitized public display fields.

3. **Confidential Ownership Verification**:
   - Reporters can specify confidential verification details (e.g., engraving, lock-screen wallpaper, serial numbers, specific card details).
   - Claimants must provide proof before contact info is shared.

4. **Input Sanitization & Abuse Protection**:
   - Uploaded photos are strictly validated for MIME type (`image/png`, `image/jpeg`, `image/webp`) and capped at 5MB.
   - Audio files are limited to 10MB.
   - Deduplication guards prevent rapid duplicate report submissions.

5. **Server-Side AI Secrets**:
   - All calls to Sarvam AI originate from the Python backend. The client browser never receives or handles the API key.

