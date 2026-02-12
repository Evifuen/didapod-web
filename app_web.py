import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, base64, requests, io
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURATION & CLOUD LINKS ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLceo0Pah9sBwimtjic9yURqKQ6_x7ms60Yigil8EboGoxVl7xCBtXJNeWR9ulbcFjXuUkgJ5g56tS/pub?output=csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"

st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

# --- 2. PROFESSIONAL STYLING ---
st.markdown("""
<style>
.stApp { background-color: #0f172a !important; }
.stButton>button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 18px !important;
    font-weight: 800 !important;
    width: 100% !important;
    border: none !important;
}
.stButton>button:hover { background-color: #6d28d9 !important; border: none !important; }
h1, h2, h3, label, p, span, div { color: white !important; }
.stSelectbox div, .stFileUploader section { background-color: #1e293b !important; color: white !important; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. SECRET CLEANER ENGINE (FIXES ERROR 5) ---
def get_clean_secret(name):
    val = st.secrets.get(name, "")
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 4. LOGIN & DATABASE REGISTRATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login_form"):
        st.markdown("<h2 style='text-align: center;'>🎙️ DIDAPOD ACCESS</h2>", unsafe_allow_html=True)
        user_email = st.text_input("Corporate Email")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="didactai2026")
        
        if st.form_submit_button("LOGIN TO PLATFORM"):
            if u == "admin" and p == "didactai2026" and "@" in user_email:
                try:
                    # Register access in Google Sheets
                    requests.post(APPS_SCRIPT_URL, json={
                        "email": user_email, 
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                except: pass
                st.session_state["auth"] = True
                st.session_state["user_email"] = user_email
                st.rerun()
            else:
                st.error("Invalid credentials or email format.")
    st.stop()

# --- 5. MAIN INTERFACE ---
st.title("🎙️ DIDAPOD PRO")
st.write(f"Welcome, **{st.session_state['user_email']}**")

col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2:
    voice_gender = st.selectbox("Voice Gender:", ["Female", "Male"])

uploaded_file = st.file_uploader("Upload Podcast Audio (MP3/WAV)", type=["mp3", "wav"])

if uploaded_file and AZ_KEY:
    st.audio(uploaded_file)
    
    if st.button("🚀 START AI DUBBING PROCESS"):
        try:
            with st.spinner("🤖 Processing with Azure AI Dubbing Engine..."):
                # Save temp file
                with open("input_audio.wav", "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 1. Translation Setup
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                t_cfg.set_property(speechsdk.PropertyId.Speech_LogFilename, "azure_log.txt")
                
                lang_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(lang_map[target_lang])
                
                audio_config = speechsdk.audio.AudioConfig(filename="input_audio.wav")
                recognizer = speechsdk.translation.TranslationRecognizer(t_cfg, audio_config)
                
                result = recognizer.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    # 2. Voice Synthesis Setup
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    output_filename = "didapod_dubbed.mp3"
                    audio_output = speechsdk.audio.AudioOutputConfig(filename=output_filename)
                    synthesizer = speechsdk.SpeechSynthesizer(s_cfg, audio_output)
                    
                    # Synthesize translated text
                    translated_text = result.translations[lang_map[target_lang]]
                    synthesizer.speak_text_async(translated_text).get()

                    st.balloons()
                    st.success("Dubbing process completed!")
                    
                    # Display Audio Player and Download Button
                    st.audio(output_filename)
                    with open(output_filename, "rb") as f:
                        st.download_button(
                            label="📥 DOWNLOAD DUBBED PODCAST",
                            data=f,
                            file_name=f"dubbed_{target_lang}.mp3",
                            mime="audio/mp3"
                        )
                else:
                    st.error(f"Azure Connection Issue: {result.reason}")
                    st.info("Please verify your AZURE_KEY in Streamlit Secrets.")
        except Exception as e:
            st.error(f"System Error: {e}")

# --- 6. FOOTER ---
st.markdown("<br><hr><center><small>© 2026 DidactAI | Professional AI Solutions</small></center>", unsafe_allow_html=True)
