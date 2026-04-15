from dotenv import load_dotenv
load_dotenv()
import httpx
import os

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_USERNAME = os.getenv("CAL_USERNAME")
BASE_URL = "https://api.cal.com/v2"

print(f"DEBUG CAL_USERNAME: {CAL_USERNAME}")
print(f"DEBUG CAL_API_KEY: {CAL_API_KEY[:10]}..." if CAL_API_KEY else "DEBUG CAL_API_KEY: None")

DOCTORS = {
    "dr. sharma": {
        "slug": "dr-sharma-consultation",
        "name": "Dr. Priya Sharma",
        "specialty": "General Medicine",
    },
    "dr. patel": {
        "slug": "dr-patel-consultation",
        "name": "Dr. Rahul Patel",
        "specialty": "Pediatrics",
    },
}


async def get_available_slots(doctor_key: str, date_str: str):
    """Get available slots for a doctor on a given date."""
    doctor = DOCTORS.get(doctor_key)
    if not doctor:
        return {"error": "Doctor not found"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/slots",
            params={
                "username": CAL_USERNAME,
                "eventTypeSlug": doctor["slug"],
                "start": date_str,
                "end": date_str,
                "timeZone": "Asia/Kolkata",
            },
            headers={
                "Authorization": f"Bearer {CAL_API_KEY}",
                "cal-api-version": "2024-09-04",
            },
        )

    print(f"DEBUG SLOTS STATUS: {resp.status_code}")
    print(f"DEBUG SLOTS RESPONSE: {resp.text[:500]}")

    if resp.status_code == 200:
        return resp.json().get("data", {})
    return {"error": resp.text}


async def book_appointment(doctor_key: str, start_time: str, patient_name: str, patient_email: str):
    """Book an appointment with a doctor."""
    doctor = DOCTORS.get(doctor_key)
    if not doctor:
        return {"error": "Doctor not found"}

    payload = {
        "eventTypeSlug": doctor["slug"],
        "username": CAL_USERNAME,
        "start": start_time,
        "attendee": {
            "name": patient_name,
            "email": patient_email,
            "timeZone": "Asia/Kolkata",
        },
        "location": "City Clinic",
    }

    print(f"DEBUG BOOKING PAYLOAD: {payload}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/bookings",
            json=payload,
            headers={
                "Authorization": f"Bearer {CAL_API_KEY}",
                "cal-api-version": "2024-08-13",
                "Content-Type": "application/json",
            },
        )

    print(f"DEBUG BOOKING STATUS: {resp.status_code}")
    print(f"DEBUG BOOKING RESPONSE: {resp.text[:500]}")

    if resp.status_code in [200, 201]:
        return {"success": True, "data": resp.json()}
    return {"error": resp.text}