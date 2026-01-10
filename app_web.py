import streamlit as st
import edge_tts
import asyncio
import os
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# --- 1. PAGE CONFIG & STYLING (English) ---
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    .main-title { color: white; font-size: 40px; font-weight: 800; margin-bottom: 0px; }
    .sub-title { color: #94a3b8; font-size: 18px; margin-bottom: 30px; }
    .stButton>button { 
        background-color: #7c3aed !important; color: white !important; 
        border-radius: 10px; padding: 15px 30px; font-weight: bold; width: 100%; 
    }
    label, .stMarkdown p, .stSuccess, .stInfo { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PRIVACY SYSTEM (English) ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("<h2 style='color:white;'>🔐 DidactAI Restricted Access</h2>", unsafe_allow_html=True)
    with st.form("login"):
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if user == "admin" and pw == "didactai2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Invalid credentials")
    st.stop()

# --- 3. INTERFACE (English) ---
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists("logo.png"): st.image("logo.png", width=80)
with col2:
    st.markdown('<p class="main-title">DIDAPOD</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Powered by DidactAI-US</p>', unsafe_allow_html=True)

st.markdown("### 🗺️ Workflow")
c1, c2, c3, c4 = st.columns(4)
c1.info("1. Upload")
c2.info("2. Language")
c3.info("3. Dubbing")
c4.info("4. Finish")

st.markdown("---")
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French"])
uploaded_file = st.file_uploader("Upload your podcast (MP3 or WAV)", type=["mp3", "wav"])

if uploaded_file:
    st.audio(uploaded_file)
    
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.status("🤖 Processing audio...", expanded=True) as status:
                # 1. Save and Convert
                st.write("⏳ Preparing file...")
                with open("temp_input.mp3", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                audio = AudioSegment.from_file("temp_input.mp3")
                audio.export("temp_wav.wav", format="wav")

                # 2. Transcription
                st.write("🎙️ Transcribing original podcast...")
                r = sr.Recognizer()
                with sr.AudioFile("temp_wav.wav") as source:
                    audio_data = r.record(source)
                    text_orig = r.recognize_google(audio_data, language="es-ES") # Detects Spanish input

                # 3. Translation
                st.write("🌍 Translating content...")
                codes = {"English": "en", "Spanish": "es", "French": "fr"}
                text_trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text_orig)

                # 4. AI Voice Generation (Using Emma for English)
                st.write("🔊 Generating AI Voice...")
                voice_map = {
                    "English": "en-US-EmmaMultilingualNeural",
                    "Spanish": "es-ES-ElviraNeural",
                    "French": "fr-FR-DeniseNeural"
                }
                
                communicate = edge_tts.Communicate(text_trans, voice_map[target_lang])
                asyncio.run(communicate.save("output.mp3"))
                
                status.update(label="Dubbing Complete!", state="complete")
            
            st.balloons()
            with open("output.mp3", "rb") as f:
                st.download_button("📥 Download Dubbed Podcast", f, "didapod_result.mp3")
        
        except Exception as e:
            st.error(f"Technical detail: {e}")

# --- 4. FOOTER ---
st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US | AI Enterprise Solutions</small></center>", unsafe_allow_html=True)
