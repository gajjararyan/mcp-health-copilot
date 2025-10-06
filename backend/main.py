import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests

# Google Calendar imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Calendar setup
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
creds = None
if os.path.exists('backend/token.json'):
    creds = Credentials.from_authorized_user_file('backend/token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('backend/credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
    with open('backend/token.json', 'w') as token:
        token.write(creds.to_json())
service = build('calendar', 'v3', credentials=creds)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo, allow all. Restrict in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory log
logs = []

# --- Gemini API Helper ---
def gemini_generate(prompt):
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    params = {"key": GEMINI_API_KEY}
    try:
        response = requests.post(url, headers=headers, params=params, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "No response from Gemini.")
    except Exception as e:
        return f"Error contacting Gemini: {e}"

# --- Intent Detection ---
def detect_intent(message):
    prompt = (
        f"Classify the user's intent from this message: '{message}'. "
        "Choose one of: symptom_check, medicine_suggest, appointment, reminder, log, chit_chat, unknown. "
        "Reply with only the intent label."
    )
    intent = gemini_generate(prompt).strip().lower()
    if intent not in ["symptom_check", "medicine_suggest", "appointment", "reminder", "log", "chit_chat"]:
        intent = "unknown"
    return intent

# --- Tool Functions ---
def check_symptom(message):
    prompt = (
        f"You are a health assistant. A user says: '{message}'. "
        "Give a short, safe, and clear health suggestion. "
        "If it's an emergency, say so. If not, suggest seeing a doctor if needed. "
        "Do not diagnose, just help."
    )
    return gemini_generate(prompt)

def suggest_medicine(message):
    prompt = (
        f"You are a health assistant. A user asks: '{message}'. "
        "Suggest only over-the-counter medicines if appropriate, with warnings. "
        "If not appropriate, say to see a doctor. Never give prescription advice."
    )
    return gemini_generate(prompt)

def create_calendar_event(summary, description, start_time, end_time):
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return f"Event created: {event.get('htmlLink')}"

def book_appointment(message):
    # For demo, book for tomorrow at 10am for 30 minutes
    now = datetime.now()
    start = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    return create_calendar_event(
        summary="Doctor Appointment",
        description=message,
        start_time=start.isoformat(),
        end_time=end.isoformat()
    )

def set_reminder(message):
    # For demo, set for today at 8pm for 15 minutes
    now = datetime.now()
    start = now.replace(hour=20, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=15)
    return create_calendar_event(
        summary="Health Reminder",
        description=message,
        start_time=start.isoformat(),
        end_time=end.isoformat()
    )

def log_action(action, detail):
    logs.append({"time": datetime.now().isoformat(), "action": action, "detail": detail})

def get_logs():
    if not logs:
        return "No health records found."
    return "\n".join([f"{l['time']}: [{l['action']}] {l['detail']}" for l in logs])

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    intent = detect_intent(message)
    reply = "Sorry, I didn't understand. Try asking about symptoms, medicines, appointments, or reminders."

    if intent == "symptom_check":
        reply = check_symptom(message)
        log_action("Symptom Check", message)
    elif intent == "medicine_suggest":
        reply = suggest_medicine(message)
        log_action("Medicine Suggest", message)
    elif intent == "appointment":
        reply = book_appointment(message)
        log_action("Appointment", message)
    elif intent == "reminder":
        reply = set_reminder(message)
        log_action("Reminder", message)
    elif intent == "log":
        reply = get_logs()
    elif intent == "chit_chat":
        reply = gemini_generate(f"Chat with the user: {message}")

    return {"reply": reply, "intent": intent}