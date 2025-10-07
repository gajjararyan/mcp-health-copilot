def check_symptom(message, gemini_generate):
    prompt = (
        f"You are a health assistant. A user says: '{message}'. "
        "Give a short, safe, and clear health suggestion. "
        "If it's an emergency, say so. If not, suggest seeing a doctor if needed. "
        "Do not diagnose, just help."
    )
    return gemini_generate(prompt)