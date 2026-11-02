# FindMyCampus — Sarvam AI Voice-First Lost & Found

Built for **Sarvam Campus '26**, FindMyCampus transforms the traditional campus lost & found board into an intuitive, voice-first AI workflow powered by **Sarvam AI**.

---

## 🌟 Key Features

1. **🎙️ Voice-First Reporting (Sarvam Saaras STT)**:
   - Speak naturally in English, Hindi, or Hinglish.
   - Live transcription with in-place user editing.
2. **🧠 Conversational Reasoning (Sarvam-105B-Conversations)**:
   - Automatically extracts item name, category, color, location, and time.
   - Detects missing attributes and asks concise follow-up questions.
3. **🔊 Audio Clarification (Sarvam Bulbul TTS)**:
   - Optional speech synthesis to listen to AI clarification questions.
4. **🔒 Privacy-By-Design & Anti-Scraping**:
   - **No public browsing feed**: Searching is strictly intent-driven.
   - **Data minimization**: Personal contact details and private verification marks are masked from search results.
   - **Safe Contact Workflow**: Claimants submit proof of ownership before contact details are mediated.
5. **🎯 Deterministic Relevance Matching**:
   - Attribute and synonym-aware ranking (English & Indic vocabulary).
   - Shows genuine match evidence without fake scores or hallucinated records.

---

## 🚀 Quickstart & Run Instructions

### 1. Requirements
- Python 3.10+
- Installed packages: `fastapi`, `uvicorn`, `sarvamai`, `python-dotenv`, `python-multipart`

### 2. Environment Setup
Configure your API key in `.env`:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```

### 3. Launch the Application
```bash
python run.py
```
Open your browser to: **http://127.0.0.1:8000**

---

## 📂 Project Structure

```
├── server/
│   ├── app.py             # FastAPI backend with REST endpoints & rate limits
│   ├── database.py        # SQLite persistence layer with realistic demo data
│   ├── matcher.py         # Relevance ranking and attribute matcher
│   └── sarvam_service.py  # Sarvam AI SDK integration (Saaras STT, 105B Reasoning, Bulbul TTS)
├── static/
│   ├── index.html         # Mobile-first light UI
│   ├── styles.css         # Modern styling & animations
│   └── app.js             # Client SPA logic & audio recording via MediaRecorder
├── docs/                  # Architecture, API setup, Security, and Testing specifications
├── uploads/               # Verified user image storage
├── main.py                # Standalone SDK verification script
├── run.py                 # Application launcher
└── .env                   # Environment secrets (ignored by git)
```
