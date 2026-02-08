import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import os
import base64
import time

# --- 1. SECURITY CONFIGURATION (SECRETS) ---
try:
    AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
    AZURE_REGION = st.secrets["AZURE_REGION"]
except:
    st.error("Azure credentials not found! Please check your Secrets in Streamlit Cloud.")
    st.stop()

# --- 2. PAGE CONFIGURATION & VISUAL STYLES ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo.png")

# CSS: Custom design and hiding Streamlit menus
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .stApp {{ background-color: #0f172a !important; }}
    
    button[kind="primaryFormSubmit"], .stButton>button {{
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        width: 100% !important;
        height: 50px !important;
    }}
    
    h1, h2, h3, label, p, span {{ color: white !important; }}
    .logo-container {{ text-align: center; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

if logo_data:
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_data}" width="200"></div>', unsafe_allow_html=True)

# --- 3. LOGIN & ACCESS CONTROL ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 DIDAPOD RESTRICTED ACCESS")
        email = st.text_input("📧 Authorized Email")
        if st.form_submit_button("VALIDATE LICENSE"):
            if email:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df = conn.read()
                    new_log = pd.DataFrame([{"Email": email, "Date": str(pd.Timestamp.now())}])
                    conn.update(data=pd.concat([df, new_log], ignore_index=True))
                    st.session_state["auth"] = True
                    st.rerun()
                except:
                    st.session_state["auth"] = True # Fallback
                    st.rerun()
    st.stop()

# --- 4. USER INTERFACE ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO v2.0</h1>", unsafe_allow_html=True)
st.write("<p style='text-align:center; color:#94a3b8;'>Azure AI Engine with Automatic Language Detection</p>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    target_lang = st.selectbox("Output Language:", ["English", "Spanish", "French", "Portuguese", "German"])
with c2:
    gender = st.selectbox("Voice Tone:", ["Male", "Female"])

up_file = st.file_uploader("Upload Podcast (Formats: MP3, WAV)", type=["mp3", "wav"])

# --- 5. PROCESSING LOGIC ---
if up_file:
    session_id = str(int(time.time()))
    temp_input = f"input_{session_id}.mp3"
    
    with open(temp_input, "wb") as f: 
        f.write(up_file.getbuffer())
    
    try:
        audio_check = AudioSegment.from_file(temp_input)
        duration_sec = len(audio_check) / 1000
        st.info(f"⏱️ Detected duration: {duration_sec:.2f} seconds")

        if st.button("🚀 START SMART TRANSLATION"):
            try:
                with st.spinner("🤖 Azure is analyzing and dubbing the audio..."):
                    # Split into 30-second chunks
                    chunks = [audio_check[i:i + 30000] for i in range(0, len(audio_check), 30000)]
                    final_audio = AudioSegment.empty()
                    
                    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                    # Use standard header format to avoid playback errors
                    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
                    
                    codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt", "German": "de"}
                    voices = {
                        "English": "en-US-AndrewNeural" if gender == "Male" else "en-US-AvaNeural",
                        "Spanish": "es-ES-AlvaroNeural" if gender == "Male" else "es-ES-ElviraNeural",
                        "French": "fr-FR-RemyNeural" if gender == "Male" else "fr-FR-DeniseNeural",
                        "Portuguese": "pt-BR-AntonioNeural" if gender == "Male" else "pt-BR-FranciscaNeural",
