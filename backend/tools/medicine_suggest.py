import os
import requests

def suggest_medicine(message):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not set. Please add it to your .env file."

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"You are a health assistant. A user asks: '{message}'. Suggest only over-the-counter medicines if appropriate, with warnings. If not appropriate, say to see a doctor. Never give prescription advice."}
                ]
            }
        ]
    }
    params = {"key": api_key}

    try:
        response = requests.post(url, headers=headers, params=params, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error contacting Gemini: {e}"