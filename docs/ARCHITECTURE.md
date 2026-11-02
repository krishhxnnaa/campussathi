# FindMyCampus Architecture

## Overview
FindMyCampus is a voice-first, privacy-by-design Lost & Found platform built for Sarvam Campus '26.

## System Components

```
[ Browser / Mobile Client ]
   ├── MediaRecorder (Audio capture in WebM / Opus)
   ├── Modern Vanilla SPA (Zero bulky framework overhead)
   └── Responsive Light UI
         │
         │ REST API (JSON / Multipart)
         ▼
[ FastAPI Backend (server/app.py) ]
   ├── Authentication & Rate Limiting Guards
   ├── Sarvam AI Service (server/sarvam_service.py)
   │     ├── Saaras STT (saaras:v3)
   │     ├── Sarvam Conversational Reasoning (sarvam-105b-conversations)
   │     └── Bulbul TTS (bulbul:v3)
   ├── Deterministic Relevance Matcher (server/matcher.py)
   │     └── Synonym & Keyword Normalization (English/Hindi/Hinglish)
   └── SQLite Database (server/database.py)
         ├── Reports Table (with private verification details)
         └── Contact Requests Table (shielded claim workflow)
```

## Data Protection Boundaries
1. **No Public Feed**: The platform does not expose an open catalog. Searching requires a query with a minimum length.
2. **Field Masking**: Results returned to searchers omit phone numbers, email addresses, and private verification details.
3. **Safe Contact Mediation**: Claimants provide proof of ownership which is routed directly to the report custodian without revealing contact information upfront.

