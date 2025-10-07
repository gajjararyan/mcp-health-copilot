import os
import re
import urllib.parse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import geocoder
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from langdetect import detect
from googletrans import Translator
from dotenv import load_dotenv
import dateparser

# ---------------- Load Environment ----------------
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Load Google Maps key

# ---------------- Google Calendar Setup ----------------
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
creds = None
if os.path.exists('backend/token.json'):
    creds = Credentials.from_authorized_user_file('backend/token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('backend/credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
    with open('backend/token.json', 'w') as token:
        token.write(creds.to_json())
service = build('calendar', 'v3', credentials=creds)

# ---------------- Translator ----------------
translator = Translator()

async def translate_to_english(text):
    try:
        lang = detect(text)
        if lang != 'en':
            translated = translator.translate(text, src=lang, dest='en')
            return translated.text, lang
        return text, 'en'
    except:
        return text, 'en'

async def translate_from_english(text, target_lang='en'):
    try:
        if target_lang != 'en':
            translated = translator.translate(text, src='en', dest=target_lang)
            return translated.text
        return text
    except:
        return text

# ---------------- Async Gemini API ----------------
async def gemini_generate(prompt: str):
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post(GEMINI_URL, headers=headers, json=data)
                res.raise_for_status()
                result = res.json()
                return (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "I'm here to help you.")
                )
        except httpx.ReadTimeout:
            print(f"Gemini timeout on attempt {attempt+1}, retrying...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Gemini API error: {e}")
    return "Sorry, I couldn't reach Gemini right now. Please try again later."

# ---------------- FastAPI Setup ----------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Detect Intent ----------------
async def detect_intent(message: str):
    prompt = f"""
    Detect user intent for: "{message}"
    Choose one: symptom_check, medicine_suggest, appointment, order_medicine, chit_chat, help.
    """
    intent = (await gemini_generate(prompt)).strip().lower()
    if intent not in ["symptom_check", "medicine_suggest", "appointment", "order_medicine", "chit_chat", "help"]:
        msg = message.lower()
        if any(word in msg for word in ["fever", "pain", "cough", "cold", "headache", "stomach", "stroke"]):
            intent = "symptom_check"
        elif any(word in msg for word in ["medicine", "tablet", "pill"]):
            intent = "medicine_suggest"
        elif any(word in msg for word in ["appointment", "doctor", "meet", "schedule"]):
            intent = "appointment"
        elif any(word in msg for word in ["order", "pharmacy", "buy medicine", "nearby"]):
            intent = "order_medicine"
        else:
            intent = "chit_chat"
    return intent

# ---------------- Calendar Event ----------------
def create_calendar_event(service, doctor_name, description, start_time):
    event = {
        'summary': f"Consultation with {doctor_name}",
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': (start_time + timedelta(minutes=30)).isoformat(), 'timeZone': 'Asia/Kolkata'},
        'conferenceData': {
            'createRequest': {'conferenceSolutionKey': {'type': 'hangoutsMeet'}, 'requestId': 'healthcopilot-meet'}
        },
        'reminders': {'useDefault': True},
    }
    event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1).execute()
    return event

# ---------------- Symptom Check ----------------
async def check_symptom(message):
    prompt = f"""
    You are a professional doctor.
    Respond empathetically to: "{message}".
    Include:
    - Home remedies
    - OTC medicines with dosage and timing
    - When to see a doctor
    End by offering to schedule a doctor.
    Keep it under 200 words.
    """
    return await gemini_generate(prompt)

# ---------------- Medicine Suggest ----------------
async def suggest_medicine(message):
    prompt = f"""
    You are a helpful pharmacist.
    Suggest safe medicines for: "{message}".
    Include dosage and timing in a clear table format if possible.
    Offer home care tips and advise to see a doctor if needed.
    """
    return await gemini_generate(prompt)

# ---------------- Get User Location ----------------
def get_user_location():
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng  # [lat, lng]
    return [23.2156, 72.6369]  # fallback Gandhinagar

# ---------------- Nearby Pharmacies ----------------
def get_nearby_pharmacies(medicine_name, user_latlng):
    lat, lng = user_latlng
    pharmacies = []
    try:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=3000&type=pharmacy&keyword={urllib.parse.quote(medicine_name)}&key={GOOGLE_MAPS_API_KEY}"
        res = httpx.get(url, timeout=10)
        results = res.json().get("results", [])
        for p in results[:5]:  # top 5 pharmacies
            pharmacies.append({
                "name": p.get("name"),
                "address": p.get("vicinity"),
                "map_link": f"https://www.google.com/maps/search/?api=1&query={p['geometry']['location']['lat']},{p['geometry']['location']['lng']}"
            })
    except Exception as e:
        print(f"Pharmacy API error: {e}")

    if not pharmacies:
        return f"No nearby pharmacies found for {medicine_name}."

    reply = f"Nearby pharmacies for {medicine_name}:\n"
    for p in pharmacies:
        reply += f"- {p['name']}, {p['address']} — [View Map]({p['map_link']})\n"
    return reply

# ---------------- Extract Doctor Name ----------------
def extract_doctor_name(text):
    match = re.search(r"(Dr\.?\s+[A-Za-z]+|General doctor|specialist|physician)", text, re.I)
    if match:
        return match.group(0)
    return "Doctor"

# ---------------- Chat Endpoint ----------------
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    user_id = data.get("user_id", "default")

    # Translate user message to English
    message_en, user_lang = await translate_to_english(message)

    # Detect intent
    intent = await detect_intent(message_en)

    # Handle intents
    if intent == "appointment":
        doctor_name = extract_doctor_name(message_en)
        date_time = dateparser.parse(message_en, settings={'PREFER_DATES_FROM': 'future'})
        if not date_time:
            reply_en = (
                "I can help you book an appointment, but I need a specific date and time.\n"
                "Please provide it in this format:\n"
                "- Doctor name (if not mentioned, default: Dr. Sharma)\n"
                "- Date and time\n\n"
                "Example messages you can send:\n"
                "1. 'Dr. Sharma tomorrow at 10 AM'\n"
                "2. 'General doctor on 15-10-2025 at 3 PM'\n"
                "3. 'Book a physician appointment next Monday at 4:30 PM'"
            )
        else:
            try:
                event = create_calendar_event(service, doctor_name, "Online consultation", date_time)
                meet_link = event.get("hangoutLink", "")
                reply_en = (
                    f"✅ Your appointment with {doctor_name} is scheduled!\n"
                    f"🕒 Time: {date_time.strftime('%I:%M %p')}\n"
                    f"📅 Date: {date_time.strftime('%d-%m-%Y')}\n"
                    f"💬 Meet Link: {meet_link}\n\n"
                    "You’ll get a calendar notification shortly!"
                )
            except Exception as e:
                reply_en = f"Error scheduling appointment: {e}"

    elif intent == "symptom_check":
        reply_en = await check_symptom(message_en)

    elif intent == "medicine_suggest":
        reply_en = await suggest_medicine(message_en)

    elif intent == "order_medicine":
        user_location = get_user_location()
        reply_en = get_nearby_pharmacies(message_en, user_location)

    elif intent == "chit_chat":
        reply_en = await gemini_generate(f"Be a friendly healthcare companion and chat nicely: {message_en}")

    elif intent == "help":
        reply_en = "I can help you with symptoms, medicines, reminders, booking doctor appointments, and ordering medicines nearby."

    else:
        reply_en = "I'm not sure I understood that. Could you please clarify?"

    # Translate reply back to user's language
    reply = await translate_from_english(reply_en, target_lang=user_lang)

    return {"reply": reply, "intent": intent}
