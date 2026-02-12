import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import os
import base64
import requests
import io
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

# --- ESTILO DIDACTAI ---
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
    border: 1px solid white !important;
}
h1, h2, h3, label, p, span { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 1. CARGA SEGURA DE LLAVES ---
# Usamos .get() para que la app no explote si no encuentra la llave
AZURE_KEY = st.secrets.get("AZURE_SPEECH_KEY")
AZURE_REGION = st.secrets.get("AZURE_SPEECH_REGION")

if not AZURE_KEY or not AZURE_REGION:
    st.error("⚠️ ERROR DE CONFIGURACIÓN: No encontré las llaves en Secrets.")
    st.info("Asegúrate de que en Streamlit > Settings > Secrets tengas:\nAZURE_SPEECH_KEY = 'tu_llave'\nAZURE_SPEECH_REGION = 'eastus'")
    st.stop()

# --- 2. HEADER ---
st.markdown("# 🎙️ DIDAPOD PRO")
st.markdown("<p style='color:#94a3b8;'>Azure Global Dubbing Engine</p>", unsafe_allow_html=True)
st.write("---")

# --- 3. INTERFAZ ---
col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Idioma Salida:", ["English", "Spanish", "French", "Portuguese"])
with col2:
    voice_gender = st.selectbox("Género Voz:", ["Female", "Male"])

up_file = st.file_uploader("Sube tu audio", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 INICIAR DOBLAJE"):
        try:
            with st.spinner("🤖 Procesando con Azure AI..."):
                # Guardar temporalmente el audio
                with open("temp.wav", "wb") as f:
                    f.write(up_file.getbuffer())

                # CONFIGURACIÓN DE TRADUCCIÓN (Protegida)
                # Limpiamos espacios en blanco por si acaso
                trans_config = speechsdk.translation.SpeechTranslationConfig(
                    subscription=AZURE_KEY.strip(), 
                    region=AZURE_REGION.strip()
                )
                
                lang_codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt"}
                target_code = lang_codes[target_lang]
                trans_config.add_target_language(target_code)
                
                # Azure detecta el idioma automáticamente si no se especifica
                audio_config = speechsdk.audio.AudioConfig(filename="temp.wav")
                translator = speechsdk.translation.TranslationRecognizer(
                    translation_config=trans_config, 
                    audio_config=audio_config
                )

                result = translator.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.TranslatedSpeech:
                    texto = result.translations[target_code]
                    
                    # SÍNTESIS DE VOZ
                    speech_config = speechsdk.SpeechConfig(
                        subscription=AZURE_KEY.strip(), 
                        region=AZURE_REGION.strip()
                    )
                    
                    voices = {
                        "English": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
                        "Spanish": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
                        "French": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
                        "Portuguese": {"Female": "pt-BR-FranciscaNeural", "Male": "pt-BR-AntonioNeural"}
                    }
                    speech_config.speech_synthesis_voice_name = voices[target_lang][voice_gender]
                    
                    out_file = "dubbed_audio.mp3"
                    audio_out = speechsdk.audio.AudioOutputConfig(filename=out_file)
                    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out)
                    synthesizer.speak_text_async(texto).get()

                    st.balloons()
                    st.audio(out_file)
                    with open(out_file, "rb") as f:
                        st.download_button("📥 DESCARGAR DOBLAJE", f, "didapod_azure.mp3")
                else:
                    st.warning("Azure no pudo procesar el audio. Verifica que se escuche una voz clara.")

        except Exception as e:
            st.error(f"Fallo de conexión con Azure: {str(e)}")
            st.info("Consejo: Revisa que la Clave 1 en Secrets sea idéntica a la del portal de Azure.")

st.markdown("<br><hr><center><small style='color:#94a3b8;'>© 2026 DidactAI-US</small></center>", unsafe_allow_html=True)

