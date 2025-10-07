
def suggest_medicine(message):
    prompt = (
        f"You are a health assistant. A user asks: '{message}'. "
        "Suggest only over-the-counter medicines if appropriate, with warnings. "
        "If not appropriate, say to see a doctor. Never give prescription advice."
    )
    return gemini_generate(prompt)