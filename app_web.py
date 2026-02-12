import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import base64
import requests
import io
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE NUBE (Google Sheets) ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLceo0Pah9sBwimtjic9yURqKQ6_x7ms60Yigil8EboGoxVl7xCBtXJNeWR9ulbcFjXuUkgJ5g56tS/pub?output=csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLIO5CsYs-7Z2xt335yT2ZQx9Hp3sxfVY7Bzvpdmu3LsD6uHTxvpukLHb2AAjMvDk2qA/exec"

# --- 1. CONFIGURATION & STYLE (EL LOOK ORIGINAL) ---
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
.stButton>button, .stDownloadButton>button {
    background-color: #7c3aed !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 18px !important;
    font-weight: 800 !important;
    width: 100% !important;
    border: 1px solid white !important;
}
.stExpander {
    background-color: #1e293b !important;
    border: 1px solid #7c3aed !important;
    border-radius: 10px !important;
}
h1, h2, h3, label, p, span { color: white !important; }
.lang-tag {
    background-color: #7c3aed;
    color: white;
    padding: 4px 10px;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE BASE DE DATOS ---
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

# --- 3. SISTEMA DE LOGIN (TUS CREDENCIALES) ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.container():
        st.markdown("<h2 style='text-align:center;'>🔐 ACCESO DIDAPOD</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_email = st.text_input("Introduce tu Email corporativo")
            u = st.text_input("Usuario", value="admin")
            p = st.text_input("Contraseña", type="password", value="didactai2026")
            
            if st.form_submit_button("INGRESAR A LA PLATAFORMA"):
                if u == "admin" and p == "didactai2026" and "@" in user_email:
                    if check_email_limit(user_email) >= 2:
                        st.error("🚫 Límite de uso alcanzado para este email.")
                    else:
                        register_email_cloud(user_email)
                        st.session_state["auth"] = True
                        st.rerun()
                else:
                    st.error("Credenciales incorrectas o email no válido.")
    st.stop()

# --- 4. HEADER Y CARGA DE AZURE SECRETS ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if logo_data:
        st.markdown(f'<img src="data:image/png;base64,{logo_data}" width="100">', unsafe_allow_html=True)
    else: st.title("🎙️")
with col_r:
    st.markdown("<h1 style='margin:0;'>DIDAPOD PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Doblaje con Inteligencia Artificial - Azure Engine</p>", unsafe_allow_html=True)

# Recuperamos las llaves de la "caja fuerte" de Streamlit
AZ_KEY = st.secrets.get("AZURE_SPEECH_KEY")
AZ_REG = st.secrets.get("AZURE_SPEECH_REGION")

if not AZ_KEY or not AZ_REG:
    st.warning("⚠️ Error en la configuración de Azure (Secrets).")
    st.stop()

# --- 5. INTERFAZ DE TRABAJO ---
st.write("---")
c1, c2 = st.columns(2)
with c1:
    target_lang = st.selectbox("Idioma de Destino:", ["English", "Spanish", "French", "Portuguese"])
with c2:
    voice_gender = st.selectbox("Tipo de Voz:", ["Female", "Male"])

up_file = st.file_uploader("Sube el audio a traducir", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 INICIAR PROCESO DE DOBLAJE"):
        try:
            with st.spinner("🤖 Detectando idioma y traduciendo..."):
                # Guardar audio temporal
                with open("temp_input.wav", "wb") as f:
                    f.write(up_file.getbuffer())

                # Configuración Azure (Limpiando espacios accidentales)
                trans_config = speechsdk.translation.SpeechTranslationConfig(
                    subscription=AZ_KEY.strip(), region=AZ_REG.strip()
                )
                
                lang_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                target_code = lang_map[target_lang]
                trans_config.add_target_language(target_code)
                
                audio_config = speechsdk.audio.AudioConfig(filename="temp_input.wav")
                recognizer = speechsdk.translation.TranslationRecognizer(
                    translation_config=trans_config, audio_config=audio_config
                )

                result = recognizer.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    texto_out = result.translations[target_code]
                    st.markdown(f"**Idioma detectado:** <span class='lang-tag'>{result.language.upper()}</span>", unsafe_allow_html=True)

                    # Síntesis de Voz Profesional
                    speech_config = speechsdk.SpeechConfig(subscription=AZ_KEY.strip(), region=AZ_REG.strip())
                    
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    speech_config.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    output_name = "final_dubbing.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=output_name)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out)
                    synthesizer.speak_text_async(texto_out).get()

                    st.balloons()
                    st.success("¡Doblaje completado!")
                    st.audio(output_name)
                    with open(output_name, "rb") as f:
                        st.download_button("📥 DESCARGAR AUDIO FINAL", f, "didapod_pro.mp3")
                else:
                    st.error("No se pudo extraer voz del audio.")

        except Exception as e:
            st.error(f"Fallo de conexión con Azure. Revisa la Clave 1 en tus Secrets.")

# --- 6. LOG DE REGISTRO ---
st.write("---")
with st.expander("📊 Log de Accesos (Administrador)"):
    try:
        resp = requests.get(SHEET_CSV_URL.replace("&amp;", "&"), timeout=10)
        df = pd.read_csv(io.BytesIO(resp.content))
        st.dataframe(df)
    except: st.info("Base de datos no disponible.")

st.markdown("<br><center><small style='color:#94a3b8;'>© 2026 DidactAI-US | Soluciones Pro</small></center>", unsafe_allow_html=True)




