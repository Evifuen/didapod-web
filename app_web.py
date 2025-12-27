import streamlit as st
import os
import asyncio
import edge_tts
from pydub import AudioSegment
import speech_recognition as sr
from deep_translator import GoogleTranslator
import time
from PIL import Image

# 1. CONFIGURACIÓN DE MARCA
st.set_page_config(page_title="DidactAI - DIDAPOD", page_icon="🎙️", layout="centered")

# 2. ESTILO CSS PARA COLORES DIDACTAI
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .main-title { 
        font-size: 45px; font-weight: bold; 
        background: linear-gradient(90deg, #9333ea, #3b82f6); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0px; 
    }
    div.stButton > button {
        background: linear-gradient(135deg, #9333ea 0%, #3b82f6 100%);
        color: white; border: none; padding: 15px;
        border-radius: 12px; font-weight: bold;
    }
    div.stDownloadButton > button {
        background-color: transparent; color: #3b82f6;
        border: 2px solid #3b82f6; border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. ENCABEZADO CON LOGO
try:
    img = Image.open("logo.png")
    col_l, col_r = st.columns([1, 4])
    with col_l:
        st.image(img, width=120)
    with col_r:
        st.markdown('<p class="main-title">DIDAPOD</p>', unsafe_allow_html=True)
        st.write("<p style='color: #94a3b8;'>Powered by DidactAI</p>", unsafe_allow_html=True)
except:
    st.markdown('<p class="main-title">DIDAPOD by DidactAI</p>', unsafe_allow_html=True)

st.write("---")

# 4. LÓGICA DE TRADUCCIÓN (Soporta +13k caracteres)
def traducir_largo(texto):
    traductor = GoogleTranslator(source='es', target='en')
    paso = 4000
    resultado = []
    for i in range(0, len(texto), paso):
        chunk = texto[i:i+paso]
        resultado.append(traductor.translate(chunk))
    return " ".join(resultado)

# 5. INTERFAZ DE USUARIO
archivo = st.file_uploader("Sube tu podcast para doblaje (MP3)", type=["mp3"])

if archivo:
    if st.button("🚀 INICIAR DOBLAJE IA"):
        progreso = st.progress(0)
        status = st.empty()
        
        try:
            with open("temp_web.mp3", "wb") as f:
                f.write(archivo.getbuffer())
            
            # Transcripción (v1.3 estable)
            status.info("🎙️ Transcribiendo podcast...")
            audio = AudioSegment.from_mp3("temp_web.mp3").set_channels(1).set_frame_rate(16000)
            r = sr.Recognizer()
            texto_es = ""
            for i in range(0, len(audio), 30000):
                chunk = audio[i:i+30000]
                chunk.export("chunk.wav", format="wav")
                with sr.AudioFile("chunk.wav") as source:
                    try: texto_es += r.recognize_google(r.record(source), language="es-ES") + ". "
                    except: continue
                progreso.progress(min(50, 10 + int((i/len(audio))*40)))
            
            # Traducción sin límites
            status.info(f"📝 Traduciendo {len(texto_es)} caracteres...")
            texto_en = traducir_largo(texto_es)
            progreso.progress(80)

            # Síntesis de voz final
            status.info("🔊 Generando voz final DIDAPOD...")
            salida = f"DIDAPOD_OUT_{int(time.time())}.mp3"
            asyncio.run(edge_tts.Communicate(texto_en, "en-US-EmmaNeural").save(salida))
            progreso.progress(100)
            
            status.success("✨ ¡Proceso completado con éxito!")
            with open(salida, "rb") as f:
                st.download_button("📥 DESCARGAR RESULTADO", f, file_name=f"Doblaje_{archivo.name}")

        except Exception as e:
            st.error(f"Fallo en el sistema: {str(e)}")