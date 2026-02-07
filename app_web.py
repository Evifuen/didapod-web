import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import os
import base64

# --- 1. CONFIGURACIÓN DE AZURE (Cámbialo por tus Secrets) ---
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_REGION"]

# --- 2. CONFIGURACIÓN DE PÁGINA Y DISEÑO ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo.png")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    button[kind="primaryFormSubmit"], .stButton>button {{
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 2px solid #ffffff !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        width: 100% !important;
        height: 50px !important;
    }}
    h1, h2, h3, label, p, span {{ color: white !important; }}
    .logo-container {{ text-align: center; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

if logo_data:
    st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_data}" width="200"></div>', unsafe_allow_html=True)

# --- 3. LOGIN & GOOGLE SHEETS ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 📝 DIDAPOD PRO ACCESS")
        email = st.text_input("📧 Your Email")
        if st.form_submit_button("ENTER DIDAPOD"):
            if email:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df = conn.read()
                    nuevo = pd.DataFrame([{"Email": email, "Date": str(pd.Timestamp.now())}])
                    conn.update(data=pd.concat([df, nuevo], ignore_index=True))
                    st.session_state["auth"] = True
                    st.rerun()
                except:
                    st.session_state["auth"] = True
                    st.rerun()
    st.stop()

# --- 4. INTERFAZ ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO (AZURE)</h1>", unsafe_allow_html=True)
st.write("<p style='text-align:center;'>Detección automática de idioma activada.</p>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    target_lang = st.selectbox("Traducir a:", ["English", "Spanish", "French", "Portuguese", "German"])
with c2:
    gender = st.selectbox("Voz de salida:", ["Male", "Female"])

up_file = st.file_uploader("Sube tu podcast (Cualquier idioma)", type=["mp3", "wav"])

if up_file:
    st.audio(up_file)
    if st.button("🚀 INICIAR TRADUCCIÓN PRO"):
        try:
            with st.spinner("🤖 Azure detectando idioma y traduciendo..."):
                # Guardar archivo temporal
                with open("temp.mp3", "wb") as f: f.write(up_file.getbuffer())
                audio = AudioSegment.from_file("temp.mp3")
                chunks = [audio[i:i + 40000] for i in range(0, len(audio), 40000)]
                final_audio = AudioSegment.empty()

                # CONFIGURACIÓN DE AZURE
                speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                
                # Mapeo de idiomas y voces
                codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt", "German": "de"}
                voices = {
                    "English": "en-US-AndrewNeural" if gender == "Male" else "en-US-AvaNeural",
                    "Spanish": "es-ES-AlvaroNeural" if gender == "Male" else "es-ES-ElviraNeural",
                    "French": "fr-FR-RemyNeural" if gender == "Male" else "fr-FR-DeniseNeural",
                    "Portuguese": "pt-BR-AntonioNeural" if gender == "Male" else "pt-BR-FranciscaNeural",
                    "German": "de-DE-ConradNeural" if gender == "Male" else "de-DE-KatjaNeural"
                }

                # CONFIGURACIÓN DE DETECCIÓN AUTOMÁTICA
                # Le decimos a Azure qué idiomas debe intentar identificar
                auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                    languages=["es-ES", "en-US", "fr-FR", "pt-BR", "de-DE"]
                )

                for i, chunk in enumerate(chunks):
                    chunk.export("c.wav", format="wav")
                    audio_config = speechsdk.audio.AudioConfig(filename="c.wav")
                    
                    # Reconocedor con auto-detección
                    recognizer = speechsdk.SpeechRecognizer(
                        speech_config=speech_config, 
                        auto_detect_source_language_config=auto_detect_config, 
                        audio_config=audio_config
                    )
                    
                    result = recognizer.recognize_once()

                    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        # Azure nos dice qué detectó
                        detected_lang = result.properties[speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult]
                        text = result.text
                        
                        # Traducir texto
                        trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                        
                        # Generar nueva voz (TTS)
                        speech_config.speech_synthesis_voice_name = voices[target_lang]
                        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
                        res_voice = synthesizer.speak_text_async(trans).get()
                        
                        with open(f"v{i}.wav", "wb") as f: f.write(res_voice.audio_data)
                        final_audio += AudioSegment.from_file(f"v{i}.wav")
                        os.remove(f"v{i}.wav")

                final_audio.export("result_pro.mp3", format="mp3")
                st.balloons()
                st.audio("result_pro.mp3")
                with open("result_pro.mp3", "rb") as f:
                    st.download_button("📥 DESCARGAR PODCAST", f, "didapod_pro.mp3")

        except Exception as e: st.error(f"Error: {e}")



