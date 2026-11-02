# AI Workflows & Prompt Engineering

## 1. Voice Report Extraction Workflow
1. User records audio or speaks description in Hindi, English, or Hinglish.
2. Saaras STT transcribes the audio into normalized text.
3. Transcript is shown to user for immediate review or correction.
4. Sarvam's `sarvam-105b-conversations` reasoning model parses the text with a strict system prompt:
   - Identifies item name, category, color, location, and time.
   - Detects missing attributes.
   - Formulates a single polite clarification question.
5. User edits any auto-extracted fields and adds an optional photo or private verification notes.
6. User explicitly clicks "Confirm & Publish". No report is ever published automatically.

## 2. Voice & Text Search Workflow
1. User provides a natural language query via voice or keyboard (e.g. "Titan watch library" or "hostel 3 blue water bottle").
2. Query tokens are normalized across Indic synonyms (e.g., *ghadi* -> *watch*, *botol* -> *bottle*).
3. Backend relevance matcher evaluates candidate reports with weighted scoring.
4. Non-matching candidates (<25% score) are rejected to eliminate false positives.
5. Top matches are returned with plain-text match explanations.

