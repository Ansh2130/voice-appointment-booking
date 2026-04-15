from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
from groq import Groq
from cal_service import get_available_slots, book_appointment, DOCTORS
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# In-memory conversation state per session
sessions = {}

SYSTEM_PROMPT = """You are a friendly voice receptionist AI for City Clinic. You are having a real-time voice conversation with a patient. Be natural, warm, and conversational — like a real receptionist on a phone call.

Available doctors:
- Dr. Priya Sharma: General Medicine (Mon-Fri, 9 AM - 5 PM)
- Dr. Rahul Patel: Pediatrics (Mon-Fri, 9 AM - 5 PM)

You need to collect ALL of the following before booking:
1. Doctor name (Sharma or Patel)
2. Preferred date
3. Preferred time
4. Patient's full name
5. Patient's email address

Rules:
- Today's date is {today}.
- If user says "tomorrow", calculate the actual date.
- If user says a weekday name, calculate the next occurrence.
- The clinic is closed on weekends (Saturday & Sunday). If user picks a weekend, say "The clinic is closed on weekends. How about Monday instead?"
- If user picks a past date, say "That date has already passed. Could you pick a future date?"
- Slot duration is 30 minutes.
- Keep responses SHORT — 1 to 2 sentences max. You are on a voice call, not writing an essay.
- Ask for information ONE AT A TIME. Never ask two things at once.
- Ask in this order: doctor → date → time → name → email.
- When asking for email, say "What's your email address? Please say it slowly."
- After user says their email, REPEAT it back and ask "Did I get that right?" before proceeding.
- If user says "yes" or "no", understand it based on your last question.
- If user says "cancel", "stop", "never mind", or "start over", say "No problem! Let's start fresh. Which doctor would you like to see?"
- If user seems confused or says "I don't know", help them: "No worries! We have Dr. Sharma for General Medicine and Dr. Patel for Pediatrics. Which sounds right for you?"
- If user says something unrelated, gently redirect: "I'd love to help with that, but I'm best at booking appointments. Would you like to book one?"
- If user gives incomplete info like just a first name, ask for full name.
- When you have ALL 5 pieces of info confirmed, respond with ONLY the ACTION block and nothing else:

ACTION: {{"action": "check_availability", "doctor": "dr. sharma", "date": "2026-04-16", "time": "15:00", "patient_name": "John Doe", "patient_email": "john@example.com"}}

- IMPORTANT: Use 24-hour time format (e.g., 15:00 for 3 PM, 09:00 for 9 AM).
- IMPORTANT: The doctor value must be exactly "dr. sharma" or "dr. patel" (lowercase).
- IMPORTANT: Date format must be YYYY-MM-DD.
- Only output the ACTION when you have ALL 5 pieces of info AND user confirmed email.
- Do NOT add any text before or after the ACTION line.
"""
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    booking_confirmed: bool = False
    booking_details: dict = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Init session
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id]
    history.append({"role": "user", "content": req.message})

    today = datetime.now().strftime("%A, %B %d, %Y")
    system = SYSTEM_PROMPT.replace("{today}", today)

    # Call Groq
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system}] + history,
        temperature=0.3,
        max_tokens=500,
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    print(f"DEBUG LLM Reply: {reply}")

    # Check if LLM wants to take action
    if "ACTION:" in reply:
        try:
            action_str = reply.split("ACTION:")[1].strip()
            # Clean up — find the JSON object boundaries
            start_idx = action_str.index("{")
            brace_count = 0
            end_idx = start_idx
            for i, ch in enumerate(action_str[start_idx:], start_idx):
                if ch == "{":
                    brace_count += 1
                elif ch == "}":
                    brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
            action_str = action_str[start_idx:end_idx + 1]
            action_str = action_str.replace("{{", "{").replace("}}", "}")
            action = json.loads(action_str)

            print(f"DEBUG ACTION: {action}")

            # Check availability first
            slots = await get_available_slots(action["doctor"], action["date"])
            print(f"DEBUG SLOTS: {slots}")

            if not slots or "error" in slots:
                reply_text = f"Sorry, no available slots on {action['date']}. Could you try a different date?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

            # Check if requested time is available
            date_slots = []
            for date_key, slot_list in slots.items():
                date_slots.extend([s.get("time") or s.get("start") for s in slot_list])

            # Find matching slot
            slot_match = None
            for slot in date_slots:
                if action["time"] in slot:
                    slot_match = slot
                    break

            if not slot_match:
                available_times = [s.split("T")[1][:5] for s in date_slots[:5]]
                if available_times:
                    reply_text = f"Sorry, {action['time']} is not available. Available slots are: {', '.join(available_times)}. Which one works for you?"
                else:
                    reply_text = f"Sorry, no slots available on {action['date']}. Would you like to try another date?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

            # Book it
            result = await book_appointment(
                action["doctor"],
                slot_match,
                action["patient_name"],
                action["patient_email"],
            )

            print(f"DEBUG BOOKING RESULT: {result}")

            if result.get("success"):
                doctor_name = DOCTORS[action["doctor"]]["name"]
                reply_text = f"Your appointment with {doctor_name} on {action['date']} at {action['time']} is confirmed! A calendar invite has been sent to {action['patient_email']}."
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(
                    reply=reply_text,
                    booking_confirmed=True,
                    booking_details=action,
                )
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"DEBUG BOOKING ERROR: {error_msg}")
                reply_text = "Sorry, there was an issue booking. Please try again or pick a different time."
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

        except Exception as e:
            print(f"DEBUG EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            reply_text = "I had trouble processing that. Could you repeat your preferred time?"
            history.append({"role": "assistant", "content": reply_text})
            return ChatResponse(reply=reply_text)

    # Clean reply — remove any partial ACTION text
    clean_reply = reply.split("ACTION:")[0].strip()
    return ChatResponse(reply=clean_reply)


@app.get("/api/doctors")
async def list_doctors():
    return {"doctors": DOCTORS}


@app.get("/health")
async def health():
    return {"status": "ok"}