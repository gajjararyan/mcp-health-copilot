# 🏥 MCP HealthCare Assistant 🤖


## Overview

**MCP HealthCare Assistant** is an AI-powered healthcare assistant designed to help users with:

- Checking symptoms and providing home remedies
- Suggesting safe OTC medicines with dosage guidance
- Finding nearby pharmacies
- Booking doctor appointments and adding them to Google Calendar
- Casual conversation and healthcare guidance
- Multi-language support

The system leverages **Model Context Protocol (MCP)** and AI models (Gemini API) to automate common healthcare workflows.

---

## Features

- **Symptom Check**
  - Provides empathetic responses for symptoms
  - Suggests home remedies and over-the-counter medicines
  - Advises when to see a doctor

- **Medicine Suggestion**
  - Lists safe medicines with recommended dosage and timing
  - Includes home care tips

- **Order Medicine**
  - Finds nearby pharmacies using Google Maps Places API
  - Provides clickable maps for convenience

- **Doctor Appointment**
  - Schedules appointments with doctors
  - Adds events to Google Calendar with Google Meet links

- **Multi-language Support**
  - Detects user language and translates messages to English for AI processing
  - Translates AI responses back to the user's language

- **Chit-Chat**
  - Casual conversation and guidance for better user experience

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, AsyncHTTPX
- **AI/Intent Detection:** Gemini 2.5 API (Google)
- **Translator:** Google Translate API
- **Calendar:** Google Calendar API
- **Location Services:** Geocoder + Google Maps Places API
- **Frontend:** Streamlit

---

## Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/gajjararyan/mcp-health-copilot.git
cd mcp-health-copilot
```

2. Create and activate a Python virtual environment for the backend
```bash
python3 -m venv backend/venv
# On Linux/macOS
source backend/venv/bin/activate
# On Windows (PowerShell)
.\backend\venv\Scripts\Activate.ps1
# On Windows (cmd)
.\backend\venv\Scripts\activate.bat
```
3. Install dependencies
Make sure your virtual environment is activated, then run:

```Bash
pip install -r requirements.txt
```
4. Setup Environment Variables
Create a .env file in the root directory with the following content:

```bash
env

GEMINI_API_KEY=<your_gemini_api_key>
GOOGLE_MAPS_API_KEY=<your_google_maps_api_key>
```

5. Google Calendar Setup
Download credentials.json from Google Cloud Console and place it in the backend/ directory.
Run backend/main.py once to generate token.json for authentication:
```Bash

python backend/main.py
```
6. Run Backend
Make sure your virtual environment is activated, then run:

```Bash

uvicorn backend.main:app --reload
```
7. Run Frontend (Streamlit)
In a new terminal (frontend does not require the backend venv), run:

```Bash
 streamlit run frontend/app.py
```