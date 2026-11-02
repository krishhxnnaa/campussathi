# Sarvam AI API Setup & Configuration

## Supported Models & APIs

### 1. Saaras Speech-to-Text (`saaras:v3`)
- **API Method**: `client.speech_to_text.transcribe()`
- **Modes**: `transcribe`, `translate`, `verbatim`, `translit`, `codemix`
- **Languages**: 22 Indic languages + English (with code-mixing support)
- **Input Audio**: WebM, WAV, MP3, AAC, FLAC

### 2. Conversational Reasoning (`sarvam-105b-conversations`)
- **API Method**: `client.chat.completions()`
- **Capabilities**: Structured JSON extraction, ambiguity detection, clarification question generation.
- **Context**: 128k context support with Indic language alignment.

### 3. Bulbul Text-to-Speech (`bulbul:v3`)
- **API Method**: `client.text_to_speech.convert()`
- **Output**: Base64 encoded audio strings for natural Indian voice synthesis.

## Environment Variable Setup
Place your subscription key in `.env`:
```env
SARVAM_API_KEY=sk_your_key_here
```
> **Security Rule:** Never commit `.env` or print the API key in client-side code or logs.

