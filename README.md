# Voice Appointment Booking System

A voice-powered appointment booking system for City Clinic. Patients speak to book appointments — no forms needed.

## Live Demo
- **Frontend**: [your-vercel-url]
- **Backend**: https://voice-appointment-booking.onrender.com

## How It Works
1. Open the URL in Chrome/Edge
2. Tap the microphone button
3. Speak your booking request (e.g., "I want to book with Dr. Sharma tomorrow at 10am")
4. The AI will ask for any missing information
5. Once confirmed, you'll receive a calendar invite via email

## Tech Stack
- **Frontend**: HTML + JavaScript + Web Speech API
- **Backend**: FastAPI (Python)
- **LLM**: Groq (Llama 3.3 70B)
- **Scheduling**: Cal.com (open-source)
- **Hosting**: Vercel (frontend) + Render (backend)

## Setup

### Prerequisites
- Python 3.10+
- Groq API key
- Cal.com account + API key

### Local Development
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload --port 8000
```

Then open `frontend/index.html` in Chrome.

### Seed Data
```bash
python seed.py
```

## Available Doctors
- **Dr. Priya Sharma** — General Medicine — Mon-Fri 9AM-5PM
- **Dr. Rahul Patel** — Pediatrics — Mon-Fri 9AM-5PM