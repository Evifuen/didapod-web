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

# --- 2. LOGIN SYSTEM ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.markdown("<h2 style='color:white;'>🔐 Restricted Access</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026":
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- 3. BRANDING & HEADER ---
col1, col2 = st.columns([1, 4])
with col2:
    st.markdown('<p class="main-title">DIDAPOD</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Powered by DidactAI-US</p>', unsafe_allow_html=True)

st.markdown("---")
target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French"])
up_file = st.file_uploader("Upload podcast (MP3/WAV)", type=["mp3", "wav"])

async def generate_voice_segments(text, voice, output_filename):
    # Divide el texto en partes de 4000 caracteres para evitar el error de límite
    text_parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    combined_audio = AudioSegment.empty()
    
    for i, part in enumerate(text_parts):
        temp_part = f"part_{i}.mp3"
        communicate = edge_tts.Communicate(part, voice)
        await communicate.save(temp_part)
        part_audio = AudioSegment.from_file(temp_part)
        combined_audio += part_audio
        os.remove(temp_part)
        
    combined_audio.export(output_filename, format="mp3")

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.status("🤖 Processing heavy-duty dubbing...", expanded=True) as status:
                # STEP 1: Process Audio in Chunks
                st.write("⏳ Fragmenting audio for stability...")
                with open("t.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("t.mp3")
                chunk_ms = 30000 
                chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]
                
                # STEP 2: Transcription
                r = sr.Recognizer()
                full_t = ""
                for i, c in enumerate(chunks):
                    st.write(f"🎙️ Transcribing fragment {i+1}/{len(chunks)}...")
                    c.export("c.wav", format="wav")
                    with sr.AudioFile("c.wav") as src:
                        try:
                            full_t += r.recognize_google(r.record(src), language="es-ES") + " "
                        except: continue

                # STEP 3: Translation
                st.write("🌍 Translating content...")
                codes = {"English": "en", "Spanish": "es", "French": "fr"}
                final_t = GoogleTranslator(source='auto', target=codes[target_lang]).translate(full_t)

                # STEP 4: Voice Generation with Chunking (Fixes 5000 chars error)
                st.write("🔊 Generating professional AI voice...")
                voice_m = {"English": "en-US-EmmaMultilingualNeural", "Spanish": "es-ES-ElviraNeural", "French": "fr-FR-DeniseNeural"}
                
                asyncio.run(generate_voice_segments(final_t, voice_m[target_lang], "final_result.mp3"))
                status.update(label="Dubbing Complete!", state="complete")
            
            st.balloons()
            with open("final_result.mp3", "rb") as f:
                st.download_button("📥 Download Final Podcast", f, "didapod_pro_result.mp3")
        except Exception as e:
            st.error(f"Technical detail: {e}")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
