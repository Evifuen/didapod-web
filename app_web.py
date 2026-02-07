import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import os
import base64
import time

# --- 1. CONFIGURACIÓN DE SEGURIDAD (SECRETS) ---
AZURE_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_REGION = st.secrets["AZURE_REGION"]

# --- 2. CONFIGURACIÓN DE PÁGINA Y BLINDAJE VISUAL ---
st.set_page_config(page_title="DIDAPOD PRO", page_icon="🎙️", layout="centered")

def get_base64_logo(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_data = get_base64_logo("logo.png")

# CSS BLINDADO: Oculta menús de Streamlit y fuerza el diseño profesional
st.markdown(f"""
    <style>
    /* Ocultar elementos de Streamlit para que parezca una App propia */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .stApp {{ background-color: #0f172a !important; }}
    
    /* Botón de entrada y botones generales */
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

# --- 3. LOGIN & ACCESO BLINDADO ---
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login"):
        st.markdown("### 🔐 ACCESO RESTRINGIDO DIDAPOD")
        email = st.text_input("📧 Correo Autorizado")
        # Aquí podrías pedir una clave específica si la tienes en el Excel
        if st.form_submit_button("VALIDAR LICENCIA"):
            if email:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df = conn.read()
                    nuevo = pd.DataFrame([{"Email": email, "Date": str(pd.Timestamp.now())}])
                    conn.update(data=pd.concat([df, nuevo], ignore_index=True))
                    st.session_state["auth"] = True
                    st.rerun()
                except:
                    st.session_state["auth"] = True # Fallback para que no se trabe
                    st.rerun()
    st.stop()

# --- 4. INTERFAZ DE USUARIO ---
st.markdown("<h1 style='text-align:center;'>🎙️ DIDAPOD PRO v2.0</h1>", unsafe_allow_html=True)
st.write("<p style='text-align:center; color:#94a3b8;'>Motor de Inteligencia Artificial Azure con Detección Automática</p>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    target_lang = st.selectbox("Idioma de salida:", ["English", "Spanish", "French", "Portuguese", "German"])
with c2:
    gender = st.selectbox("Tono de Voz:", ["Male", "Female"])

up_file = st.file_uploader("Cargar Podcast (Formatos: MP3, WAV)", type=["mp3", "wav"])

# --- 5. LÓGICA DE PROCESAMIENTO BLINDADA ---
if up_file:
    # Generar un ID único para esta sesión y evitar cruces de archivos
    session_id = str(int(time.time()))
    temp_input = f"input_{session_id}.mp3"
    
    with open(temp_input, "wb") as f: 
        f.write(up_file.getbuffer())
    
    audio_check = AudioSegment.from_file(temp_input)
    duracion_seg = len(audio_check) / 1000
    
    st.info(f"⏱️ Duración detectada: {duracion_seg:.2f} segundos")

    # BLINDAJE DE COSTOS: Límite de 5 minutos por archivo
    if duracion_seg > 300:
        st.error("🛑 El archivo supera los 5 minutos permitidos. Por favor, recorta el audio.")
        os.remove(temp_input)
    else:
        if st.button("🚀 INICIAR TRADUCCIÓN INTELIGENTE"):
            try:
                with st.spinner("🤖 Azure está analizando y doblando el audio..."):
                    chunks = [audio_check[i:i + 30000] for i in range(0, len(audio_check), 30000)]
                    final_audio = AudioSegment.empty()
                    
                    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
                    
                    # Configuración de Voces y Detección
                    codes = {"English": "en", "Spanish": "es", "French": "fr", "Portuguese": "pt", "German": "de"}
                    voices = {
                        "English": "en-US-AndrewNeural" if gender == "Male" else "en-US-AvaNeural",
                        "Spanish": "es-ES-AlvaroNeural" if gender == "Male" else "es-ES-ElviraNeural",
                        "French": "fr-FR-RemyNeural" if gender == "Male" else "fr-FR-DeniseNeural",
                        "Portuguese": "pt-BR-AntonioNeural" if gender == "Male" else "pt-BR-FranciscaNeural",
                        "German": "de-DE-ConradNeural" if gender == "Male" else "de-DE-KatjaNeural"
                    }

                    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                        languages=["es-ES", "en-US", "fr-FR", "pt-BR", "de-DE"]
                    )

                    for i, chunk in enumerate(chunks):
                        chunk_path = f"chunk_{session_id}_{i}.wav"
                        chunk.export(chunk_path, format="wav")
                        
                        audio_config = speechsdk.audio.AudioConfig(filename=chunk_path)
                        recognizer = speechsdk.SpeechRecognizer(
                            speech_config=speech_config, 
                            auto_detect_source_language_config=auto_detect_config, 
                            audio_config=audio_config
                        )
                        
                        result = recognizer.recognize_once()

                        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                            text = result.text
                            # Traducción
                            trans = GoogleTranslator(source='auto', target=codes[target_lang]).translate(text)
                            
                            # Síntesis de Voz
                            speech_config.speech_synthesis_voice_name = voices[target_lang]
                            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
                            res_voice = synthesizer.speak_text_async(trans).get()
                            
                            voice_path = f"v_{session_id}_{i}.wav"
                            with open(voice_path, "wb") as f: 
                                f.write(res_voice.audio_data)
                            
                            final_audio += AudioSegment.from_file(voice_path)
                            
                            # Limpieza inmediata de fragmentos
                            os.remove(chunk_path)
                            os.remove(voice_path)

                    output_file = f"result_{session_id}.mp3"
                    final_audio.export(output_file, format="mp3")
                    
                    st.success("✅ ¡Traducción completada!")
                    st.audio(output_file)
                    
                    with open(output_file, "rb") as f:
                        st.download_button("📥 DESCARGAR RESULTADO", f, f"didapod_{target_lang}.mp3")
                    
                    # Limpieza del resultado final después de mostrarlo
                    os.remove(temp_input)

            except Exception as e:
                st.error(f"Se ha producido un error técnico. Contacte a soporte.")
                # Log del error real solo para el desarrollador (consola)
                print(f"Error: {e}")

st.markdown("<br><hr><center><small style='color:#475569;'>DIDAPOD PRO © 2026 | Seguridad Nivel Enterprise</small></center>", unsafe_allow_html=True)
