import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="MCP Health Copilot", page_icon="🏥")
st.title("🏥 MCP Health Copilot")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your Health Copilot. How can I help you today?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type your message...")

def get_bot_reply(user_message):
    try:
        response = requests.post(
            BACKEND_URL,
            json={"message": user_message},
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"reply": f"Error contacting backend: {e}", "intent": "error"}

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    bot_reply = get_bot_reply(user_input)
    reply_text = bot_reply.get("reply", "No reply from backend.")
    intent = bot_reply.get("intent", "")

    if intent and intent != "error":
        st.info(f"Action: {intent.replace('_', ' ').title()}")

    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.write(reply_text)