# DECISIONS.md

## What I Built
A browser-based voice appointment booking system for a small clinic. Patients open a URL, speak naturally, and book appointments with doctors — no forms, no login, no app install.

## Architecture
Browser (Voice UI) <---> FastAPI Backend <---> Groq LLM + Cal.com API
|                        |
Web Speech API         Conversation
(STT + TTS)           State Manager

### Components
- **Frontend**: Single HTML file with Web Speech API for voice input/output
- **Backend**: FastAPI (Python) handling conversation logic and Cal.com integration
- **LLM**: Groq (Llama 3.3 70B) for natural language understanding and intent extraction
- **Scheduling**: Cal.com (open-source) for availability, booking, and calendar invites

## Key Decisions

### 1. Web Speech API over Deepgram/ElevenLabs
- **Why**: Free, no API key needed, works natively in Chrome/Edge
- **Tradeoff**: Only works in Chromium browsers. Acceptable for a demo — Chrome has 65%+ market share

### 2. Cal.com (cloud) over self-hosted
- **Why**: Free tier has unlimited bookings, built-in calendar invites, prevents double-booking automatically. 6-hour constraint made self-hosting impractical
- **Tradeoff**: Limited to one Cal.com user on free plan. Simulated 2 doctors using 2 event types under one account

### 3. Groq over OpenAI
- **Why**: Free tier, very fast inference (~200ms), sufficient for conversational booking
- **Tradeoff**: Llama 3.3 occasionally outputs double curly braces in JSON — handled with string sanitization

### 4. FastAPI over Node.js/Express
- **Why**: Faster development speed for me, native async support, auto-generated Swagger docs for testing
- **Tradeoff**: None significant — both would work fine

### 5. Single HTML file over React
- **Why**: No build step, instant deployment on Vercel, simpler debugging
- **Tradeoff**: Less scalable for a production app, but ideal for this scope

### 6. In-memory session state over database
- **Why**: Simplicity. Each conversation is short-lived. No persistent state needed
- **Tradeoff**: Sessions lost on server restart. Acceptable for demo

## How Conflicts Are Handled
- **Double booking**: Cal.com automatically removes booked slots from availability
- **Doctor on leave**: Cal.com respects schedule/availability settings
- **Slot not available**: System offers alternative available times
- **Weekend booking**: LLM prompt instructs to reject weekends
- **Past dates**: LLM prompt includes today's date for correct resolution
- **Garbled speech**: Text fallback input available below the mic

## What I Chose Not to Build
- **Authentication/login**: Not required — evaluator opens URL cold
- **Appointment cancellation/rescheduling**: Out of scope for 6-hour window
- **Multi-language support**: English only for demo
- **SMS notifications**: Email calendar invite covers the requirement
- **Persistent database**: In-memory sessions sufficient for demo

## Hosting & Free Tier Limits
| Service | Free Tier Limit | Impact |
|---------|----------------|--------|
| Render (backend) | 750 hours/month, spins down after 15 min inactivity | First request may take ~50s to wake up |
| Vercel (frontend) | 100GB bandwidth | No impact for demo |
| Groq | 30 requests/min | Sufficient for demo |
| Cal.com | Unlimited bookings, 1 user | Simulated 2 doctors as event types |

## Known Limitations
- Web Speech API requires Chrome or Edge (no Firefox/Safari)
- Render free tier cold starts (~50 seconds on first request)
- Speech recognition can merge words when user speaks fast (e.g., name + email together)
- Email addresses are hard to capture via speech — added text input as fallback

### Components
- **Frontend**: Single HTML file with Web Speech API for voice input/output
- **Backend**: FastAPI (Python) handling conversation logic and Cal.com integration
- **LLM**: Groq (Llama 3.3 70B) for natural language understanding and intent extraction
- **Scheduling**: Cal.com (open-source) for availability, booking, and calendar invites

## Key Decisions

### 1. Web Speech API over Deepgram/ElevenLabs
- **Why**: Free, no API key needed, works natively in Chrome/Edge
- **Tradeoff**: Only works in Chromium browsers. Acceptable for a demo — Chrome has 65%+ market share

### 2. Cal.com (cloud) over self-hosted
- **Why**: Free tier has unlimited bookings, built-in calendar invites, prevents double-booking automatically. 6-hour constraint made self-hosting impractical
- **Tradeoff**: Limited to one Cal.com user on free plan. Simulated 2 doctors using 2 event types under one account

### 3. Groq over OpenAI
- **Why**: Free tier, very fast inference (~200ms), sufficient for conversational booking
- **Tradeoff**: Llama 3.3 occasionally outputs double curly braces in JSON — handled with string sanitization

### 4. FastAPI over Node.js/Express
- **Why**: Faster development speed for me, native async support, auto-generated Swagger docs for testing
- **Tradeoff**: None significant — both would work fine

### 5. Single HTML file over React
- **Why**: No build step, instant deployment on Vercel, simpler debugging
- **Tradeoff**: Less scalable for a production app, but ideal for this scope

### 6. In-memory session state over database
- **Why**: Simplicity. Each conversation is short-lived. No persistent state needed
- **Tradeoff**: Sessions lost on server restart. Acceptable for demo

## How Conflicts Are Handled
- **Double booking**: Cal.com automatically removes booked slots from availability
- **Doctor on leave**: Cal.com respects schedule/availability settings
- **Slot not available**: System offers alternative available times
- **Weekend booking**: LLM prompt instructs to reject weekends
- **Past dates**: LLM prompt includes today's date for correct resolution
- **Garbled speech**: Text fallback input available below the mic

## What I Chose Not to Build
- **Authentication/login**: Not required — evaluator opens URL cold
- **Appointment cancellation/rescheduling**: Out of scope for 6-hour window
- **Multi-language support**: English only for demo
- **SMS notifications**: Email calendar invite covers the requirement
- **Persistent database**: In-memory sessions sufficient for demo

## Hosting & Free Tier Limits
| Service | Free Tier Limit | Impact |
|---------|----------------|--------|
| Render (backend) | 750 hours/month, spins down after 15 min inactivity | First request may take ~50s to wake up |
| Vercel (frontend) | 100GB bandwidth | No impact for demo |
| Groq | 30 requests/min | Sufficient for demo |
| Cal.com | Unlimited bookings, 1 user | Simulated 2 doctors as event types |

## Known Limitations
- Web Speech API requires Chrome or Edge (no Firefox/Safari)
- Render free tier cold starts (~50 seconds on first request)
- Speech recognition can merge words when user speaks fast (e.g., name + email together)
- Email addresses are hard to capture via speech — added text input as fallback