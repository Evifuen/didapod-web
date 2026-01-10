import streamlit as st
import edge_tts
import asyncio
import os
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment

# --- 1. LUXURY INTERFACE (ENGLISH) ---
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    .main-title { color: white; font-size: 40px; font-weight: 800; margin-bottom: 0px; }
    .sub-title { color: #94a3b8; font-size: 18px; margin-bottom: 30px; }
    .stButton>button { 
        background-color: #7c3aed !important; color: white !important; 
        border-radius: 10px; padding: 15px 30px; font-weight: bold; width: 100%; border: none;
    }
    label, .stMarkdown p, .stSuccess, .stInfo { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY SYSTEM ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.markdown("<h2 style='color:white;'>🔐 Restricted Access</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Invalid credentials")
    st.stop()

# --- 3. BRANDING ---
col1, col2 = st.columns([1, 4])
with col2:
    st.markdown('<p class="main-title">DIDAPOD</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Powered by DidactAI-US</p>', unsafe_allow_html=True)

# Workflow visual indicator
c1, c2, c3, c4 = st.columns(4)
c1.info("1. Upload")
c2.info("2. Lang")
c3.info("3. Dub")
c4.info("4. Finish")

st.markdown("---")
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French"])
up_file = st.file_uploader("Upload podcast (MP3/WAV)", type=["mp3", "wav"])

# Función para procesar textos largos dividiéndolos en partes (FIX 5000 CHARS)
async def safe_voice_generation(text, voice, output_file):
    # Divide el texto cada 4000 caracteres para no chocar con el límite de 5000
    parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    final_audio = AudioSegment.empty()
    
    for i, part in enumerate(parts):
        temp_name = f"temp_part_{i}.mp3"
        communicate = edge_tts.Communicate(part, voice)
        await communicate.save(temp_name)
        final_audio += AudioSegment.from_file(temp_name)
        os.remove(temp_name)
    
    final_audio.export(output_file, format="mp3")

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.status("🤖 Processing long-format audio...", expanded=True) as status:
                # STEP 1: Audio Fragmenting (Fixes Broken Pipe)
                st.write("⏳ Fragmenting audio for stability...")
                with open("input.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("input.mp3")
                chunk_ms = 30000 
                chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]
                
                # STEP 2: Transcription
                r = sr.Recognizer()
                full_text = ""
                for i, c in enumerate(chunks):
                    st.write(f"🎙️ Transcribing segment {i+1}/{len(chunks)}...")
                    c.export("c.wav", format="wav")
                    with sr.AudioFile("c.wav") as src:
                        try:
                            full_text += r.recognize_google(r.record(src), language="es-ES") + " "
                        except: continue

                # STEP 3: Translation
                st.write("🌍 Translating content...")
                codes = {"English": "en", "Spanish": "es", "French": "fr"}
                translated_text = GoogleTranslator(source='auto', target=codes[target_lang]).translate(full_text)

                # STEP 4: Voice Generation with Chunking (Fixes 5000 chars error)
                st.write("🔊 Generating professional AI voice...")
                voice_map = {"English": "en-US-EmmaMultilingualNeural", "Spanish": "es-ES-ElviraNeural", "French": "fr-FR-DeniseNeural"}
                
                asyncio.run(safe_voice_generation(translated_text, voice_map[target_lang], "final_dub.mp3"))
                status.update(label="Dubbing Complete!", state="complete")
            
            st.balloons()
            with open("final_dub.mp3", "rb") as f:
                st.download_button("📥 Download Final Podcast", f, "didapod_pro_result.mp3")
        except Exception as e:
            st.error(f"Technical error: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US | AI Enterprise Solutions</small></center>", unsafe_allow_html=True)


