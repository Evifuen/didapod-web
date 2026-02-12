import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, requests
from datetime import datetime

# --- 1. CONFIGURACIÓN Y LINKS (GOOGLE SHEETS) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLceo0Pah9sBwimtjic9yURqKQ6_x7ms60Yigil8EboGoxVl7xCBtXJNeWR9ulbcFjXuUkgJ5g56tS/pub?output=csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"

st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

# --- 2. ESTILO PROFESIONAL ---
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
}
h1, h2, h3, label, p, span { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. MOTOR DE LIMPIEZA DE LLAVES ---
def get_clean_secret(name):
    val = st.secrets.get(name, "")
    # Esto une la llave si se partió en los Secrets y quita basura
    return "".join(str(val).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_SPEECH_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION")

# --- 4. LOGIN Y REGISTRO ---
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
                    requests.post(APPS_SCRIPT_URL, json={
                        "email": user_email, 
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                except: pass
                st.session_state["auth"] = True
                st.session_state["user_email"] = user_email
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🎙️ DIDAPOD PRO")
st.write(f"Logged as: **{st.session_state['user_email']}**")

col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with col2:
    voice_gender = st.selectbox("Voice Gender:", ["Female", "Male"])

uploaded_file = st.file_uploader("Upload Audio File", type=["mp3", "wav"])

if uploaded_file and AZ_KEY:
    st.audio(uploaded_file)
    
    if st.button("🚀 START AI DUBBING PROCESS"):
        try:
            with st.spinner("🤖 Processing with Azure AI..."):
                with open("temp.wav", "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # CONFIGURACIÓN DE TRADUCCIÓN
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                
                # PARCHE DE SEGURIDAD: Esto soluciona el error que viste en la terminal
                t_cfg.set_property(speechsdk.PropertyId.Speech_LogFilename, "log.txt")
                
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[target_lang])
                
                audio_config = speechsdk.audio.AudioConfig(filename="temp.wav")
                recognizer = speechsdk.translation.TranslationRecognizer(t_cfg, audio_config)
                
                result = recognizer.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    # SÍNTESIS DE VOZ
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    audio_out = speechsdk.audio.AudioOutputConfig(filename="out.mp3")
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    syn.speak_text_async(result.translations[l_map[target_lang]]).get()

                    st.balloons()
                    st.success("Success!")
                    st.audio("out.mp3")
                    with open("out.mp3", "rb") as f:
                        st.download_button("📥 DOWNLOAD", f, "dubbed.mp3")
                else:
                    st.error(f"Azure Connection Failed: {result.reason}")
        except Exception as e:
            st.error(f"System Error: {e}")

st.markdown("<br><hr><center><small>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)
