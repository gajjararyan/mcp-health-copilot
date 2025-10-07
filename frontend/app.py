import streamlit as st
import requests
from urllib.parse import quote

# Backend MCP URL
BACKEND_URL = "http://localhost:8000/chat"

# Streamlit page setup
st.set_page_config(page_title="MCP Health Copilot", page_icon="🏥")
st.title("🏥 MCP Health Copilot")

# Initialize session messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your Health Copilot. How can I help you today?"}
    ]

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_input = st.chat_input("Type your message...")

def get_bot_reply(user_message):
    try:
        response = requests.post(
            BACKEND_URL,
            json={"message": user_message},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"reply": f"Error contacting backend: {e}", "intent": "error"}

# Handle user input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get backend reply
    bot_reply = get_bot_reply(user_input)
    reply_text = bot_reply.get("reply", "No reply from backend.")
    intent = bot_reply.get("intent", "")

    # Display pharmacy links as clickable
    if intent == "order_medicine":
        # Check if the bot returned a Google Maps link
        # Extract the link from the text (assuming bot returns "here: <link>")
        import re
        match = re.search(r"(https?://[^\s]+)", reply_text)
        if match:
            link = match.group(0)
            st.session_state.messages.append({"role": "assistant", "content": f"[Click here to see pharmacies]({link})"})
        else:
            st.session_state.messages.append({"role": "assistant", "content": reply_text})
    else:
        st.session_state.messages.append({"role": "assistant", "content": reply_text})

    with st.chat_message("assistant"):
        if intent == "order_medicine" and match:
            st.markdown(f"[Click here to see pharmacies]({link})")
        else:
            st.write(reply_text)

# Optional: Show intent for debugging
# if intent and intent != "error":
#     st.info(f"Detected action: {intent.replace('_', ' ').title()}")
