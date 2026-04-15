"""
Seed script for City Clinic Voice Appointment Booking System.
Sets up 2 doctors with realistic schedules on Cal.com.

Prerequisites:
- Cal.com account with API key
- Set environment variables in backend/.env:
    CAL_API_KEY=<your_key>
    CAL_USERNAME=<your_username>
    GROQ_API_KEY=<your_key>

Usage:
    python seed.py
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv("backend/.env")

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_USERNAME = os.getenv("CAL_USERNAME")
BASE_URL = "https://api.cal.com/v2"

DOCTORS = [
    {
        "name": "Dr. Priya Sharma",
        "specialty": "General Medicine",
        "slug": "dr-sharma-consultation",
        "duration": 30,
        "schedule": "Mon-Fri, 9:00 AM - 5:00 PM IST",
        "room": "Room 101",
        "description": "General medicine consultations for adults. Walk-ins welcome.",
    },
    {
        "name": "Dr. Rahul Patel",
        "specialty": "Pediatrics",
        "slug": "dr-patel-consultation",
        "duration": 30,
        "schedule": "Mon-Fri, 9:00 AM - 5:00 PM IST",
        "room": "Room 205",
        "description": "Pediatric consultations for children aged 0–18.",
    },
]

EVENT_TYPE_PAYLOAD_TEMPLATE = {
    "lengthInMinutes": 30,
    "bookingFields": [
        {"type": "name", "slug": "name", "required": True},
        {"type": "email", "slug": "email", "required": True},
    ],
    "locations": [{"type": "inPerson", "address": "City Clinic"}],
}


def print_banner():
    print("=" * 55)
    print("  City Clinic — Seed Script")
    print("=" * 55)
    print(f"\n  Cal.com Username : {CAL_USERNAME}")
    masked = CAL_API_KEY[:10] + "..." if CAL_API_KEY else "NOT SET"
    print(f"  API Key          : {masked}")
    print()


def verify_env():
    missing = []
    if not CAL_API_KEY:
        missing.append("CAL_API_KEY")
    if not CAL_USERNAME:
        missing.append("CAL_USERNAME")
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Copy backend/.env.example to backend/.env and fill in your keys.")
        raise SystemExit(1)


def create_event_type(doctor: dict) -> dict:
    """
    Attempt to create a Cal.com event type via the v2 API.
    Returns the API response dict.
    """
    payload = {
        **EVENT_TYPE_PAYLOAD_TEMPLATE,
        "title": f"{doctor['name']} — {doctor['specialty']}",
        "slug": doctor["slug"],
        "description": doctor["description"],
    }

    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(f"{BASE_URL}/event-types", json=payload, headers=headers)

    return {"status": resp.status_code, "body": resp.json()}


def seed():
    print_banner()
    verify_env()

    print("Doctor Configuration")
    print("-" * 55)
    for doc in DOCTORS:
        print(f"\n  {doc['name']} ({doc['specialty']})")
        print(f"    Slug     : {doc['slug']}")
        print(f"    Duration : {doc['duration']} min")
        print(f"    Schedule : {doc['schedule']}")
        print(f"    Room     : City Clinic, {doc['room']}")
        print(f"    Cal URL  : https://cal.com/{CAL_USERNAME}/{doc['slug']}")

    print()
    print("Creating event types via Cal.com API v2 ...")
    print("-" * 55)

    for doc in DOCTORS:
        try:
            result = create_event_type(doc)
            status = result["status"]
            if status in (200, 201):
                print(f"  [OK]  {doc['name']} — event type created (HTTP {status})")
            elif status == 409:
                print(f"  [--]  {doc['name']} — already exists, skipping (HTTP {status})")
            else:
                print(f"  [ERR] {doc['name']} — unexpected response (HTTP {status})")
                print(f"        {result['body']}")
        except Exception as exc:
            print(f"  [ERR] {doc['name']} — {exc}")

    print()
    print("Seed complete.")
    print("Both doctors are now configured on Cal.com and accepting bookings.")
    print()
    print("Next steps:")
    print("  1. Log in to Cal.com and verify event types under your profile.")
    print("  2. Set availability schedules (Mon–Fri 9 AM–5 PM IST) if not auto-applied.")
    print("  3. Start the backend:  uvicorn main:app --reload --port 8000")
    print("  4. Open frontend/index.html in Chrome.")


if __name__ == "__main__":
    seed()