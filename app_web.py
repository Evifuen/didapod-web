import streamlit as st
import edge_tts
import asyncio
import os
import base64
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment
from datetime import datetime
import pandas as pd  # Para leer la nube
import requests      # Para escribir en la nube

# --- CONFIGURACIÓN DE NUBE (RELLENA ESTO) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/19H6aHpni_PnqwZhIKg9MP1CvUmvb7HeX0T8OTSpV29o/export?format=csv&id=19H6aHpni_PnqwZhIKg9MP1CvUmvb7HeX0T8OTSpV29o&gid=0"
FORM_URL = "https://docs.google.com/forms/d/e/TU_ID_FORM/formResponse"
FORM_ENTRY_ID = "entry.XXXXXXXXX"

# --- 1. CONFIGURATION & STYLE ---
# Cambio mínimo: Icono estándar para evitar el NameError que viste en la imagen
st.set_page_config(page_title="DIDAPOD - DidactAI", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    return None

logo_data = get_base64_logo("logo2.png")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    .stExpander { 
        background-color: #7c3aed !important; 
        border: 2px solid white !important; 
        border-radius: 12px !important;
    }
    .stExpander summary, .stExpander summary * { 
        color: #ffffff !important; 
        font-weight: 800 !important; 
        font-size: 19px !important;
        text-transform: uppercase !important;
    }
    .stButton>button, .stDownloadButton>button { 
        background-color: #7c3aed !important; 
        color: white !important; 
        border-radius: 12px !important; 
        padding: 18px !important; 
        font-weight: 800 !important; 
        width: 100% !important; 
        border: 1px solid white !important;
    }
    h1, h2, h3, label, p, span { color: white !important; }
    .stSpinner > div { border-top-color: #7c3aed !important; }
    .lang-tag {
        background-color: #1e293b;
        color: #7c3aed;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        border: 1px solid #7c3aed;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CAMBIO AQUÍ: VALIDACIÓN EN LA NUBE ---
def check_email_limit(email):
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        count = df.astype(str).apply(lambda x: x.str.contains(email, case=False)).any(axis=1).sum()
        return count
    except:
        return 0

def register_email_cloud(email):
    try:
        requests.post(FORM_URL, data={FORM_ENTRY_ID: email})
    except:
        pass

# --- 2. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 ACCESS PANEL")
        user_email = st.text_input("Email Address")
        u = st.text_input("User", value="admin")
        p = st.text_input("Pass", type="password", value="didactai2026")
        
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026":
                if user_email and "@" in user_email:
                    attempts = check_email_limit(user_email)
                    if attempts >= 2:
                        st.error(f"🚫 Access denied for {user_email}. Limit reached.")
                    else:
                        # Registro en la nube
                        register_email_cloud(user_email)
                        st.session_state["auth"] = True
                        st.rerun()
                else:
                    st.error("Please enter a valid email address.")
    st.stop()

# --- 3. HEADER (INTACTO) ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="110" style="border-radius:10px;">', unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='margin:0;'>🎙️</h1>", unsafe_allow_html=True)
with col_r:
    st.markdown("<h1 style='margin:0;'>DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>Enterprise Dubbing by DidactAI-US</p>", unsafe_allow_html=True)

st.write("---")

# --- 4. PROCESSING (INTACTO) ---
col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2:
    voice_gender = st.selectbox("Select Voice Gender:", ["Female", "Male"])

up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.spinner("🤖 Processing audio..."):
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
                chunks = [audio[i:i + 40000] for i in range(0, len(audio), 40000)]
                total_chunks = len(chunks)
                
                progress_bar = st.progress(0)
                info_col1, info_col2 = st.columns([1, 1])
                status_text = info_col1.empty()
                lang_label = info_col2.empty()
                
                final_audio = AudioSegment.empty()
                r = sr.Recognizer()
                
                codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                voices_db = {
                    "English": {"Female": "en-US-EmmaMultilingualNeural", "Male": "en-US-BrianNeural"},
                    "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                    "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                    "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                }
                
                selected_voice = voices_db[target_lang][voice_gender]

                for i, chunk in enumerate(chunks):
                    percent = (i + 1) / total_chunks
                    progress_bar.progress(percent)
                    status_text.text(f"Chunk {i+1} of {total_chunks}")

                    chunk_path = f"c_{i}.wav"
                    chunk.export(chunk_path, format="wav")
                    with sr.AudioFile(chunk_path) as src:
                        try:
                            audio_data = r.record(src)
                            raw_response = r.recognize_google(audio_data, show_all=True)
                            
                            if raw_response and 'alternative' in raw_response:
                                text = raw_response['alternative'][0]['transcript']
                                translator = GoogleTranslator(source='auto', target=codes[target_lang])
                                trans = translator.translate(text)
                                detected_lang = translator.source.upper()
                                
                                lang_label.markdown(f'<div style="text-align:right;"><span class="lang-tag">Detected: {detected_lang}</span></div>', unsafe_allow_html=True)

                                voice_path = f"v_{i}.mp3"
                                asyncio.run(edge_tts.Communicate(trans, selected_voice).save(voice_path))
                                final_audio += AudioSegment.from_file(voice_path)
                                os.remove(voice_path)
                            
                        except Exception:
                            continue
                        finally:
                            if os.path.exists(chunk_path): os.remove(chunk_path)
                
                final_audio.export("result.mp3", format="mp3")
                status_text.empty()
                lang_label.empty()
                progress_bar.empty()
            
            st.balloons()
            st.markdown("<div style='background: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border: 1px solid #7c3aed;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>✅ PODCAST READY</h3>", unsafe_allow_html=True)
            with st.expander("▶️ CLICK HERE TO LISTEN BEFORE DOWNLOADING"):
                st.audio("result.mp3")
            st.write("")
            with open("result.mp3", "rb") as f:
                st.download_button("📥 DOWNLOAD FINAL FILE", f, "didapod_result.mp3")
            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e: 
            st.error(f"General Error: {e}")

# --- 5. DATA LOG VIEW (DESDE LA NUBE) ---
st.write("---")
with st.expander("📊 View Registered Emails (Admin Only)"):
    try:
        df_cloud = pd.read_csv(SHEET_CSV_URL)
        st.dataframe(df_cloud)
    except:
        st.info("Cloud database is currently empty or unreachable.")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)


