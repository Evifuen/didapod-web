import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os, sys

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

# --- 2. LIMPIADOR DE LLAVES (ELIMINA EL ERROR 5) ---
def get_clean_secret(name, default=""):
    raw = st.secrets.get(name, default)
    # Eliminamos espacios, saltos de línea, comillas y caracteres invisibles
    return "".join(str(raw).split()).replace('"', '').replace("'", "").strip()

AZ_KEY = get_clean_secret("AZURE_KEY")
AZ_REG = get_clean_secret("AZURE_SPEECH_REGION", "eastus")

# --- 3. LOGIN ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 DIDAPOD ACCESS")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="didactai2026")
        if st.form_submit_button("LOGIN"):
            if u == "admin" and p == "didactai2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- 4. INTERFAZ ---
st.title("🎙️ DIDAPOD PRO")

c1, c2 = st.columns(2)
with c1: lang = st.selectbox("Target Language:", ["English", "Spanish", "French", "Portuguese"])
with c2: gen = st.selectbox("Voice Gender:", ["Female", "Male"])

up = st.file_uploader("Upload Audio", type=["mp3", "wav"])

if up and AZ_KEY:
    st.audio(up)
    if st.button("🚀 START AI DUBBING PROCESS"):
        try:
            with st.spinner("🤖 Connecting to Azure..."):
                with open("temp.wav", "wb") as f: f.write(up.getbuffer())

                # CONFIGURACIÓN DE TRADUCCIÓN
                t_cfg = speechsdk.translation.SpeechTranslationConfig(subscription=AZ_KEY, region=AZ_REG)
                
                # ESTA LÍNEA ES NUEVA: Ayuda con los errores de red/certificados
                t_cfg.set_property(speechsdk.PropertyId.Speech_LogFilename, "log.txt")
                
                l_map = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                t_cfg.add_target_language(l_map[lang])
                
                audio_cfg = speechsdk.audio.AudioConfig(filename="temp.wav")
                reco = speechsdk.translation.TranslationRecognizer(t_cfg, audio_cfg)
                
                # Ejecutar reconocimiento
                res = reco.recognize_once_async().get()

                if res.reason == speechsdk.ResultReason.TranslatedSpeech:
                    # SÍNTESIS
                    s_cfg = speechsdk.SpeechConfig(subscription=AZ_KEY, region=AZ_REG)
                    v_db = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    s_cfg.speech_synthesis_voice_name = v_db[lang][gen]
                    
                    audio_out = speechsdk.audio.AudioOutputConfig(filename="out.mp3")
                    syn = speechsdk.SpeechSynthesizer(s_cfg, audio_out)
                    syn.speak_text_async(res.translations[l_map[lang]]).get()

                    st.balloons()
                    st.success("Success!")
                    st.audio("out.mp3")
                    with open("out.mp3", "rb") as f:
                        st.download_button("📥 DOWNLOAD", f, "dubbed.mp3")
                else:
                    # Mensaje detallado si falla
                    st.error(f"Azure Connection Failed: {res.reason}")
                    if "AuthenticationFailure" in str(res.reason):
                        st.info("Check your AZURE_KEY in Secrets. It seems incorrect.")
        except Exception as e:
            st.error(f"System Error: {e}")
