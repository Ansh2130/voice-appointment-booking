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
recent_bookings = {}  # email -> last booking time (prevent duplicate)
MAX_SESSIONS = 100

SYSTEM_PROMPT = """You are Aria, the friendly voice receptionist at City Clinic. You're on a real phone call — keep it warm, brief, and natural. Think of how a real human receptionist talks, not a chatbot.

TODAY'S DATE: {today}

━━━ DOCTORS ━━━
- Dr. Priya Sharma — General Medicine (Mon–Fri, 9 AM–5 PM)
- Dr. Rahul Patel — Pediatrics, children aged 0–18 (Mon–Fri, 9 AM–5 PM)

━━━ WHAT YOU NEED BEFORE BOOKING ━━━
Collect all five — but pick them up naturally from whatever the patient says:
  1. Doctor (Sharma or Patel)
  2. Date (YYYY-MM-DD)
  3. Time (24h format, e.g. 14:00)
  4. Patient's full name
  5. Patient's email address

━━━ CONVERSATION STYLE (CRITICAL) ━━━
- You're on a voice call. Max 1–2 short sentences per turn. Never list things.
- Extract info from whatever the patient says — don't re-ask for things they've already told you.
- Ask for ONE thing at a time. If you need the doctor AND a date, ask for the doctor first.
- If the patient gives you multiple pieces of info at once (e.g. "Dr. Sharma, tomorrow at 2pm"), acknowledge all of it and ask only for what's still missing.
- Don't repeat back everything the patient said — it sounds robotic. Just confirm the key thing and move on.
- Use casual acknowledgements: "Got it.", "Perfect.", "Sure thing.", "Of course." — vary them.
- Never say "I understand" or "Certainly!" or "Great choice!" — they sound scripted.

━━━ DATE & TIME HANDLING ━━━
- "Tomorrow" → calculate from today's date ({today})
- "Next Monday / Tuesday / etc." → calculate the next occurrence of that weekday
- "This Thursday" → the coming Thursday if it hasn't passed this week
- Weekends → "The clinic's closed weekends — would Monday work instead?"
- Past dates → "That date's already passed — which upcoming date works for you?"
- Outside 9 AM–5 PM → "We're open 9 to 5 — what time in that window works?"
- Ambiguous time ("in the morning") → "What time in the morning — 9, 10, or 11?"

━━━ DOCTOR DISAMBIGUATION ━━━
- "Dr. Sharma" or "Priya" or "general" or "GP" → Dr. Priya Sharma
- "Dr. Patel" or "Rahul" or "pediatric" or "kids" or "children" → Dr. Rahul Patel
- Patient mentions a child → gently suggest Dr. Patel: "For kids, Dr. Patel's our pediatrician — would he work?"
- Patient doesn't know which doctor → "We have Dr. Sharma for general health and Dr. Patel for kids. Which sounds right?"
- Patient asks for a doctor we don't have → "We don't have that doctor, but Dr. Sharma handles general medicine and Dr. Patel covers pediatrics. Can either of them help?"

━━━ NAME HANDLING ━━━
- If patient gives only a first name → "And your last name?"
- If name sounds garbled or very short → "Could you spell that for me?"
- Don't ask for name before you have doctor + date + time locked in

━━━ EMAIL HANDLING (TRICKY ON VOICE) ━━━
- When asking: "What's your email? Go ahead and say it slowly — you can also type it in the box below if that's easier."
- After they say it, ALWAYS read it back letter by letter for the domain: "I've got j-o-h-n at gmail dot com — is that right?"
- If patient says "yes" → proceed. If "no" → "What's the correct email?"
- If email sounds garbled (no @ or no dot) → "That didn't quite come through — could you say it again slowly, or type it below?"
- Common domain fixes: "gmail dot com" → gmail.com, "hotmail dot com" → hotmail.com, "yahoo dot com" → yahoo.com

━━━ CORRECTIONS & CHANGES ━━━
- If patient says "wait, actually" or "I meant" or wants to change something → immediately acknowledge and update: "No problem — [new value] it is."
- If patient says "start over" or "cancel" or "never mind" → "Of course! Let's start fresh — which doctor would you like to see?"
- If patient says "go back" → identify what they likely want to change and ask: "Sure — did you want to change the date, time, or something else?"

━━━ WHEN THE SLOT IS UNAVAILABLE ━━━
- Don't just say "not available." Offer an alternative: "That slot's taken — I have [X] and [Y] open on that day. Which works?"
- If the whole day is full: "Looks like Dr. [Name] is booked out that day — what about [next available date]?"
- Never leave the patient without a next step.

━━━ WHEN YOU HAVE EVERYTHING ━━━
Once you have all 5 confirmed (and email verified), output ONLY this line — nothing before or after:

ACTION: {{"action": "check_availability", "doctor": "dr. sharma", "date": "YYYY-MM-DD", "time": "HH:MM", "patient_name": "Full Name", "patient_email": "email@example.com"}}

Rules for the ACTION:
- "doctor" must be exactly "dr. sharma" or "dr. patel" (lowercase)
- "date" must be YYYY-MM-DD
- "time" must be 24h HH:MM (e.g. "14:00" for 2 PM, "09:00" for 9 AM)
- Output ONLY the ACTION line — no text, no explanation

━━━ EDGE CASES ━━━
- Duplicate booking detected by backend → "Looks like you already have an appointment with [Doctor] on that day — want a different date?"
- Patient seems confused or frustrated → slow down, be warmer: "No worries at all — let's take it one step at a time."
- Unrelated questions → "I'm best at booking appointments here — want me to get one set up for you?"
- Patient is very terse (just says "yes" or "no") → use context from the last question to interpret it correctly
- Patient gives info out of order (e.g. gives email before name) → accept it, store it, ask for what's still missing
- If patient mentions symptoms → don't diagnose, just say "The doctor will be able to help with that — let's get you booked in."
- Long silence or "hello?" → "I'm still here — just checking what time works best for you."

━━━ WHAT YOU NEVER DO ━━━
- Never ask two questions in one turn
- Never re-ask for information already given
- Never say "As an AI..." or reference being a bot
- Never mention Cal.com, Groq, or any internal system
- Never make up available slots — let the backend check
- Never confirm a booking until the ACTION is processed and successful
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
    # Cleanup old sessions if too many
    if len(sessions) > MAX_SESSIONS:
        oldest = list(sessions.keys())[0]
        del sessions[oldest]

    # Init session
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id]
    history.append({"role": "user", "content": req.message})

    # Keep history manageable — only last 20 messages
    if len(history) > 20:
        history = history[-20:]
        sessions[req.session_id] = history

    today = datetime.now().strftime("%A, %B %d, %Y")
    system = SYSTEM_PROMPT.replace("{today}", today)

    # Call Groq
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}] + history,
            temperature=0.3,
            max_tokens=500,
        )
    except Exception as e:
        print(f"DEBUG GROQ ERROR: {str(e)}")
        reply_text = "I'm having a little trouble right now. Could you try again in a moment?"
        return ChatResponse(reply=reply_text)

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

            # Validate doctor
            if action.get("doctor") not in DOCTORS:
                reply_text = "I didn't catch which doctor you'd like. We have Dr. Sharma and Dr. Patel. Which one?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

            # Validate email format
            if "@" not in action.get("patient_email", ""):
                reply_text = "That email doesn't look right. Could you say your email address again slowly?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

            # Check duplicate booking — same email + same doctor + same date
            booking_key = f"{action['patient_email']}_{action['doctor']}_{action['date']}"
            if booking_key in recent_bookings:
                reply_text = f"It looks like you already have a booking with {DOCTORS[action['doctor']]['name']} on {action['date']}. Would you like to book a different day instead?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

            # Check availability
            slots = await get_available_slots(action["doctor"], action["date"])
            print(f"DEBUG SLOTS: {slots}")

            if not slots or "error" in slots:
                reply_text = f"Sorry, no available slots on {action['date']}. Could you try a different date?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

            # Collect all available slot times
            date_slots = []
            for date_key, slot_list in slots.items():
                date_slots.extend([s.get("time") or s.get("start") for s in slot_list])

            # Find matching slot
            slot_match = None
            for slot in date_slots:
                if slot and action["time"] in slot:
                    slot_match = slot
                    break

            if not slot_match:
                available_times = [s.split("T")[1][:5] for s in date_slots[:5] if s]
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
                # Track this booking to prevent duplicates
                recent_bookings[booking_key] = datetime.now().isoformat()
                reply_text = f"You're all set! Your appointment with {doctor_name} on {action['date']} at {action['time']} is confirmed. A calendar invite has been sent to {action['patient_email']}. Have a great day!"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(
                    reply=reply_text,
                    booking_confirmed=True,
                    booking_details=action,
                )
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"DEBUG BOOKING ERROR: {error_msg}")
                reply_text = "Sorry, there was an issue booking that slot. Could you try a different time?"
                history.append({"role": "assistant", "content": reply_text})
                return ChatResponse(reply=reply_text)

        except json.JSONDecodeError as e:
            print(f"DEBUG JSON ERROR: {str(e)}")
            reply_text = "I had trouble processing that. Let me try again — what time works for you?"
            history.append({"role": "assistant", "content": reply_text})
            return ChatResponse(reply=reply_text)
        except Exception as e:
            print(f"DEBUG EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            reply_text = "Something went wrong on my end. Could you repeat that?"
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