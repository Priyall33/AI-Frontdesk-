import streamlit as st
import requests
import uuid
import base64
import os

API_KEY = os.getenv("API_KEY", "")
API_URL = "http://localhost:8000/api"

st.set_page_config(page_title="AIFRONTDESK", page_icon="🏥", layout="centered")

MD_ICON = '<svg width="44" height="44" viewBox="103.967 0.470703 54.779 40.941" xmlns="http://www.w3.org/2000/svg"><path d="M151.883 0.470703H110.83C107.04 0.470703 103.967 3.31501 103.967 6.82364V35.0589C103.967 38.5676 107.04 41.4119 110.83 41.4119H151.883C155.673 41.4119 158.746 38.5676 158.746 35.0589V6.82364C158.746 3.31501 155.673 0.470703 151.883 0.470703Z" fill="white"/><path d="M133.834 14.1177L133.325 15.1765L126.081 29.8824H123.793L116.421 15.1765V33.6471H113.498V9.29418H116.421L124.937 26.2354L133.707 8.23535V14.1177H133.834Z" fill="#16A4B2" stroke="#16A4B2" stroke-width="3" stroke-linecap="square"/><path d="M133.834 8.82324H141.333C146.798 8.82324 150.103 11.5291 150.103 16.8232V26.4703C150.103 28.1174 149.086 32.9409 140.951 32.9409H133.834V8.82324Z" fill="#16A4B2" stroke="#16A4B2" stroke-width="3"/><path d="M134.597 19.2939L133.326 18.588H140.825L140.571 19.1762L142.604 22.588L152.772 9.05859L155.441 14.7057L142.477 30.8233" fill="white"/></svg>'
md_b64 = base64.b64encode(MD_ICON.encode()).decode()
MD_AVATAR = f"data:image/svg+xml;base64,{md_b64}"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
* { font-family: 'Space Grotesk', sans-serif !important; }

.stApp { background: #16A4B2; }
#MainMenu, footer, header { visibility: hidden; }

@keyframes popDown {
    0%   { opacity: 0; transform: translateY(-50px) scale(0.95); }
    65%  { transform: translateY(6px) scale(1.01); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
.block-container {
    animation: popDown 0.65s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    padding-top: 2rem !important;
    max-width: 680px !important;
}

.stChatMessage {
    background: rgba(255,255,255,0.12) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    box-shadow: none !important;
}
.stChatMessage p,
.stChatMessage li,
.stChatMessage span { color: white !important; }

.stCaption { color: rgba(255,255,255,0.55) !important; font-size: 0.72rem !important; }

[data-testid="stBottom"] {
    padding: 1rem 0 2rem 0 !important;
    width: 100% !important;
    left: 0 !important;
    right: 0 !important;
}
[data-testid="stBottomBlockContainer"] { padding: 0 !important; }
.stChatInput { padding: 0 !important; width: 100% !important; }
.stChatInput > div {
    border-radius: 50px !important;
    border: none !important;
    background: white !important;
    padding: 10px 24px !important;
    box-shadow: 0 8px 40px rgba(0,0,0,0.15) !important;
    width: 100% !important;
    margin: 0 !important;
}
.stChatInput input {
    color: #0d3d44 !important;
    font-size: 0.95rem !important;
    background: transparent !important;
}
.stChatInput input::placeholder { color: #9bb5b8 !important; }
[data-testid="stChatInputSubmitButton"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 2rem 0;">
    <div style="
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: white;
        letter-spacing: -2px;
        line-height: 1;
    ">AI<span style="font-weight:300;">FRONTDESK</span></div>
    <div style="
        font-size: 0.7rem;
        color: rgba(255,255,255,0.6);
        letter-spacing: 4px;
        margin-top: 10px;
        text-transform: uppercase;
    ">Your Clinic Assistant</div>
    <div style="
        display:inline-flex; align-items:center; gap:6px;
        margin-top: 14px;
        background: rgba(255,255,255,0.15);
        border-radius: 30px;
        padding: 5px 16px;
        font-size: 0.72rem;
        color: white;
    ">
        <span style="width:7px;height:7px;background:#4fffb0;border-radius:50%;display:inline-block;"></span>
        We're online
    </div>
</div>
""", unsafe_allow_html=True)

# session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "welcomed" not in st.session_state:
    st.session_state.welcomed = False
if "patient_name" not in st.session_state:
    st.session_state.patient_name = None

if not st.session_state.welcomed:
    welcome = "Hello! Welcome to the clinic. May I have your name please?"
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    st.session_state.welcomed = True

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message("assistant", avatar=MD_AVATAR):
            st.write(msg["content"])
            if msg.get("sources"):
                st.caption(f"Source: {', '.join(msg['sources'])}")
    else:
        with st.chat_message("user"):
            st.write(msg["content"])

if prompt := st.chat_input("Ask about the clinic or book an appointment..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # first message after welcome = patient's name
    if st.session_state.patient_name is None:
        st.session_state.patient_name = prompt.strip()
        answer = f"Hey {st.session_state.patient_name}! How can I assist you today?"
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant", avatar=MD_AVATAR):
            st.write(answer)
        st.rerun()
    else:
        with st.spinner(""):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"message": prompt, "session_id": st.session_state.session_id},
                    headers={"x-api-key": API_KEY},
                )
                data = response.json()
                answer = data["answer"]
                sources = data.get("sources", [])
            except Exception:
                answer = "I'm having trouble connecting. Please try again."
                sources = []

        with st.chat_message("assistant", avatar=MD_AVATAR):
            st.write(answer)
            if sources:
                st.caption(f"Source: {', '.join(sources)}")

        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})