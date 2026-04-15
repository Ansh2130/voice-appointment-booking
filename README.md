# Voice Appointment Booking System

A voice-powered appointment booking system for City Clinic. Patients speak naturally to book appointments — no forms, no login, no app install required.

## Live Demo

- **Frontend**: [your-vercel-url]
- **Backend**: https://voice-appointment-booking.onrender.com

> **Note:** The Render free tier spins down after 15 minutes of inactivity. The first request may take ~50 seconds to wake up. Subsequent requests are fast.

---

## How It Works

1. Open the URL in **Chrome or Edge** (Web Speech API required)
2. Tap the **microphone button**
3. Speak naturally — e.g. *"I want to see Dr. Sharma tomorrow at 10am"*
4. The AI asks for any missing info (doctor, date, time, name, email)
5. Once everything is confirmed, your appointment is booked and a **calendar invite** is sent to your email

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML + JavaScript + Web Speech API |
| Backend | FastAPI (Python 3.10+) |
| LLM | Groq — Llama 3.3 70B |
| Scheduling | Cal.com v2 API |
| Hosting (frontend) | Vercel |
| Hosting (backend) | Render |

---

## Available Doctors

| Doctor | Specialty | Hours |
|---|---|---|
| Dr. Priya Sharma | General Medicine | Mon–Fri, 9 AM – 5 PM IST |
| Dr. Rahul Patel | Pediatrics | Mon–Fri, 9 AM – 5 PM IST |

---

## Local Setup

### Prerequisites

- Python 3.10+
- A Groq API key — [console.groq.com](https://console.groq.com)
- A Cal.com account + API key — [cal.com](https://cal.com)
- Chrome or Edge (for voice input)

### 1. Clone & install dependencies

```bash
git clone <your-repo-url>
cd backend
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=your_groq_key_here
CAL_API_KEY=your_cal_api_key_here
CAL_USERNAME=your_cal_username_here
```

### 3. Seed Cal.com with doctor event types

```bash
python seed.py
```

This creates two event types on Cal.com (`dr-sharma-consultation` and `dr-patel-consultation`). If they already exist, the script skips them safely.

### 4. Start the backend

```bash
uvicorn main:app --reload --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Open the frontend

Open `frontend/index.html` directly in Chrome or Edge.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a chat message, get AI reply |
| `GET` | `/api/doctors` | List available doctors |
| `GET` | `/health` | Health check |

### POST `/api/chat`

**Request:**
```json
{
  "session_id": "abc123",
  "message": "I want to book with Dr. Sharma"
}
```

**Response:**
```json
{
  "reply": "Sure! What date works for you?",
  "booking_confirmed": false,
  "booking_details": null
}
```

---

## Project Structure

```
.
├── backend/
│   ├── main.py           # FastAPI app, conversation logic, booking flow
│   ├── cal_service.py    # Cal.com API integration (slots + bookings)
│   ├── seed.py           # One-time setup script for Cal.com event types
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── index.html        # Single-file voice UI
├── DECISIONS.md          # Architecture decisions and tradeoffs
└── README.md
```

---

## Known Limitations

- **Chrome / Edge only** — Web Speech API is not supported in Firefox or Safari
- **Email via speech** — Hard to dictate accurately; a text fallback input is provided below the mic button
- **Single Cal.com user** — Free plan supports one user; both doctors are simulated as separate event types under one account
- **In-memory sessions** — Conversation state is lost if the backend restarts
- **Cold starts** — Render free tier may take ~50 seconds on first request after inactivity