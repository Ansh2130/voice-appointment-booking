Top 3 Practices Used
1. User-Centric Conversation Design

I focused on making the interaction feel like a real receptionist instead of a chatbot. The system asks only one thing at a time, avoids repeating information, and adapts based on what the user already said. This improves usability, especially for voice interfaces.

2. Modular Architecture

The system is split into clear components:

Frontend (Voice UI)
Backend (FastAPI)
LLM (Groq)
Scheduling (Cal.com)

This separation made development faster and debugging easier.

3. Graceful Error Handling

I added fallbacks for real-world issues like:

Invalid email inputs
Unavailable slots
Backend cold starts
Garbled speech

Instead of breaking, the system always guides the user to the next step.

One Challenge Faced

Handling unstructured voice input reliably was challenging.

Users often provide multiple pieces of information at once (e.g., doctor, time, and name in one sentence), or speak unclearly.

How I Solved It

I used an LLM-based approach to extract structured data from natural language and designed strict conversation rules to:

Capture missing fields step-by-step
Avoid re-asking known information
Validate inputs like email carefully

Additionally, I added fallback text input for cases where voice input fails, especially for email capture.

Final Thought

The goal was to create a frictionless, voice-first experience. Instead of interacting with a system, the user feels like they are speaking to a real assistant — simple, fast, and intuitive.