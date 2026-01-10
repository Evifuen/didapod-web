import streamlit as st
import edge_tts
import asyncio
import os
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# --- VISUAL SETUP (Keep it light) ---
st.set_page_config(page_title="DIDAPOD", page_icon="🎙️")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    .main-title { color: white; font-size: 32px; font-weight: bold; }
    label, p { color: #94a3b8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "didactai2026":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- HEADER ---
st.markdown('<p class="main-title">DIDAPOD by DidactAI</p>', unsafe_allow_html=True)

target_lang = st.selectbox("Target Language:", ["English", "Spanish"])
uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav"])

if uploaded_file:
    if st.button("🚀 START DUBBING"):
        try:
            with st.spinner("Processing... Please wait"):
                # Save temp file
                with open("temp.mp3", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Convert to small WAV (Crucial to avoid Broken Pipe)
                audio = AudioSegment.from_file("temp.mp3")
                audio = audio.set_frame_rate(16000).set_channels(1)
                audio.export("temp.wav", format="wav")

                # Transcription
                r = sr.Recognizer()
                with sr.AudioFile("temp.wav") as source:
                    audio_data = r.record(source)
                    text_orig = r.recognize_google(audio_data, language="es-ES")

                # Translation
                lang_code = "en" if target_lang == "English" else "es"
                text_trans = GoogleTranslator(source='auto', target=lang_code).translate(text_orig)

                # Voice
                voice = "en-US-EmmaMultilingualNeural" if lang_code == "en" else "es-ES-ElviraNeural"
                asyncio.run(edge_tts.Communicate(text_trans, voice).save("out.mp3"))
                
                st.success("Done!")
                st.audio("out.mp3")
                with open("out.mp3", "rb") as f:
                    st.download_button("Download result", f, "result.mp3")
        except Exception as e:
            st.error(f"Error: {e}. Try a shorter clip first.")
