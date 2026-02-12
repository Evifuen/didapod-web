import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import base64
import asyncio
from datetime import datetime
import pandas as pd
import requests
import io

# --- CONFIGURACIÓN DE NUBE (Google Sheets) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLceo0Pah9sBwimtjic9yURqKQ6_x7ms60Yigil8EboGoxVl7xCBtXJNeWR9ulbcFjXuUkgJ5g56tS/pub?output=csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"

# --- 1. CONFIGURATION & STYLE (LOOK ORIGINAL) ---
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

# --- 2. FUNCIONES DE VALIDACIÓN Y NUBE ---
def check_email_limit(email):
    try:
        url = SHEET_CSV_URL.replace("&amp;", "&")
        resp = requests.get(url, timeout=10)
        df = pd.read_csv(io.BytesIO(resp.content))
        count = df.astype(str).apply(lambda x: x.str.contains(email, case=False, na=False)).any(axis=1).sum()
        return int(count)
    except: return 0

def register_email_cloud(email):
    try:
        payload = {"email": email, "fecha": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
        requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
    except: pass

# --- 3. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 ACCESS PANEL")
        user_email = st.text_input("Email Address")
        u = st.text_input("User", value="admin")
        p = st.text_input("Pass", type="password", value="didactai2026")
        if st.form_submit_button("Login"):
            if u == "admin" and p == "didactai2026" and "@" in user_email:
                if check_email_limit(user_email) >= 2:
                    st.error("🚫 Access denied. Limit reached.")
                else:
                    register_email_cloud(user_email)
                    st.session_state["auth"] = True
                    st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

# --- 4. HEADER ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="110" style="border-radius:10px;">', unsafe_allow_html=True)
    else: st.markdown("<h1>🎙️</h1>", unsafe_allow_html=True)
with col_r:
    st.markdown("<h1 style='margin:0;'>DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8 !important; margin:0;'>Enterprise Dubbing by Azure & DidactAI</p>", unsafe_allow_html=True)

st.write("---")

# --- 5. PROCESSING (MOTOR AZURE) ---
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_SPEECH_REGION"]

col1, col2 = st.columns(2)
with col1:
    target_lang_name = st.selectbox("Select Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2:
    voice_gender = st.selectbox("Select Voice Gender:", ["Female", "Male"])

up_file = st.file_uploader("Upload podcast", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 START AI DUBBING"):
        try:
            with st.spinner("🤖 Processing with Azure AI..."):
                input_path = "temp_audio.wav"
                with open(input_path, "wb") as f:
                    f.write(up_file.getbuffer())

                # Configuración de Traducción con Azure
                translation_config = speechsdk.translation.SpeechTranslationConfig(
                    subscription=AZURE_KEY, region=AZURE_REGION
                )
                
                lang_codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                target_code = lang_codes[target_lang_name]
                translation_config.add_target_language(target_code)
                
                # Auto-detección: Por defecto es-ES pero Azure buscará el idioma real
                audio_config = speechsdk.audio.AudioConfig(filename=input_path)
                translator = speechsdk.translation.TranslationRecognizer(
                    translation_config=translation_config, audio_config=audio_config
                )

                result = translator.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    texto_traducido = result.translations[target_code]
                    detected_src = result.language
                    
                    st.markdown(f'<div style="text-align:right;"><span class="lang-tag">Detected: {detected_src.upper()}</span></div>', unsafe_allow_html=True)

                    # Síntesis de Voz Profesional
                    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    speech_config.speech_synthesis_voice_name = voices[target_lang_name][voice_gender]
                    
                    output_path = "result.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=output_path)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out)
                    synthesizer.speak_text_async(texto_traducido).get()

                    st.balloons()
                    st.markdown("<div style='background: rgba(255,255,255,0.05); padding: 25px; border-radius: 20px; border: 1px solid #7c3aed;'>", unsafe_allow_html=True)
                    st.markdown("<h3 style='text-align:center;'>✅ PODCAST READY</h3>", unsafe_allow_html=True)
                    st.audio(output_path)
                    with open(output_path, "rb") as f:
                        st.download_button("📥 DOWNLOAD FINAL FILE", f, "didapod_result.mp3")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error("No speech detected. Check audio quality.")

        except Exception as e:
            st.error(f"Error: {e}")

# --- 6. DATA LOG VIEW ---
st.write("---")
with st.expander("📊 View Registered Emails (Admin Only)"):
    try:
        url = SHEET_CSV_URL.replace("&amp;", "&")
        resp = requests.get(url, timeout=10)
        df_cloud = pd.read_csv(io.BytesIO(resp.content))
        if 'Marca temporal' in df_cloud.columns:
            df_cloud = df_cloud.rename(columns={'Marca temporal': 'fecha'})
        df_cloud = df_cloud.loc[:, ~df_cloud.columns.duplicated(keep='first')]
        st.dataframe(df_cloud)
    except: st.info("Cloud database unreachable.")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
