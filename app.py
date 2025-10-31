import streamlit as st
import random

# Streamlit page setup
st.set_page_config(
    page_title="Career Path Navigator — Explore. Analyze. Grow.",
    layout="wide"
)

# Serve the same HTML with JS and CSS intact
with open("edu.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# --- Simple local mock backend (simulate /api/chat) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def get_bot_reply(message, interests=""):
    """Return a lightweight AI-like response."""
    text = message.lower().strip()
    generic = [
        "That sounds interesting! Would you like to explore STEM or Creative fields?",
        "Great question! Try selecting a domain to visualize career options.",
        "Focus on your strengths — I can help map them to suitable careers.",
        "You can rate your skills below and get a personalized learning roadmap!",
        "Consider exploring related domains to broaden your career opportunities.",
    ]
    if not text:
        reply = "Please type something to begin our discussion!"
    elif "hello" in text or "hi" in text:
        reply = "Hello there! 👋 I’m your career guide. What are your interests?"
    elif "career" in text:
        reply = "There are many career paths! Try selecting a domain or entering interests to explore them."
    elif "help" in text or "guide" in text:
        reply = "Sure! Select a domain or describe your interests, and I’ll help visualize your options."
    elif "thanks" in text:
        reply = "You’re welcome! 🌟 Keep exploring and analyzing your skills."
    else:
        reply = random.choice(generic)
    if interests:
        reply += f" Based on your interests in {interests}, I suggest exploring those domains in the dendrogram."
    return reply

# Streamlit doesn’t directly allow JS fetch to /api/chat,
# so we simulate it within the Streamlit app itself.
# Inject JavaScript that calls Streamlit’s component via a message channel.

# Replace the original fetch('/api/chat', ...) with a mock function
mock_js_patch = """
<script>
  // Patch fetch('/api/chat') to call Streamlit backend using events
  window.fetch = async (url, options) => {
    if (url === '/api/chat') {
      const body = JSON.parse(options.body);
      const message = body.message;
      const interests = body.interests || '';
      const pyReply = await window.streamlitChatReply(message, interests);
      return {
        ok: true,
        json: async () => ({ reply: pyReply })
      };
    }
    return window._fetchOrig(url, options);
  };
</script>
"""

# Inject a bridge between JS and Python via Streamlit components
from streamlit.components.v1 import html as st_html
import json

# Frontend call handler using session_state
if "_last_msg" not in st.session_state:
    st.session_state._last_msg = None
if "_last_reply" not in st.session_state:
    st.session_state._last_reply = None

def handle_js_call():
    """Read latest message from frontend (via hidden text_input)."""
    msg = st.session_state.get("_js_input")
    if msg and msg != st.session_state._last_msg:
        st.session_state._last_msg = msg
        try:
            data = json.loads(msg)
            reply = get_bot_reply(data.get("message", ""), data.get("interests", ""))
            st.session_state._last_reply = reply
        except Exception:
            st.session_state._last_reply = "Error: invalid message."

# Hidden text input to receive data from JS
st.text_input("hidden", key="_js_input", on_change=handle_js_call, label_visibility="hidden")

# Inject bridge to allow JS→Python communication
bridge_js = """
<script>
  // Expose a function that JS can call to get a Python reply
  window.streamlitChatReply = async function(message, interests) {
    const payload = JSON.stringify({message: message, interests: interests});
    const input = window.parent.document.querySelector('input[id="_js_input"]');
    input.value = payload;
    input.dispatchEvent(new Event('change', { bubbles: true }));
    // Wait a bit until Streamlit processes
    await new Promise(r => setTimeout(r, 400));
    // Fetch latest reply text (stored in session)
    return window.parent.document.querySelector('textarea[readonly]').value;
  };
</script>
"""

# Display the full HTML + our mock patches and bridge
final_html = html_content + mock_js_patch + bridge_js

# Render the app
st_html(final_html, height=1600, scrolling=True)
